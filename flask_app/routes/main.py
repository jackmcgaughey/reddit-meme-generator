"""
Main routes for the Shreddit Meme Generator web application.
"""
import os
import uuid
import logging
import requests
import random
import time
from flask import (
    Blueprint, flash, g, redirect, render_template, request,
    url_for, current_app, send_from_directory, jsonify
)
from werkzeug.utils import secure_filename

from config_manager import ConfigManager
from reddit_api import RedditMemeAPI
from ai_meme_generator import AIMemeGenerator
from image_editor import MemeEditor
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

# Initialize ImgFlip generator
imgflip_generator = ImgFlipGenerator()

# Load ImgFlip credentials from environment variables
import os
from dotenv import load_dotenv
load_dotenv()

imgflip_username = os.environ.get('IMGFLIP_USERNAME', '')
imgflip_password = os.environ.get('IMGFLIP_PASSWORD', '')
if imgflip_username and imgflip_password:
    imgflip_generator.set_credentials(imgflip_username, imgflip_password)
    logger.info("ImgFlip credentials loaded from environment variables")
else:
    logger.warning("ImgFlip credentials not found in environment variables")

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

@bp.route('/meme-templates')
def meme_templates():
    """
    Render the meme templates browsing page.
    This shows templates from ImgFlip that can be used for meme generation.
    """
    # Get templates from ImgFlip API
    templates = imgflip_generator.get_popular_templates()
    
    # Get filter parameters
    search_query = request.args.get('search', '')
    box_count = request.args.get('box_count', '')
    
    # Apply filters if provided
    if search_query:
        templates = imgflip_generator.search_templates(search_query)
    if box_count and box_count.isdigit():
        templates = imgflip_generator.filter_templates_by_box_count(int(box_count))
    
    # Get analysis status for each template
    for template in templates:
        template_id = str(template['id'])
        template['is_analyzed'] = imgflip_generator.is_template_analyzed(template_id)
    
    return render_template('meme_templates.html', templates=templates)

@bp.route('/analyze-template/<template_id>')
def analyze_template(template_id):
    """
    Analyze a specific template to understand its context and usage.
    """
    # Check if template is already analyzed
    if imgflip_generator.is_template_analyzed(template_id):
        flash('Template already analyzed')
        return redirect(url_for('main.meme_templates'))
    
    # Find the template data
    templates = imgflip_generator.get_popular_templates()
    template = None
    for t in templates:
        if str(t['id']) == template_id:
            template = t
            break
    
    if not template:
        flash('Template not found')
        return redirect(url_for('main.meme_templates'))
    
    # Create analysis prompt
    prompt = imgflip_generator.create_template_analysis_prompt(
        template_id=template_id,
        box_count=template['box_count'],
        template_url=template['url']
    )
    
    # Analyze the template
    try:
        analysis = ai_generator.analyze_meme_template(prompt)
        
        # Save analysis to metadata cache
        if analysis and analysis.get('analyzed', False):
            imgflip_generator.save_template_metadata(template_id, analysis)
            flash('Template analysis completed successfully')
        else:
            flash('Template analysis failed')
            
    except Exception as e:
        logger.error(f"Error analyzing template: {str(e)}")
        flash(f'Error analyzing template: {str(e)}')
    
    return redirect(url_for('main.template_details', template_id=template_id))

@bp.route('/template-details/<template_id>')
def template_details(template_id):
    """
    Show details for a specific template, including its analysis if available.
    """
    # Get template metadata
    metadata = imgflip_generator.get_template_metadata(template_id)
    
    # Find the template data
    templates = imgflip_generator.get_popular_templates()
    template = None
    for t in templates:
        if str(t['id']) == template_id:
            template = t
            break
    
    if not template:
        flash('Template not found')
        return redirect(url_for('main.meme_templates'))
    
    # Merge metadata with template data
    template_data = {**template, **metadata}
    
    return render_template('template_details.html', template=template_data)

@bp.route('/analyze-templates-batch')
def analyze_templates_batch():
    """
    Analyze a batch of templates to understand their context and usage.
    This is an admin function to prime the cache.
    """
    # Get the number of templates to analyze
    count = request.args.get('count', '10')
    try:
        count = int(count)
    except ValueError:
        count = 10
    
    # Get templates
    templates = imgflip_generator.get_popular_templates()
    
    # Filter to only unanalyzed templates
    unanalyzed = []
    for template in templates:
        template_id = str(template['id'])
        if not imgflip_generator.is_template_analyzed(template_id):
            unanalyzed.append(template)
            if len(unanalyzed) >= count:
                break
    
    if not unanalyzed:
        flash('No templates need analysis')
        return redirect(url_for('main.meme_templates'))
    
    # Analyze the templates
    try:
        results = ai_generator.analyze_template_batch(unanalyzed, imgflip_generator)
        flash(f'Successfully analyzed {len(results)} templates')
    except Exception as e:
        logger.error(f"Error in batch template analysis: {str(e)}")
        flash(f'Error analyzing templates: {str(e)}')
    
    return redirect(url_for('main.meme_templates'))

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

@bp.route('/generate-template-meme', methods=['GET', 'POST'])
def generate_template_meme():
    """
    Generate a meme using an ImgFlip template with AI-generated text about a band or genre.
    """
    # Get parameters
    if request.method == 'POST':
        template_id = request.form.get('template_id', '')
        template_url = request.form.get('template_url', '')
        template_name = request.form.get('template_name', '')
        box_count = request.form.get('box_count', 2)
        content_type = request.form.get('content_type', 'band')
        band_name = request.form.get('band_name', '')
        genre = request.form.get('genre', '')
        context = request.form.get('context', '')
        regenerate_text_only = request.form.get('regenerate_text_only', 'false') == 'true'
    else:
        template_id = request.args.get('template_id', '')
        template_url = request.args.get('template_url', '')
        template_name = request.args.get('template_name', '')
        box_count = request.args.get('box_count', 2)
        content_type = request.args.get('content_type', 'band')
        band_name = request.args.get('band_name', '')
        genre = request.args.get('genre', '')
        context = request.args.get('context', '')
        regenerate_text_only = request.args.get('regenerate_text_only', 'false') == 'true'
    
    # Validate input
    try:
        box_count = int(box_count)
    except ValueError:
        box_count = 2
    
    if not template_id:
        flash('Template ID is required')
        return redirect(url_for('main.meme_templates'))
    
    if content_type == 'band' and not band_name:
        flash('Band name is required')
        return redirect(url_for('main.template_details', template_id=template_id))
    
    if content_type == 'genre' and not genre:
        flash('Genre is required')
        return redirect(url_for('main.template_details', template_id=template_id))
    
    # Ensure ImgFlip credentials are set
    if not imgflip_username or not imgflip_password:
        flash("ImgFlip credentials are not configured. Please set them in your .env file.", "danger")
        logger.error("ImgFlip credentials not set. Cannot generate meme.")
        return redirect(url_for('main.template_details', template_id=template_id))
        
    imgflip_generator.set_credentials(imgflip_username, imgflip_password)
    
    # Get template metadata and check if it's been analyzed
    template_metadata = imgflip_generator.get_template_metadata(template_id)
    
    # If template isn't analyzed or if forced regeneration is requested, analyze it
    if not template_metadata.get('analyzed', False) or regenerate_text_only:
        # Create analysis prompt
        prompt = imgflip_generator.create_template_analysis_prompt(
            template_id=template_id,
            box_count=box_count,
            template_url=template_url
        )
        
        try:
            # Analyze the template
            analysis = ai_generator.analyze_meme_template(prompt)
            
            # Save analysis to metadata cache if successful and we're not just regenerating text
            if analysis and analysis.get('analyzed', False) and not regenerate_text_only:
                imgflip_generator.save_template_metadata(template_id, analysis)
                template_metadata = analysis
                logger.info(f"Generated new template analysis for {template_id}")
        except Exception as e:
            logger.error(f"Error analyzing template: {str(e)}")
            flash(f"Error analyzing template: {str(e)}")
            return redirect(url_for('main.template_details', template_id=template_id))
    
    # If we're regenerating text only, use the existing template metadata
    
    # Generate template-specific meme text
    band_or_genre = band_name if content_type == 'band' else genre
    is_band = content_type == 'band'
    
    try:
        meme_texts = ai_generator.generate_template_specific_meme_text(
            template_analysis=template_metadata,
            band_or_genre=band_or_genre,
            context=context,
            is_band=is_band
        )
        
        # Ensure we have enough text items for the box count
        while len(meme_texts) < box_count:
            meme_texts.append("")
        
        # Truncate to the required number of boxes
        meme_texts = meme_texts[:box_count]
        
        logger.info(f"Generated template-specific text for {template_name}: {meme_texts}")
    except Exception as e:
        logger.error(f"Error generating template-specific meme text: {str(e)}")
        flash(f"Error generating meme text: {str(e)}")
        return redirect(url_for('main.template_details', template_id=template_id))
    
    # Generate output file path
    output_filename = f"template_meme_{template_id}_{uuid.uuid4().hex[:8]}.jpg"
    output_path = os.path.join(current_app.config['GENERATED_FOLDER'], output_filename)
    
    # Generate the meme
    try:
        result = imgflip_generator.generate_from_template(
            template_id=template_id,
            texts=meme_texts,
            output_path=output_path
        )
        
        if result["success"]:
            logger.info(f"Successfully generated template meme: {result['url']}")
            
            # Store generation info for display
            meme_info = {
                "url": result["url"],
                "local_path": result.get("local_path", output_path),
                "template_name": template_name,
                "template_id": template_id,
                "template_url": template_url,
                "texts": meme_texts,
                "content_type": content_type,
                "band_or_genre": band_or_genre,
                "context": context,
                "box_count": box_count,
                "generation_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Render the template meme result page
            return render_template('template_meme_result.html', meme=meme_info)
        else:
            logger.error(f"Error generating meme: {result.get('error_message', 'Unknown error')}")
            flash(f"Error generating meme: {result.get('error_message', 'Unknown error')}")
            return redirect(url_for('main.template_details', template_id=template_id))
            
    except Exception as e:
        logger.error(f"Unexpected error generating template meme: {str(e)}")
        flash(f"Unexpected error: {str(e)}")
        return redirect(url_for('main.template_details', template_id=template_id))

@bp.route('/regenerate-template-meme', methods=['GET', 'POST'])
def regenerate_template_meme():
    """
    Regenerate a meme using the same template but with new AI-generated text.
    """
    # Get parameters
    if request.method == 'POST':
        template_id = request.form.get('template_id', '')
        template_url = request.form.get('template_url', '')
        template_name = request.form.get('template_name', '')
        box_count = request.form.get('box_count', 2)
        content_type = request.form.get('content_type', 'band')
        band_or_genre = request.form.get('band_or_genre', '')
        context = request.form.get('context', '')
    else:
        template_id = request.args.get('template_id', '')
        template_url = request.args.get('template_url', '')
        template_name = request.args.get('template_name', '')
        box_count = request.args.get('box_count', 2)
        content_type = request.args.get('content_type', 'band')
        band_or_genre = request.args.get('band_or_genre', '')
        context = request.args.get('context', '')
    
    logger.info(f"Regenerating template meme for template {template_id} with {content_type} {band_or_genre}")
    
    # Redirect to generate-template-meme with regenerate_text_only flag
    return redirect(url_for(
        'main.generate_template_meme',
        template_id=template_id,
        template_url=template_url,
        template_name=template_name,
        box_count=box_count,
        content_type=content_type,
        band_name=band_or_genre if content_type == 'band' else '',
        genre=band_or_genre if content_type == 'genre' else '',
        context=context,
        regenerate_text_only='true'
    )) 