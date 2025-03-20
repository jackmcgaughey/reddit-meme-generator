import requests
from PIL import Image, ImageDraw, ImageFont
import os

class ImageEditor:
    """Handles image downloading and text overlay."""
    
    def __init__(self, font_path="arial.ttf", font_size=40):
        """Initialize with font settings."""
        self.font_path = font_path
        self.font_size = font_size
    
    def add_text_to_image(self, image_url, top_text, bottom_text, output_path="custom_meme.png"):
        """
        Download an image, add text, and save the result.
        Args:
            image_url (str): URL of the image to download.
            top_text (str): Text for the top of the image.
            bottom_text (str): Text for the bottom of the image.
            output_path (str): Path to save the customized image.
        Returns:
            str: Path to the saved image, or None if failed.
        """
        # Download the image
        temp_path = "temp_meme.jpg"
        response = requests.get(image_url)
        if response.status_code != 200:
            print("Failed to download image.")
            return None
        with open(temp_path, 'wb') as f:
            f.write(response.content)
        
        # Open and prepare the image
        image = Image.open(temp_path)
        draw = ImageDraw.Draw(image)
        
        # Load font
        try:
            font = ImageFont.truetype(self.font_path, self.font_size)
        except IOError:
            print(f"Font not found at {self.font_path}. Please provide a valid font file.")
            os.remove(temp_path)
            return None
        
        # Calculate text positions
        width, height = image.size
        top_text_width, top_text_height = font.getsize(top_text)
        bottom_text_width, bottom_text_height = font.getsize(bottom_text)
        top_position = ((width - top_text_width) / 2, 10)
        bottom_position = ((width - bottom_text_width) / 2, height - bottom_text_height - 10)
        
        # Add text with outline
        def draw_text_with_outline(text, position):
            x, y = position
            for offset in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                draw.text((x + offset[0], y + offset[1]), text, font=font, fill='black')
            draw.text((x, y), text, font=font, fill='white')
        
        draw_text_with_outline(top_text, top_position)
        draw_text_with_outline(bottom_text, bottom_position)
        
        # Save and clean up
        image.save(output_path)
        os.remove(temp_path)
        return output_path