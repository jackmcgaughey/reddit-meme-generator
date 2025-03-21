"""
Main routes for the Shreddit Meme Generator web application.
"""
import os
import uuid
import logging
import requests
import random
from flask import (
    Blueprint, flash, g, redirect, render_template, request,
    url_for, current_app, send_from_directory, jsonify
)
from werkzeug.utils import secure_filename

from config_manager import ConfigManager
from reddit_api import RedditMemeAPI
from ai_meme_generator import AIMemeGenerator
from image_editor import MemeEditor

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
    # Common music genres
    music_genres = [
        "Rock", "Metal", "Pop", "Hip Hop", "Jazz", "Blues", 
        "Country", "Electronic", "Classical", "Reggae", "Punk", 
        "R&B", "Soul", "Folk", "Indie", "Techno", "Disco",
        "Alternative", "Funk", "Grunge"
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
            # Search for genre images - get 30 to have enough after filtering
            images = reddit_api.search_genre_images(genre, limit=30)
            if not images:
                # Fallback to guitar memes if no genre images found
                flash(f'No images found for genre: {genre}. Showing guitar memes instead.')
                images = reddit_api.get_guitar_memes(limit=20)
            
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