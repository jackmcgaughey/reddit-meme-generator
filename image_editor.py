"""
Image editor module for processing meme images.
"""
import os
import uuid
import logging
import requests
from io import BytesIO
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemeEditor:
    """Class to handle meme image editing and text generation."""
    
    def __init__(self, font_path: Optional[str] = None, output_dir: str = "generated_memes"):
        """
        Initialize the meme editor.
        
        Args:
            font_path: Path to font file, if None uses default
            output_dir: Directory to save generated memes
        """
        # Create output directory if it doesn't exist
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Set up font
        if font_path and os.path.exists(font_path):
            self.font_path = font_path
        else:
            # Use default system font if specified font doesn't exist
            try:
                # Try to find Arial
                if os.path.exists("/Library/Fonts/Arial.ttf"):
                    self.font_path = "/Library/Fonts/Arial.ttf"
                elif os.path.exists("/Library/Fonts/Arial Bold.ttf"):
                    self.font_path = "/Library/Fonts/Arial Bold.ttf"
                # Try to find another system font
                elif os.path.exists("/System/Library/Fonts/Supplemental/Impact.ttf"):
                    self.font_path = "/System/Library/Fonts/Supplemental/Impact.ttf"
                else:
                    # Default to a PIL built-in font
                    self.font_path = None
                    logger.warning("No suitable font found, will use PIL default")
            except Exception as e:
                logger.error(f"Error finding system font: {e}")
                self.font_path = None
                
        logger.info(f"Meme editor initialized with font: {self.font_path}")
    
    def generate_meme(
        self, 
        image_url: str, 
        top_text: str = "", 
        bottom_text: str = "",
        text_color: Tuple[int, int, int] = (255, 255, 255),  # white
        outline_color: Tuple[int, int, int] = (0, 0, 0),     # black
        output_filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a meme by adding text to an image.
        
        Args:
            image_url: URL of the image to use as base
            top_text: Text to add at the top of the image
            bottom_text: Text to add at the bottom of the image
            text_color: RGB color tuple for the text
            outline_color: RGB color tuple for the text outline
            output_filename: Optional custom filename, if None uses a UUID
            
        Returns:
            Path to the generated meme image or None if failed
        """
        try:
            # Download the image
            logger.info(f"Downloading image: {image_url}")
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            img = Image.open(BytesIO(response.content))
            
            # Get image dimensions
            width, height = img.size
            
            # Create a drawing context
            draw = ImageDraw.Draw(img)
            
            # Calculate font size based on image dimensions
            font_size = int(width / 12)  # Adjust font size to image width
            
            # Load font
            try:
                if self.font_path:
                    font = ImageFont.truetype(self.font_path, font_size)
                else:
                    # Use default font
                    font = ImageFont.load_default()
                    # Scale default font to be more visible
                    font_size = int(width / 20)
            except Exception as e:
                logger.error(f"Error loading font, falling back to default: {e}")
                font = ImageFont.load_default()
                font_size = int(width / 20)
            
            # Add top text
            if top_text:
                self._add_text_with_outline(
                    draw, 
                    top_text, 
                    (width/2, height*0.1),  # Position at top
                    font, 
                    text_color, 
                    outline_color
                )
                
            # Add bottom text
            if bottom_text:
                self._add_text_with_outline(
                    draw, 
                    bottom_text, 
                    (width/2, height*0.9),  # Position at bottom
                    font, 
                    text_color, 
                    outline_color
                )
            
            # Generate output filename if not provided
            if not output_filename:
                file_uuid = uuid.uuid4().hex[:8]
                output_filename = f"meme_{file_uuid}.jpg"
                
            # Ensure it has a file extension
            if not output_filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                output_filename += '.jpg'
                
            # Full path
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Save image
            img.save(output_path, quality=95)
            logger.info(f"Meme saved to: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating meme: {e}")
            return None
    
    def _add_text_with_outline(
        self, 
        draw: ImageDraw.Draw, 
        text: str, 
        position: Tuple[float, float], 
        font: ImageFont.FreeTypeFont,
        text_color: Tuple[int, int, int],
        outline_color: Tuple[int, int, int],
        outline_width: int = 2
    ) -> None:
        """
        Add text with an outline to make it readable on any background.
        
        Args:
            draw: PIL drawing context
            text: Text to add
            position: (x, y) center position
            font: Font to use
            text_color: RGB color tuple for text
            outline_color: RGB color tuple for outline
            outline_width: Width of the outline in pixels
        """
        # Convert text to uppercase for meme style
        text = text.upper()
        
        # Get text size for centering
        try:
            # Calculate text size for PIL's text rendering 
            # Note: GetTextSize is deprecated in newer PIL versions,
            # but for backward compatibility we'll use try/except
            try:
                text_width, text_height = draw.textsize(text, font=font)
            except AttributeError:
                # For newer PIL versions
                text_width, text_height = font.getmask(text).getbbox()[2:4]
        except Exception:
            # Fallback if text size calculation fails
            text_width, text_height = len(text) * font.size // 2, font.size
        
        # Calculate position for centered text
        x, y = position
        x -= text_width // 2
        y -= text_height // 2
        
        # Draw the outline by offsetting the text slightly in each direction
        for offset_x in range(-outline_width, outline_width + 1):
            for offset_y in range(-outline_width, outline_width + 1):
                if offset_x == 0 and offset_y == 0:
                    continue  # Skip the center (will be drawn last)
                draw.text((x + offset_x, y + offset_y), text, font=font, fill=outline_color)
        
        # Draw the main text
        draw.text((x, y), text, font=font, fill=text_color) 