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
import uuid
import json

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
    
    def is_api_key_configured(self) -> bool:
        """
        Check if the OpenAI API key is configured.
        
        Returns:
            bool: True if the API key is configured, False otherwise
        """
        return self.client is not None
    
    def set_api_key(self, api_key: str) -> bool:
        """
        Set or update the OpenAI API key.
        
        Args:
            api_key: The OpenAI API key
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI API key updated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to update OpenAI client with new API key: {e}")
            return False
    
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
    
    def generate_meme_text(self, image_path: str, context: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate meme text (top and bottom) for an image using OpenAI API.
        
        Args:
            image_path: Path to the image file or URL
            context: Optional context about the meme or image
            
        Returns:
            Tuple containing top and bottom text for the meme
        """
        if not self.client:
            logger.error("OpenAI client not initialized. Cannot generate text.")
            raise ValueError("OpenAI API key is not configured")
            
        # Extract image data or download it if it's a URL
        image_data = self._extract_image_data(image_path)
        
        # Prepare the payload for OpenAI API
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Build the prompt
        system_prompt = """
        You are a witty meme generator. Your task is to create humorous top and bottom text for a meme image.
        Be creative, clever, and funny. The text should be concise and fit the meme format.
        Respond with JSON in the format:
        {
            "top_text": "The top text for the meme",
            "bottom_text": "The bottom text for the meme"
        }
        """
        
        user_prompt = "Generate funny top and bottom text for this meme image."
        if context:
            user_prompt += f" Context: {context}"
            
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            logger.debug(f"OpenAI response: {content}")
            
            try:
                result = json.loads(content)
                top_text = result.get("top_text", "")
                bottom_text = result.get("bottom_text", "")
                return top_text, bottom_text
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from OpenAI response: {content}")
                # Fallback to simple text extraction
                lines = content.strip().split('\n')
                top_text = lines[0] if lines else ""
                bottom_text = lines[-1] if len(lines) > 1 else ""
                return top_text, bottom_text
                
        except Exception as e:
            logger.error(f"Error generating meme text with OpenAI: {str(e)}")
            raise
    
    def generate_band_meme_text(self, band_name: str, context: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate band-themed meme text using OpenAI.
        
        Args:
            band_name: Name of the band to reference in the meme
            context: Optional context about the meme or image
            
        Returns:
            Tuple containing top and bottom text for the band-themed meme
        """
        if not self.client:
            logger.error("OpenAI client not initialized. Cannot generate text.")
            raise ValueError("OpenAI API key is not configured")
        
        # Build the prompt
        system_prompt = f"""
        You are a asshole meme generator specialized in creating music and band humor like a polically incorrect out of touch 50 year old white man. 
        Your task is to create funny top and bottom text for a meme about the band "{band_name}".
        These memes need to make sense within the context of the image, also it needs to be funny and make sense.The humor should reference their music style, famous songs, band members, or iconic moments, particularly moments that may be controversial or offensive.
        Be creative, clever, and make sure the joke would be understood by fans of {band_name}.
        
        Respond with JSON in the format:
        {{
            "top_text": "The top text for the meme",
            "bottom_text": "The bottom text for the meme"
        }}
        """
        
        user_prompt = f"Generate funny top and bottom text for a meme about {band_name}."
        if context:
            user_prompt += f" The meme image shows: {context}"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            logger.debug(f"OpenAI response for band meme: {content}")
            
            try:
                result = json.loads(content)
                top_text = result.get("top_text", "")
                bottom_text = result.get("bottom_text", "")
                return top_text, bottom_text
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from OpenAI response: {content}")
                # Fallback to simple text extraction
                lines = content.strip().split('\n')
                top_text = lines[0] if lines else ""
                bottom_text = lines[-1] if len(lines) > 1 else ""
                return top_text, bottom_text
                
        except Exception as e:
            logger.error(f"Error generating band meme text with OpenAI: {str(e)}")
            raise
    
    def generate_band_themed_meme(self, image_path: str, band_name: str, 
                                image_editor, context: Optional[str] = None) -> str:
        """
        Generate a complete band-themed meme from an image.
        
        Args:
            image_path: Path to the image file or URL
            band_name: Name of the band to reference in the meme
            image_editor: ImageEditor instance to create the final meme
            context: Optional context about the meme or image
            
        Returns:
            Path to the generated meme image
        """
        # Generate band-themed text
        top_text, bottom_text = self.generate_band_meme_text(band_name, context)
        
        # Use the image editor to create the meme
        output_path = image_editor.generate_meme(
            image_path=image_path,
            top_text=top_text,
            bottom_text=bottom_text
        )
        
        return output_path

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
            
    def generate_band_meme(self, image_url: str, band_name: str, band_context: str, image_editor) -> Optional[str]:
        """
        Generate a band-themed meme from a selected image.
        
        Args:
            image_url: URL of the image to use
            band_name: Name of the band to reference
            band_context: Additional context about the band
            image_editor: MemeEditor instance to create the meme
            
        Returns:
            Path to the generated band meme or None if failed
        """
        try:
            # First download the image
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Save to temp file
            temp_image_path = os.path.join(self.temp_dir, f"band_meme_source_{uuid.uuid4().hex[:8]}.jpg")
            with open(temp_image_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded image for band meme to: {temp_image_path}")
            
            # Generate band-specific meme text
            top_text, bottom_text = self.generate_band_meme_text(band_name, band_context)
            if not top_text and not bottom_text:
                logger.error("Failed to generate band meme text")
                return None
            
            # Generate the meme
            output_filename = f"band_meme_{band_name.replace(' ', '_').lower()}_{uuid.uuid4().hex[:8]}.jpg"
            
            # Use the image editor to create the meme
            new_meme_path = image_editor.generate_meme(
                image_path=temp_image_path,
                top_text=top_text,
                bottom_text=bottom_text,
                output_filename=output_filename,
                use_local_image=True
            )
            
            logger.info(f"Band meme for {band_name} saved to: {new_meme_path}")
            return new_meme_path
            
        except Exception as e:
            logger.error(f"Error generating band meme: {e}")
            return None 