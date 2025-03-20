"""
AI-powered meme generator module.

This module provides functionality to:
1. Extract images from existing memes
2. Generate new meme text using OpenAI
3. Create new memes with the extracted images and AI-generated text
"""
import os
import logging
import base64
import requests
from io import BytesIO
from typing import Tuple, Optional, Dict, Any
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AIMemeGenerator:
    """Class to handle AI-powered meme generation."""
    
    def __init__(self, api_key: Optional[str] = None, temp_dir: str = "temp_images"):
        """
        Initialize the AI meme generator.
        
        Args:
            api_key: OpenAI API key, defaults to environment variable
            temp_dir: Directory to save temporary images
        """
        # Create temp directory if it doesn't exist
        self.temp_dir = temp_dir
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        # Set up OpenAI client
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("No OpenAI API key provided. AI features will not work.")
        
        try:
            self.client = OpenAI(api_key=api_key)
            logger.info("AI meme generator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None
    
    def extract_image_from_meme(self, meme_path: str) -> Optional[str]:
        """
        Extract the base image from a meme by removing text.
        
        Args:
            meme_path: Path to the meme image
            
        Returns:
            Path to the extracted image or None if failed
        """
        try:
            # Load the image
            img = Image.open(meme_path)
            
            # For now, we'll just crop out the middle part of the image
            # In a more advanced implementation, we could use OCR to detect and remove text
            width, height = img.size
            
            # Crop out the top and bottom 15% where text is typically located
            crop_top = int(height * 0.15)
            crop_bottom = height - int(height * 0.15)
            
            # Crop the image to remove typical meme text areas
            cropped_img = img.crop((0, crop_top, width, crop_bottom))
            
            # Create a new blank image with the original dimensions
            new_img = Image.new("RGB", (width, height), (255, 255, 255))
            
            # Paste the cropped image into the center
            new_img.paste(cropped_img, (0, crop_top))
            
            # Save the processed image
            output_path = os.path.join(self.temp_dir, f"extracted_{os.path.basename(meme_path)}")
            new_img.save(output_path)
            
            logger.info(f"Extracted image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error extracting image from meme: {e}")
            return None
    
    def generate_meme_text(self, image_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate meme text using OpenAI's vision capabilities.
        
        Args:
            image_path: Path to the image to generate text for
            
        Returns:
            Tuple of (top_text, bottom_text) or (None, None) if failed
        """
        if not self.client:
            logger.error("OpenAI client not initialized. Cannot generate text.")
            return None, None
        
        try:
            # Encode image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a humorous meme caption generator. Given an image, create a funny meme with a top text and bottom text. Be witty and relevant to the image content. Return ONLY the text in the format 'TOP TEXT: [your text here]\nBOTTOM TEXT: [your text here]'"
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Create a funny meme caption for this image."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=100
            )
            
            # Extract the generated text
            generated_text = response.choices[0].message.content
            logger.info(f"Generated text: {generated_text}")
            
            # Parse the top and bottom text
            top_text = ""
            bottom_text = ""
            
            # Simple parsing, assumes format "TOP TEXT: ... BOTTOM TEXT: ..."
            lines = generated_text.strip().split('\n')
            for line in lines:
                if line.startswith("TOP TEXT:"):
                    top_text = line.replace("TOP TEXT:", "").strip()
                elif line.startswith("BOTTOM TEXT:"):
                    bottom_text = line.replace("BOTTOM TEXT:", "").strip()
            
            return top_text, bottom_text
            
        except Exception as e:
            logger.error(f"Error generating meme text: {e}")
            return None, None
    
    def regenerate_meme(self, original_meme_path: str, image_editor) -> Optional[str]:
        """
        Regenerate a meme using AI.
        
        Args:
            original_meme_path: Path to the original meme
            image_editor: MemeEditor instance to create the new meme
            
        Returns:
            Path to the regenerated meme or None if failed
        """
        try:
            # Extract the image from the meme
            extracted_image_path = self.extract_image_from_meme(original_meme_path)
            if not extracted_image_path:
                return None
            
            # Generate new meme text
            top_text, bottom_text = self.generate_meme_text(extracted_image_path)
            if not top_text and not bottom_text:
                return None
            
            # Generate a new meme with the extracted image and generated text
            output_filename = f"ai_meme_{os.path.basename(original_meme_path)}"
            
            # Use the existing image editor to create the new meme
            new_meme_path = image_editor.generate_meme(
                image_path=extracted_image_path,  # Use the local path instead of URL
                top_text=top_text,
                bottom_text=bottom_text,
                output_filename=output_filename,
                use_local_image=True  # Flag to indicate this is a local file
            )
            
            logger.info(f"AI-generated meme saved to: {new_meme_path}")
            return new_meme_path
            
        except Exception as e:
            logger.error(f"Error regenerating meme: {e}")
            return None 