"""
Main routes for the Shreddit Meme Generator web application.
"""
import os
import uuid
import logging
import requests
import random
import json
from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request,
    url_for, current_app, send_from_directory, jsonify, session
)
from werkzeug.utils import secure_filename

from config_manager import ConfigManager
from reddit_api import RedditMemeAPI
from ai_meme_generator import AIMemeGenerator
from image_editor import MemeEditor
from imgflip_api import ImgFlipAPI
from imgflip_generator import ImgFlipGenerator

# Set up logging
logging.basicConfig(
    filename="flask_app.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("flask_app")

# Create blueprint
bp = Blueprint('main', __name__)

# Initialize components
config = ConfigManager()
config._load_config()

# Extract the Reddit API credentials from config
client_id = config.config.get('reddit', {}).get('client_id', '')
client_secret = config.config.get('reddit', {}).get('client_secret', '')
user_agent = config.config.get('reddit', {}).get('user_agent', 'MemeGenerator/1.0')

# Initialize components
reddit_api = RedditMemeAPI(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
ai_generator = AIMemeGenerator()
image_editor = MemeEditor()

# Initialize ImgFlip clients
imgflip_api = ImgFlipAPI(cache_dir="cache")
imgflip_generator = ImgFlipGenerator(cache_dir="cache")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

@bp.route('/guitar-band-memes')
def guitar_band_memes():
    """Render the guitar/band memes page."""
    return render_template('guitar_band_memes.html')

@bp.route('/search-band-images', methods=['POST'])
def search_band_images():
    """Search for band images."""
    if request.method == 'POST':
        band_name = request.form.get('band_name', '')
        if not band_name:
            flash('Please enter a band name')
            return redirect(url_for('main.guitar_band_memes'))
        
        try:
            # Search for band images - get 30 to have enough after filtering
            images = reddit_api.search_band_images(band_name, limit=30)
            if not images:
                # Fallback to guitar memes if no band images found
                flash(f'No images found for band: {band_name}. Showing guitar memes instead.')
                images = reddit_api.get_guitar_memes(limit=20)
            
            # Randomize the results to provide variety each time
            random.shuffle(images)
            
            # Limit to 20 images
            images = images[:20]
            
            # Store image URLs in session
            image_list = [{'url': img[1], 'title': img[0]} for img in images]
            
            logger.info(f"Found {len(image_list)} images for band '{band_name}'")
            return render_template('band_image_results.html', images=image_list, band_name=band_name)
        
        except Exception as e:
            logger.error(f"Error searching for band images: {e}", exc_info=True)
            flash(f'Error searching for images: {str(e)}')
            return redirect(url_for('main.guitar_band_memes'))

@bp.route('/generate-band-meme', methods=['POST'])
def generate_band_meme():
    """Generate a band-themed meme."""
    if request.method == 'POST':
        image_url = request.form.get('image_url', '')
        band_name = request.form.get('band_name', '')
        
        if not image_url or not band_name:
            flash('Missing required information')
            return redirect(url_for('main.guitar_band_memes'))
        
        try:
            # Generate a unique ID for this meme
            unique_id = str(uuid.uuid4())
            temp_dir = current_app.config['UPLOAD_FOLDER']
            image_path = os.path.join(temp_dir, f"{unique_id}.jpg")
            
            # Handle different image sources (URL vs local upload)
            if image_url.startswith('http'):
                # It's a real URL - download it
                reddit_api.download_image(image_url, image_path)
            elif image_url.startswith('/upload/'):
                # It's a local upload - copy the file
                upload_filename = os.path.basename(image_url)
                source_path = os.path.join(current_app.config['UPLOAD_FOLDER'], upload_filename)
                
                # Check if the file exists
                if not os.path.exists(source_path):
                    logger.error(f"Uploaded file not found: {source_path}")
                    flash('Uploaded image not found')
                    return redirect(url_for('main.guitar_band_memes'))
                
                # Copy the file instead of downloading
                import shutil
                shutil.copy2(source_path, image_path)
                logger.info(f"Copied uploaded file from {source_path} to {image_path}")
            else:
                # Invalid URL format
                logger.error(f"Invalid image URL format: {image_url}")
                flash('Invalid image source')
                return redirect(url_for('main.guitar_band_memes'))
            
            # Generate meme text - pass the image path to analyze the content
            top_text, bottom_text = ai_generator.generate_band_meme_text(band_name=band_name, image_path=image_path)
            
            # Create the meme
            output_path = os.path.join(current_app.config['GENERATED_FOLDER'], f"{unique_id}_meme.jpg")
            image_editor.generate_meme(
                image_path=image_path,
                top_text=top_text,
                bottom_text=bottom_text,
                output_filename=output_path,
                use_local_image=True
            )
            
            # Return the meme page
            return render_template('meme_result.html', 
                                  meme_path=f"/meme/{unique_id}_meme.jpg",
                                  top_text=top_text,
                                  bottom_text=bottom_text,
                                  source_type="band",
                                  source_name=band_name)
            
        except Exception as e:
            logger.error(f"Error generating band meme: {e}", exc_info=True)
            flash(f'Error generating meme: {str(e)}')
            return redirect(url_for('main.guitar_band_memes'))

@bp.route('/genre-memes')
def genre_memes():
    """Render the genre memes page."""
    # Music genres without "Music" suffix but still specific to music
    music_genres = [
        "Rock", "Heavy Metal", "Pop", "Hip Hop", "Jazz", 
        "Blues", "Country", "Electronic", "Classical", 
        "Reggae", "Punk Rock", "R&B", "Soul", "Folk", 
        "Indie Rock", "Techno", "Disco", "Alternative Rock", 
        "Funk", "Grunge"
    ]
    return render_template('genre_memes.html', genres=music_genres)

@bp.route('/search-genre-images', methods=['POST'])
def search_genre_images():
    """Search for genre images."""
    if request.method == 'POST':
        genre = request.form.get('genre', '')
        if not genre:
            flash('Please select a genre')
            return redirect(url_for('main.genre_memes'))
        
        try:
            # Internally add "music" context for search without changing display name
            search_genre = f"{genre} Music"
            
            # Search for genre images - get 30 to have enough after filtering
            images = reddit_api.search_genre_images(search_genre, limit=30)
            if not images or len(images) < 5:
                # Try a different search strategy if no results
                logger.info(f"First search returned insufficient results for '{search_genre}', trying secondary search")
                secondary_images = reddit_api.search_memes(f"{genre} band concert", limit=30)
                if secondary_images:
                    images.extend(secondary_images)
                
                # If still no results, fall back to generic music images
                if not images or len(images) < 5:
                    flash(f'Limited images found for genre: {genre}. Including some general music images.')
                    fallback_images = reddit_api.search_memes("music concert band", limit=20)
                    images.extend(fallback_images)
            
            # Randomize the results to provide variety each time
            random.shuffle(images)
            
            # Limit to 20 images
            images = images[:20]
            
            # Store image URLs in session
            image_list = [{'url': img[1], 'title': img[0]} for img in images]
            
            logger.info(f"Found {len(image_list)} images for genre '{genre}'")
            return render_template('genre_image_results.html', images=image_list, genre=genre)
        
        except Exception as e:
            logger.error(f"Error searching for genre images: {e}", exc_info=True)
            flash(f'Error searching for images: {str(e)}')
            return redirect(url_for('main.genre_memes'))

@bp.route('/generate-genre-meme', methods=['POST'])
def generate_genre_meme():
    """Generate a genre-themed meme."""
    if request.method == 'POST':
        image_url = request.form.get('image_url', '')
        genre = request.form.get('genre', '')
        
        if not image_url or not genre:
            flash('Missing required information')
            return redirect(url_for('main.genre_memes'))
        
        try:
            # Generate a unique ID for this meme
            unique_id = str(uuid.uuid4())
            temp_dir = current_app.config['UPLOAD_FOLDER']
            image_path = os.path.join(temp_dir, f"{unique_id}.jpg")
            
            # Handle different image sources (URL vs local upload)
            if image_url.startswith('http'):
                # It's a real URL - download it
                reddit_api.download_image(image_url, image_path)
            elif image_url.startswith('/upload/'):
                # It's a local upload - copy the file
                upload_filename = os.path.basename(image_url)
                source_path = os.path.join(current_app.config['UPLOAD_FOLDER'], upload_filename)
                
                # Check if the file exists
                if not os.path.exists(source_path):
                    logger.error(f"Uploaded file not found: {source_path}")
                    flash('Uploaded image not found')
                    return redirect(url_for('main.genre_memes'))
                
                # Copy the file instead of downloading
                import shutil
                shutil.copy2(source_path, image_path)
                logger.info(f"Copied uploaded file from {source_path} to {image_path}")
            else:
                # Invalid URL format
                logger.error(f"Invalid image URL format: {image_url}")
                flash('Invalid image source')
                return redirect(url_for('main.genre_memes'))
            
            # Generate meme text - pass the image path to analyze the content
            top_text, bottom_text = ai_generator.generate_genre_meme_text(genre=genre, image_path=image_path)
            
            # Create the meme
            output_path = os.path.join(current_app.config['GENERATED_FOLDER'], f"{unique_id}_meme.jpg")
            image_editor.generate_meme(
                image_path=image_path,
                top_text=top_text,
                bottom_text=bottom_text,
                output_filename=output_path,
                use_local_image=True
            )
            
            # Return the meme page
            return render_template('meme_result.html', 
                                  meme_path=f"/meme/{unique_id}_meme.jpg",
                                  top_text=top_text,
                                  bottom_text=bottom_text,
                                  source_type="genre",
                                  source_name=genre)
            
        except Exception as e:
            logger.error(f"Error generating genre meme: {e}", exc_info=True)
            flash(f'Error generating meme: {str(e)}')
            return redirect(url_for('main.genre_memes'))

@bp.route('/regenerate-meme', methods=['POST'])
def regenerate_meme():
    """Regenerate meme text for an existing meme."""
    if request.method == 'POST':
        image_path = request.form.get('image_path', '')
        source_type = request.form.get('source_type', '')
        source_name = request.form.get('source_name', '')
        
        if not image_path or not source_type or not source_name:
            flash('Missing required information')
            return redirect(url_for('main.index'))
        
        try:
            # Extract unique ID from the image path
            filename = os.path.basename(image_path)
            unique_id = filename.split('_')[0]
            
            # Get the original image path
            temp_dir = current_app.config['UPLOAD_FOLDER']
            original_image_path = os.path.join(temp_dir, f"{unique_id}.jpg")
            
            # Generate new meme text
            if source_type == 'band':
                top_text, bottom_text = ai_generator.generate_band_meme_text(band_name=source_name, image_path=original_image_path)
            elif source_type == 'genre':
                top_text, bottom_text = ai_generator.generate_genre_meme_text(genre=source_name, image_path=original_image_path)
            else:
                top_text, bottom_text = ai_generator.generate_meme_text(image_path=original_image_path, context="a meme about music")
            
            # Create the meme with new text
            output_path = os.path.join(current_app.config['GENERATED_FOLDER'], f"{unique_id}_meme.jpg")
            image_editor.generate_meme(
                image_path=original_image_path,
                top_text=top_text,
                bottom_text=bottom_text,
                output_filename=output_path,
                use_local_image=True
            )
            
            # Return the meme page
            return render_template('meme_result.html', 
                                  meme_path=f"/meme/{unique_id}_meme.jpg",
                                  top_text=top_text,
                                  bottom_text=bottom_text,
                                  source_type=source_type,
                                  source_name=source_name)
            
        except Exception as e:
            logger.error(f"Error regenerating meme: {e}", exc_info=True)
            flash(f'Error regenerating meme: {str(e)}')
            return redirect(url_for('main.index'))

@bp.route('/meme/<filename>')
def serve_meme(filename):
    """Serve generated meme images."""
    return send_from_directory(current_app.config['GENERATED_FOLDER'], filename)

@bp.route('/upload/<filename>')
def serve_upload(filename):
    """Serve uploaded images."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@bp.route('/gallery')
def gallery():
    """Display a gallery of previously generated memes."""
    try:
        # Get list of generated meme files
        meme_folder = current_app.config['GENERATED_FOLDER']
        meme_files = [f for f in os.listdir(meme_folder) 
                     if os.path.isfile(os.path.join(meme_folder, f)) 
                     and f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        
        # Sort by creation time (newest first)
        meme_files.sort(key=lambda x: os.path.getctime(os.path.join(meme_folder, x)), reverse=True)
        
        # Limit to most recent 20 memes
        meme_files = meme_files[:20]
        
        # Create list of meme URLs
        memes = [{'url': url_for('main.serve_meme', filename=f), 
                 'filename': f,
                 'created': os.path.getctime(os.path.join(meme_folder, f))} 
                for f in meme_files]
        
        return render_template('gallery.html', memes=memes)
        
    except Exception as e:
        logger.error(f"Error loading gallery: {e}", exc_info=True)
        flash(f'Error loading gallery: {str(e)}')
        return redirect(url_for('main.index'))

@bp.route('/about')
def about():
    """Display the about page."""
    return render_template('about.html')

@bp.route('/upload-image', methods=['POST'])
def upload_image():
    """Handle image upload."""
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}.jpg"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        target_page = request.form.get('target', 'band')
        
        if target_page == 'band':
            return redirect(url_for('main.guitar_band_memes', uploaded_image=filename))
        else:
            return redirect(url_for('main.genre_memes', uploaded_image=filename))
    else:
        flash('Invalid file type. Please upload a PNG, JPG, JPEG, or GIF file.')
        return redirect(url_for('main.index'))

@bp.route('/browse-meme-templates', methods=['GET', 'POST'])
def browse_meme_templates():
    """Browse available meme templates."""
    if request.method == 'POST':
        # Handle POST request (from other pages)
        context = request.form.get('context', 'band')
        source_name = request.form.get('source_name', '')
        return redirect(url_for('main.browse_meme_templates', context=context, source_name=source_name))
    
    # Handle GET request (direct access or redirected from POST)
    context = request.args.get('context', 'band')
    source_name = request.args.get('source_name', '')
    category = request.args.get('category', 'music')
    
    # Validate context
    if context not in ['band', 'genre']:
        context = 'band'
    
    # Get templates
    if category == 'all':
        templates = imgflip_api.get_templates()
    else:
        templates = imgflip_api.get_templates_by_category(category)
    
    return render_template('meme_templates.html', 
                          templates=templates, 
                          context=context, 
                          source_name=source_name,
                          category=category)

@bp.route('/generate-template-meme', methods=['GET', 'POST'])
def generate_template_meme():
    """Generate a meme using a selected template and AI-generated text."""
    template_id = request.args.get('template_id')
    template_url = request.args.get('template_url')
    template_name = request.args.get('template_name')
    box_count = int(request.args.get('box_count', 2))
    context = request.args.get('context', 'band')
    source_name = request.args.get('source_name', '')
    use_ai = current_app.config.get('USE_AI', True)  # Default to True if not configured
    
    # Initialize AI-generator for text creation
    ai_generator = AIMemeGenerator()
    
    # Check for OpenAI API key
    openai_api_key = current_app.config.get('OPENAI_API_KEY')
    if not openai_api_key:
        flash("OpenAI API key is not configured. Please set it in your environment variables.", "danger")
        logger.error("OpenAI API key not set")
        return redirect(url_for('main.browse_meme_templates', context=context, source_name=source_name))
    
    # Check for ImgFlip credentials
    imgflip_username = current_app.config.get('IMGFLIP_USERNAME', '')
    imgflip_password = current_app.config.get('IMGFLIP_PASSWORD', '')
    
    if not imgflip_username or not imgflip_password:
        flash("ImgFlip credentials are not configured. Please set them in your config file.", "danger")
        logger.error("ImgFlip credentials not set")
        return redirect(url_for('main.browse_meme_templates', context=context, source_name=source_name))
    else:
        imgflip_generator.set_credentials(imgflip_username, imgflip_password)
    
    # Get template metadata for context
    template_metadata = imgflip_generator.get_template_metadata(template_id)
    
    # Check if template metadata exists or needs to be generated
    if not template_metadata.get('analyzed', False) or not template_metadata.get('description') or template_metadata.get('description') == "A popular meme template.":
        if use_ai:
            # Generate template analysis using AI with improved prompt
            enhanced_prompt = f"""
Analyze this meme template thoroughly (ID: {template_id}, Box Count: {box_count})
URL: {template_url}

I need detailed information about this specific meme template to generate appropriate content:

1. Full Name: The complete/proper name of this meme template

2. Description: A detailed description of:
   - What the image actually shows (people, objects, scene)
   - The typical meaning or use of this meme in internet culture
   - What makes this template recognizable or unique

3. Format: Explain precisely how this template with {box_count} text boxes is used:
   - What specific content goes in each text area 
   - The relationship between the text areas
   - The specific format or pattern that makes this meme template work
   - If each text area represents different speakers, perspectives, or concepts

4. Example: Provide 1-2 examples of text that would typically be used in this meme, showing exactly what would go in each text area

5. Tone: The emotional tone or context this meme is typically used in (humorous, ironic, sarcastic, etc.)

Your analysis must accurately reflect this specific template's actual usage in meme culture. 
Format your response as a JSON structure with these keys: name, description, format, example, tone
"""
            template_metadata_json, analysis_prompt = ai_generator.analyze_meme_template(enhanced_prompt)
            try:
                template_metadata = json.loads(template_metadata_json)
                # Store the analysis prompt with the metadata
                template_metadata['analysis_prompt'] = analysis_prompt
            except json.JSONDecodeError:
                logger.error("Failed to parse template metadata JSON")
                template_metadata = {
                    "name": f"Template {template_id}",
                    "description": "A popular meme template.",
                    "format": f"Template with {box_count} text fields.",
                    "example": "Example text for this meme format.",
                    "tone": "Humorous, internet meme culture.",
                    "analysis_prompt": enhanced_prompt
                }
            imgflip_generator.save_template_metadata(template_id, template_metadata)
            # Also save to the API's cache for consistency
            imgflip_api.save_custom_metadata(template_id, template_metadata)
    
    # Generate meme text based on context and template
    meme_texts = []
    ai_prompts = {}
    logger.info(f"Generating {box_count} text blocks for template {template_id}")

    try:
        if context == 'band':
            text_blocks, ai_prompts = ai_generator.generate_band_meme_text(
                source_name,
                template_image_path=template_url,
                context=template_metadata,
                box_count=box_count
            )
        elif context == 'genre':
            text_blocks, ai_prompts = ai_generator.generate_genre_meme_text(
                source_name,
                template_image_path=template_url,
                context=template_metadata,
                box_count=box_count
            )
        else:
            # Default/fallback text generation
            text_blocks, ai_prompts = ai_generator.generate_meme_text(
                context="music",
                template_image_path=template_url,
                template_context=template_metadata,
                box_count=box_count
            )
        
        # Extract text blocks from response
        meme_texts = text_blocks
        logger.info(f"Generated {len(meme_texts)} text blocks successfully")
    except Exception as e:
        logger.error(f"Error generating meme text: {str(e)}", exc_info=True)
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('main.browse_meme_templates', context=context, source_name=source_name))
    
    # Output path for saving meme
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    output_filename = f"template_meme_{unique_id}.jpg"
    output_path = os.path.join(current_app.config['GENERATED_FOLDER'], output_filename)
    
    # Generate meme using ImgFlip API
    try:
        result = imgflip_generator.generate_from_template(
            template_id=template_id,
            texts=meme_texts,
            output_path=output_path
        )
        
        if result.get('success'):
            meme_url = result.get('url')
            logger.info(f"Meme generated successfully: {meme_url}")
            
            # Save meme to session for regeneration
            session['last_template_meme'] = {
                'template_id': template_id,
                'template_url': template_url,
                'template_name': template_name,
                'box_count': box_count,
                'context': context,
                'source_name': source_name,
                'texts': meme_texts
            }
            
            # Add AI prompts from template analysis if available
            if template_metadata.get('analysis_prompt'):
                ai_prompts['template_analysis_prompt'] = template_metadata.get('analysis_prompt')
            
            return render_template('template_meme_result.html',
                                  meme_url=meme_url,
                                  meme_texts=meme_texts,
                                  template_id=template_id,
                                  template_url=template_url,
                                  template_name=template_name,
                                  box_count=box_count,
                                  context=context,
                                  source_name=source_name,
                                  template_context=template_metadata,
                                  ai_prompts=ai_prompts,
                                  extra_context='')
        else:
            error_message = result.get('error_message', 'Unknown error')
            logger.error(f"Error generating meme: {error_message}")
            flash(f"Error generating meme: {error_message}", "danger")
            return redirect(url_for('main.browse_meme_templates', context=context, source_name=source_name))
    except Exception as e:
        logger.error(f"Error generating meme: {str(e)}", exc_info=True)
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('main.browse_meme_templates', context=context, source_name=source_name))

@bp.route('/regenerate-template-meme', methods=['GET', 'POST'])
def regenerate_template_meme():
    """Regenerate a meme using the same template but with new AI-generated text."""
    # Get parameters
    if request.method == 'POST':
        template_id = request.form.get('template_id')
        template_url = request.form.get('template_url')
        template_name = request.form.get('template_name')
        box_count = int(request.form.get('box_count', 2))
        context = request.form.get('context', 'band')
        source_name = request.form.get('source_name', '')
    else:
        template_id = request.args.get('template_id')
        template_url = request.args.get('template_url')
        template_name = request.args.get('template_name')
        box_count = int(request.args.get('box_count', 2))
        context = request.args.get('context', 'band')
        source_name = request.args.get('source_name', '')
    
    # Log regeneration request
    logger.info(f"Regenerating meme for template {template_id} with new AI-generated text")
    
    # Redirect to generate endpoint (which will create new AI prompts)
    return redirect(url_for('main.generate_template_meme',
                          template_id=template_id,
                          template_url=template_url,
                          template_name=template_name,
                          box_count=box_count,
                          context=context,
                          source_name=source_name))

@bp.route('/regenerate-with-updated-context', methods=['POST'])
def regenerate_with_updated_context():
    """Regenerate a meme with updated text or context."""
    template_id = request.form.get('template_id')
    template_url = request.form.get('template_url')
    template_name = request.form.get('template_name')
    box_count = int(request.form.get('box_count', 2))
    context = request.form.get('context', 'band')
    source_name = request.form.get('source_name', '')
    extra_context = request.form.get('extra_context', '')
    
    # Get user-edited text boxes
    text_boxes = request.form.getlist('text_boxes[]')
    
    # Initialize AI-generator and ImgFlip generator
    ai_generator = AIMemeGenerator()
    
    # Check for ImgFlip credentials
    imgflip_username = current_app.config.get('IMGFLIP_USERNAME', '')
    imgflip_password = current_app.config.get('IMGFLIP_PASSWORD', '')
    
    if not imgflip_username or not imgflip_password:
        flash("ImgFlip credentials are not configured. Please set them in your config file.", "danger")
        logger.error("ImgFlip credentials not set")
        return redirect(url_for('main.browse_meme_templates', context=context, source_name=source_name))
    else:
        imgflip_generator.set_credentials(imgflip_username, imgflip_password)
    
    # Get template metadata
    template_metadata = imgflip_generator.get_template_metadata(template_id)
    
    # Create AI prompts dictionary with manually provided information
    ai_prompts = {
        "user_prompt": f"User manually edited the text boxes and provided this context: {extra_context}",
        "system_prompt": "Text boxes were manually edited by the user"
    }
    
    # Add template analysis prompt if available
    if template_metadata and 'analysis_prompt' in template_metadata:
        ai_prompts['template_analysis_prompt'] = template_metadata['analysis_prompt']
    
    # Output path for saving meme
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    output_filename = f"template_meme_{unique_id}.jpg"
    output_path = os.path.join(current_app.config['GENERATED_FOLDER'], output_filename)
    
    # Generate meme using ImgFlip API with the updated text
    try:
        result = imgflip_generator.generate_from_template(
            template_id=template_id,
            texts=text_boxes,
            output_path=output_path
        )
        
        if result.get('success'):
            meme_url = result.get('url')
            logger.info(f"Meme regenerated successfully with updated context: {meme_url}")
            
            # Save meme to session for regeneration
            session['last_template_meme'] = {
                'template_id': template_id,
                'template_url': template_url,
                'template_name': template_name,
                'box_count': box_count,
                'context': context,
                'source_name': source_name,
                'texts': text_boxes
            }
            
            return render_template('template_meme_result.html',
                                  meme_url=meme_url,
                                  meme_texts=text_boxes,
                                  template_id=template_id,
                                  template_url=template_url,
                                  template_name=template_name,
                                  box_count=box_count,
                                  context=context,
                                  source_name=source_name,
                                  template_context=template_metadata,
                                  ai_prompts=ai_prompts,
                                  extra_context=extra_context)
        else:
            error_message = result.get('error_message', 'Unknown error')
            logger.error(f"Error regenerating meme: {error_message}")
            flash(f"Error regenerating meme: {error_message}", "danger")
            return redirect(url_for('main.browse_meme_templates', context=context, source_name=source_name))
    except Exception as e:
        logger.error(f"Error regenerating meme: {str(e)}", exc_info=True)
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('main.browse_meme_templates', context=context, source_name=source_name))

@bp.route('/update-template-metadata', methods=['POST'])
def update_template_metadata():
    """Update meme template metadata manually."""
    if request.method == 'POST':
        template_id = request.form.get('template_id', '')
        redirect_url = request.form.get('redirect_url', url_for('main.browse_meme_templates'))
        
        if not template_id:
            flash('Missing template ID')
            return redirect(redirect_url)
        
        try:
            # Get the metadata fields from the form
            metadata = {
                'name': request.form.get('name', ''),
                'description': request.form.get('description', ''),
                'format': request.form.get('format', ''),
                'example': request.form.get('example', ''),
                'tone': request.form.get('tone', '')
            }
            
            # Save the updated metadata
            imgflip_api.save_custom_metadata(template_id, metadata)
            
            flash(f"Template metadata has been updated successfully.", 'success')
            logger.info(f"Template {template_id} metadata manually updated: {metadata.get('name', 'Unknown')}")
            
            return redirect(redirect_url)
            
        except Exception as e:
            logger.error(f"Error updating template metadata: {e}", exc_info=True)
            flash(f'Error updating template metadata: {str(e)}')
            return redirect(redirect_url)

@bp.route('/select-band-for-template')
def select_band_for_template():
    """Select a band to use with a meme template."""
    # Get template parameters from query string
    template_id = request.args.get('template_id')
    template_url = request.args.get('template_url')
    template_name = request.args.get('template_name')
    box_count = request.args.get('box_count', 2)
    context = request.args.get('context', 'band')
    
    if not template_id or not template_url:
        flash("Missing template information", "danger")
        return redirect(url_for('main.browse_meme_templates'))
    
    # List of popular bands for quick selection
    popular_bands = [
        "The Beatles", "Queen", "Pink Floyd", "Led Zeppelin", "The Rolling Stones",
        "AC/DC", "Metallica", "Black Sabbath", "Nirvana", "Guns N' Roses",
        "Radiohead", "The Who", "U2", "The Doors", "Fleetwood Mac",
        "Aerosmith", "Eagles", "Foo Fighters", "Red Hot Chili Peppers", "Pearl Jam"
    ]
    
    return render_template('select_band.html',
                          template_id=template_id,
                          template_url=template_url,
                          template_name=template_name,
                          box_count=box_count,
                          context=context,
                          popular_bands=popular_bands)

@bp.route('/select-genre-for-template')
def select_genre_for_template():
    """Select a music genre to use with a meme template."""
    # Get template parameters from query string
    template_id = request.args.get('template_id')
    template_url = request.args.get('template_url')
    template_name = request.args.get('template_name')
    box_count = request.args.get('box_count', 2)
    context = request.args.get('context', 'genre')
    
    if not template_id or not template_url:
        flash("Missing template information", "danger")
        return redirect(url_for('main.browse_meme_templates'))
    
    # Music genres
    music_genres = [
        "Rock", "Heavy Metal", "Pop", "Hip Hop", "Jazz", 
        "Blues", "Country", "Electronic", "Classical", 
        "Reggae", "Punk Rock", "R&B", "Soul", "Folk", 
        "Indie Rock", "Techno", "Disco", "Alternative Rock", 
        "Funk", "Grunge"
    ]
    
    return render_template('select_genre.html',
                          template_id=template_id,
                          template_url=template_url,
                          template_name=template_name,
                          box_count=box_count,
                          context=context,
                          genres=music_genres)

@bp.route('/submit-band-for-template', methods=['POST'])
def submit_band_for_template():
    """Submit the selected band and generate a meme with the template."""
    if request.method == 'POST':
        template_id = request.form.get('template_id')
        template_url = request.form.get('template_url')
        template_name = request.form.get('template_name')
        box_count = request.form.get('box_count', 2)
        context = request.form.get('context', 'band')
        band_name = request.form.get('band_name', '')
        
        if not band_name:
            flash("Please enter a band name", "danger")
            return redirect(url_for('main.select_band_for_template', 
                                   template_id=template_id,
                                   template_url=template_url,
                                   template_name=template_name,
                                   box_count=box_count,
                                   context=context))
        
        # Redirect to meme generation with the band name as source_name
        return redirect(url_for('main.generate_template_meme',
                              template_id=template_id,
                              template_url=template_url,
                              template_name=template_name,
                              box_count=box_count,
                              context=context,
                              source_name=band_name))

@bp.route('/submit-genre-for-template', methods=['POST'])
def submit_genre_for_template():
    """Submit the selected genre and generate a meme with the template."""
    if request.method == 'POST':
        template_id = request.form.get('template_id')
        template_url = request.form.get('template_url')
        template_name = request.form.get('template_name')
        box_count = request.form.get('box_count', 2)
        context = request.form.get('context', 'genre')
        genre = request.form.get('genre', '')
        
        if not genre:
            flash("Please select a genre", "danger")
            return redirect(url_for('main.select_genre_for_template', 
                                   template_id=template_id,
                                   template_url=template_url,
                                   template_name=template_name,
                                   box_count=box_count,
                                   context=context))
        
        # Redirect to meme generation with the genre as source_name
        return redirect(url_for('main.generate_template_meme',
                              template_id=template_id,
                              template_url=template_url,
                              template_name=template_name,
                              box_count=box_count,
                              context=context,
                              source_name=genre))

@bp.route('/check-template-metadata', methods=['GET'])
def check_template_metadata():
    """Check all templates for missing metadata and generate it if needed."""
    # In production, this should be protected with authentication
    # For now, anyone can trigger metadata checks
    
    # Parameters
    process_limit = request.args.get('limit', '10')
    process_all = request.args.get('all', 'false').lower() == 'true'
    force_refresh = request.args.get('force', 'false').lower() == 'true'
    specific_template_id = request.args.get('template_id')
    
    # If processing a specific template
    if specific_template_id and 'process' in request.args:
        # Initialize AI-generator for text creation
        ai_generator = AIMemeGenerator()
        
        # Check for OpenAI API key
        openai_api_key = current_app.config.get('OPENAI_API_KEY')
        if not openai_api_key:
            return render_template('admin_result.html', 
                title="API Key Missing", 
                content="OpenAI API key is not configured. Please set it in your environment variables.")
        
        # Get template info
        all_templates = imgflip_api.get_templates()
        template = next((t for t in all_templates if t.get('id') == specific_template_id), None)
        
        if not template:
            return render_template('admin_result.html', 
                title="Template Not Found", 
                content=f"Template with ID {specific_template_id} not found.")
        
        # Generate metadata for this specific template
        template_id = template.get('id')
        template_url = template.get('url')
        template_name = template.get('name')
        box_count = template.get('box_count', 2)
        
        # Generate template analysis using AI with improved prompt
        enhanced_prompt = f"""
Analyze this meme template thoroughly (ID: {template_id}, Box Count: {box_count})
URL: {template_url}

I need detailed information about this specific meme template to generate appropriate content:

1. Full Name: The complete/proper name of this meme template

2. Description: A detailed description of:
   - What the image actually shows (people, objects, scene)
   - The typical meaning or use of this meme in internet culture
   - What makes this template recognizable or unique

3. Format: Explain precisely how this template with {box_count} text boxes is used:
   - What specific content goes in each text area 
   - The relationship between the text areas
   - The specific format or pattern that makes this meme template work
   - If each text area represents different speakers, perspectives, or concepts

4. Example: Provide 1-2 examples of text that would typically be used in this meme, showing exactly what would go in each text area

5. Tone: The emotional tone or context this meme is typically used in (humorous, ironic, sarcastic, etc.)

Your analysis must accurately reflect this specific template's actual usage in meme culture. 
Format your response as a JSON structure with these keys: name, description, format, example, tone
"""
        
        try:
            template_metadata_json, analysis_prompt = ai_generator.analyze_meme_template(enhanced_prompt)
            try:
                template_metadata = json.loads(template_metadata_json)
                # Store the analysis prompt with the metadata
                template_metadata['analysis_prompt'] = analysis_prompt
                template_metadata['analyzed'] = True
                imgflip_api.save_custom_metadata(template_id, template_metadata)
                
                content = f"""
<h4>Successfully processed template: {template_name}</h4>
<div class="row mb-4">
    <div class="col-md-4">
        <img src="{template_url}" class="img-fluid rounded" alt="{template_name}">
    </div>
    <div class="col-md-8">
        <div class="card">
            <div class="card-body">
                <pre class="bg-light p-3">{json.dumps(template_metadata, indent=2)}</pre>
            </div>
        </div>
    </div>
</div>
<a href="{url_for('main.browse_meme_templates')}" class="btn btn-primary">Return to Templates</a>
"""
                return render_template('admin_result.html', 
                    title=f"Template Metadata for {template_name}", 
                    content=content)
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse template metadata JSON for {template_id}")
                return render_template('admin_result.html', 
                    title="JSON Parse Error", 
                    content=f"Failed to parse JSON response for template: {template_name}")
                
        except Exception as e:
            logger.error(f"Error analyzing template {template_id}: {str(e)}")
            return render_template('admin_result.html', 
                title="Processing Error", 
                content=f"Error processing template {template_name}: {str(e)}")
    
    # Get all templates for the batch processing mode
    all_templates = imgflip_api.get_templates()
    
    # Check which templates need metadata
    templates_needing_metadata = []
    templates_with_metadata = []
    
    for template in all_templates:
        template_id = template.get('id')
        metadata = imgflip_api.get_template_metadata(template_id)
        
        # Determine if metadata needs to be generated/refreshed
        needs_metadata = (
            force_refresh or 
            not metadata.get('analyzed', False) or 
            not metadata.get('description') or 
            metadata.get('description') == "A popular meme template."
        )
        
        if needs_metadata:
            templates_needing_metadata.append(template)
        else:
            templates_with_metadata.append(template)
    
    # Process templates if requested for batch mode
    processed_templates = []
    errors = []
    
    if 'process' in request.args and not specific_template_id:
        # Initialize AI-generator for text creation
        ai_generator = AIMemeGenerator()
        
        # Check for OpenAI API key
        openai_api_key = current_app.config.get('OPENAI_API_KEY')
        if not openai_api_key:
            return render_template('admin_result.html', 
                title="API Key Missing", 
                content="OpenAI API key is not configured. Please set it in your environment variables.")
        
        # Determine how many templates to process
        if process_all:
            templates_to_process = templates_needing_metadata
        else:
            try:
                limit = int(process_limit)
            except ValueError:
                limit = 10
            templates_to_process = templates_needing_metadata[:limit]
        
        for template in templates_to_process:
            template_id = template.get('id')
            template_url = template.get('url')
            box_count = template.get('box_count', 2)
            
            # Generate template analysis using AI with improved prompt
            enhanced_prompt = f"""
Analyze this meme template thoroughly (ID: {template_id}, Box Count: {box_count})
URL: {template_url}

I need detailed information about this specific meme template to generate appropriate content:

1. Full Name: The complete/proper name of this meme template

2. Description: A detailed description of:
   - What the image actually shows (people, objects, scene)
   - The typical meaning or use of this meme in internet culture
   - What makes this template recognizable or unique

3. Format: Explain precisely how this template with {box_count} text boxes is used:
   - What specific content goes in each text area 
   - The relationship between the text areas
   - The specific format or pattern that makes this meme template work
   - If each text area represents different speakers, perspectives, or concepts

4. Example: Provide 1-2 examples of text that would typically be used in this meme, showing exactly what would go in each text area

5. Tone: The emotional tone or context this meme is typically used in (humorous, ironic, sarcastic, etc.)

Your analysis must accurately reflect this specific template's actual usage in meme culture. 
Format your response as a JSON structure with these keys: name, description, format, example, tone
"""
            try:
                template_metadata_json, analysis_prompt = ai_generator.analyze_meme_template(enhanced_prompt)
                try:
                    template_metadata = json.loads(template_metadata_json)
                    # Store the analysis prompt with the metadata
                    template_metadata['analysis_prompt'] = analysis_prompt
                    template_metadata['analyzed'] = True
                    imgflip_api.save_custom_metadata(template_id, template_metadata)
                    processed_templates.append({
                        'id': template_id,
                        'name': template.get('name', 'Unknown'),
                        'success': True,
                        'metadata': template_metadata
                    })
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse template metadata JSON for {template_id}")
                    errors.append(f"Failed to parse JSON for {template_id}: {template.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error analyzing template {template_id}: {str(e)}")
                errors.append(f"Error processing {template_id}: {template.get('name', 'Unknown')} - {str(e)}")
    
    # Format stats and results for display
    stats = {
        'total_templates': len(all_templates),
        'templates_with_metadata': len(templates_with_metadata),
        'templates_needing_metadata': len(templates_needing_metadata),
        'templates_processed': len(processed_templates),
        'errors': len(errors)
    }
    
    # Generate result content
    content = f"""
<h4>Template Metadata Stats:</h4>
<ul>
    <li>Total Templates: {stats['total_templates']}</li>
    <li>Templates with Metadata: {stats['templates_with_metadata']}</li>
    <li>Templates Needing Metadata: {stats['templates_needing_metadata']}</li>
</ul>

<h4>Actions:</h4>
<div class="mb-3">
    <a href="{url_for('main.check_template_metadata', process='true', limit=10)}" class="btn btn-primary">Process 10 Templates</a>
    <a href="{url_for('main.check_template_metadata', process='true', limit=25)}" class="btn btn-primary">Process 25 Templates</a>
    <a href="{url_for('main.check_template_metadata', process='true', all='true')}" class="btn btn-warning">Process All Templates</a>
    <a href="{url_for('main.check_template_metadata', process='true', force='true', limit=10)}" class="btn btn-danger">Force Refresh 10 Templates</a>
</div>
"""
    
    # Add processing results if any
    if processed_templates:
        content += f"""
<h4>Processed Templates ({stats['templates_processed']}):</h4>
<div class="accordion" id="processedTemplatesAccordion">
"""
        for i, template in enumerate(processed_templates):
            content += f"""
<div class="accordion-item">
    <h2 class="accordion-header" id="heading{i}">
        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse{i}" aria-expanded="false" aria-controls="collapse{i}">
            {template['name']} (ID: {template['id']})
        </button>
    </h2>
    <div id="collapse{i}" class="accordion-collapse collapse" aria-labelledby="heading{i}" data-bs-parent="#processedTemplatesAccordion">
        <div class="accordion-body">
            <pre class="bg-light p-3">{json.dumps(template['metadata'], indent=2)}</pre>
        </div>
    </div>
</div>
"""
        content += "</div>"
    
    # Add errors if any
    if errors:
        content += f"""
<h4>Errors ({stats['errors']}):</h4>
<ul class="list-group">
"""
        for error in errors:
            content += f'<li class="list-group-item list-group-item-danger">{error}</li>'
        content += "</ul>"
    
    return render_template('admin_result.html', 
        title="Template Metadata Check", 
        content=content)

# Add template context processor for accessing template metadata in templates
@bp.app_context_processor
def inject_template_metadata():
    """
    Make the template metadata function available to Jinja templates.
    """
    def get_template_metadata(template_id):
        """Get metadata for a template by ID"""
        return imgflip_api.get_template_metadata(template_id)
    
    return dict(get_template_metadata=get_template_metadata) 