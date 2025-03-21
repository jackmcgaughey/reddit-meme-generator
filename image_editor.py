"""
Image editor module for processing meme images.
"""
import os
import uuid
import logging
import requests
from io import BytesIO
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

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
        image_path: str, 
        top_text: str = "", 
        bottom_text: str = "",
        text_color: Tuple[int, int, int] = (255, 255, 255),  # white
        outline_color: Tuple[int, int, int] = (0, 0, 0),     # black
        output_filename: Optional[str] = None,
        use_local_image: bool = False
    ) -> Optional[str]:
        """
        Generate a meme image with text overlays.
        
        Args:
            image_path: URL or local path to the base image
            top_text: Text to overlay at the top of the image
            bottom_text: Text to overlay at the bottom of the image
            text_color: RGB tuple for text color
            outline_color: RGB tuple for text outline color
            output_filename: Optional custom filename, if None uses a UUID
            use_local_image: If True, image_path is treated as a local file path
            
        Returns:
            Path to the generated meme image or None if failed
        """
        try:
            # Get the image
            if use_local_image:
                # Load from local file
                logger.info(f"Loading local image: {image_path}")
                img = self._load_image_safe(image_path)
            else:
                # Download from URL
                logger.info(f"Downloading image: {image_path}")
                try:
                    response = requests.get(image_path, timeout=10)
                    response.raise_for_status()
                    
                    # Check if this is a video URL by examining content type
                    content_type = response.headers.get('Content-Type', '').lower()
                    if 'video' in content_type:
                        raise ValueError("Cannot process video content. Video support will be added in a future update.")
                    
                    img = self._load_image_safe(BytesIO(response.content))
                except requests.RequestException as e:
                    if 'video' in str(e).lower() or '.mp4' in image_path.lower() or 'v.redd.it' in image_path.lower():
                        raise ValueError("Cannot process video content. Video support will be added in a future update.")
                    else:
                        raise
            
            # Get image dimensions
            width, height = img.size
            
            # Create a drawing context
            draw = ImageDraw.Draw(img)
            
            # Calculate font size based on image dimensions
            base_font_size = int(width / 12)  # Initial font size based on image width
            
            # Load font
            try:
                if self.font_path:
                    font = ImageFont.truetype(self.font_path, base_font_size)
                else:
                    # Use default font
                    font = ImageFont.load_default()
                    # Scale default font to be more visible
                    base_font_size = int(width / 20)
            except Exception as e:
                logger.error(f"Error loading font, falling back to default: {e}")
                font = ImageFont.load_default()
                base_font_size = int(width / 20)
            
            # Add top text with margin check
            if top_text:
                # Calculate safe margins
                margin_y = height * 0.05  # 5% margin from top
                self._add_text_with_outline(
                    draw,
                    img.size, 
                    top_text, 
                    (width/2, margin_y + base_font_size),  # Position at top with margin
                    font,
                    base_font_size, 
                    text_color, 
                    outline_color,
                    position_type="top"  # Indicate this is top text
                )
                
            # Add bottom text with margin check
            if bottom_text:
                # Calculate safe margins
                margin_y = height * 0.05  # 5% margin from bottom
                self._add_text_with_outline(
                    draw,
                    img.size, 
                    bottom_text, 
                    (width/2, height - margin_y - base_font_size),  # Position at bottom with margin
                    font,
                    base_font_size, 
                    text_color, 
                    outline_color,
                    position_type="bottom"  # Indicate this is bottom text
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
        image_size: Tuple[int, int], 
        text: str, 
        position: Tuple[float, float], 
        font: ImageFont.FreeTypeFont,
        base_font_size: int,
        text_color: Tuple[int, int, int],
        outline_color: Tuple[int, int, int],
        outline_width: int = 2,
        position_type: str = "top"  # Either "top" or "bottom"
    ) -> None:
        """
        Add text with an outline to make it readable on any background.
        Ensures text stays within image boundaries.
        
        Args:
            draw: PIL drawing context
            image_size: (width, height) of the image
            text: Text to add
            position: (x, y) center position
            font: Font to use
            base_font_size: Base font size calculated from image width
            text_color: RGB color tuple for text
            outline_color: RGB color tuple for outline
            outline_width: Width of the outline in pixels
            position_type: Whether this is "top" or "bottom" text
        """
        width, height = image_size
        
        # Minimum margin in pixels (5% of image height)
        min_margin = height * 0.05
        
        # Convert text to uppercase for meme style
        text = text.upper()
        
        # Function to calculate text size with given font size
        def get_text_size(font_size, measure_text=text):
            try:
                # Create a temporary font with the specified size
                if self.font_path:
                    temp_font = ImageFont.truetype(self.font_path, font_size)
                else:
                    # If we can't get a specific size from default font, make a reasonable estimate
                    temp_font = font
                    # For newer PIL versions
                try:
                    text_width, text_height = draw.textsize(measure_text, font=temp_font)
                except AttributeError:
                    # For newer PIL versions
                    text_bbox = temp_font.getbbox(measure_text)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                
                return temp_font, text_width, text_height
            except Exception as e:
                logger.error(f"Error calculating text size: {e}")
                # Fallback to estimate text size
                return font, len(text) * font_size // 2, font_size
        
        # Start with the base font size
        current_font_size = base_font_size
        current_font, text_width, text_height = get_text_size(current_font_size)
        
        # If text is too wide, reduce font size until it fits within 90% of the image width
        max_width = width * 0.9  # 90% of image width
        while text_width > max_width and current_font_size > 12:  # Don't go below 12pt
            current_font_size -= 2
            current_font, text_width, text_height = get_text_size(current_font_size)
        
        # If text is still too wide, we'll split it into multiple lines
        if text_width > max_width:
            # Split text into words
            words = text.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = current_line + [word]
                test_text = " ".join(test_line)
                # Pass the actual test_text to measure
                _, test_width, _ = get_text_size(current_font_size, test_text)
                
                if test_width <= max_width:
                    current_line = test_line
                else:
                    if current_line:  # Add current line if not empty
                        lines.append(" ".join(current_line))
                    current_line = [word]
            
            # Add the last line
            if current_line:
                lines.append(" ".join(current_line))
            
            # Recalculate position for multi-line text
            x, y = position
            if position_type == "top":
                # For top text, start at the original y position and go down
                y_offset = 0
            else:
                # For bottom text, calculate upward from the bottom position
                y_offset = -text_height * (len(lines) - 1)
            
            # Draw each line
            for line in lines:
                # Get text size for this specific line
                _, line_width, line_height = get_text_size(current_font_size, line)
                
                # Calculate position
                x_pos = x - line_width // 2
                y_pos = y + y_offset - line_height // 2
                
                # Draw the outline
                for offset_x in range(-outline_width, outline_width + 1):
                    for offset_y in range(-outline_width, outline_width + 1):
                        if offset_x == 0 and offset_y == 0:
                            continue
                        draw.text((x_pos + offset_x, y_pos + offset_y), line, font=current_font, fill=outline_color)
                
                # Draw the main text
                draw.text((x_pos, y_pos), line, font=current_font, fill=text_color)
                
                # Update y position for next line
                y_offset += line_height + 5  # Add 5px spacing between lines
        else:
            # Draw single line text
            # Calculate position for centered text
            x, y = position
            x_pos = x - text_width // 2
            y_pos = y - text_height // 2
            
            # Draw the outline
            for offset_x in range(-outline_width, outline_width + 1):
                for offset_y in range(-outline_width, outline_width + 1):
                    if offset_x == 0 and offset_y == 0:
                        continue
                    draw.text((x_pos + offset_x, y_pos + offset_y), text, font=current_font, fill=outline_color)
            
            # Draw the main text
            draw.text((x_pos, y_pos), text, font=current_font, fill=text_color) 

    def _load_image_safe(self, image_source) -> Image.Image:
        """
        Safely load an image from a file path, URL, or bytes buffer,
        handling different formats and providing clear error messages.
        
        Args:
            image_source: Path, BytesIO, or other readable source
            
        Returns:
            PIL Image object
            
        Raises:
            ValueError: If image cannot be loaded or is an unsupported format
        """
        try:
            # Handle string paths
            if isinstance(image_source, str):
                if os.path.exists(image_source):
                    # It's a local file path
                    img = Image.open(image_source)
                else:
                    raise ValueError(f"File not found: {image_source}")
            else:
                # Handle BytesIO or other file-like objects
                img = Image.open(image_source)
            
            # Convert to RGB if it's RGBA, to ensure compatibility
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
                
            return img
        except UnidentifiedImageError:
            # Handle cases where PIL can't identify the image format
            raise ValueError("Unable to process image - unsupported or corrupted format")
        except Exception as e:
            raise ValueError(f"Error loading image: {str(e)}") 