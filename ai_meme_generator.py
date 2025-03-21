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
import re
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
    
    def _extract_image_data(self, image_path: str) -> bytes:
        """
        Extract image data from a file path or URL.
        
        Args:
            image_path: Path to the image file or URL
            
        Returns:
            Image data as bytes
        """
        try:
            if image_path.startswith(('http://', 'https://')):
                # It's a URL, download the image
                response = requests.get(image_path, timeout=10)
                response.raise_for_status()
                return response.content
            else:
                # It's a local file, read it
                with open(image_path, 'rb') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error extracting image data: {str(e)}")
            raise
    
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
    
    def _remove_emojis(self, text: str) -> str:
        """
        Remove emojis and other non-standard characters from text.
        
        Args:
            text: The text to process
            
        Returns:
            Text with emojis removed
        """
        # This pattern catches most common emojis and special characters
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F700-\U0001F77F"  # alchemical symbols
            "\U0001F780-\U0001F7FF"  # Geometric Shapes
            "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U0001FA00-\U0001FA6F"  # Chess Symbols
            "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            "\U00002702-\U000027B0"  # Dingbats
            "\U000024C2-\U0001F251" 
            "]+", flags=re.UNICODE
        )
        
        # Replace emojis with empty string
        return emoji_pattern.sub(r'', text)
    
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
        
        VERY IMPORTANT:
        - Focus ONLY on what can be seen in the image itself, not any titles or descriptions that might have come with it
        - Create meme text that directly relates to the visual elements in the image
        - The viewer of the meme will ONLY see the image, not any Reddit post titles or descriptions
        - Make specific references to things visible in the image
        - Keep it punchy and memorable - meme text should be concise
        - DO NOT include any emojis or special characters in the text, as they cause rendering issues
        - Stick to plain text only with standard punctuation
        
        Respond with JSON in the format:
        {
            "top_text": "The top text for the meme",
            "bottom_text": "The bottom text for the meme"
        }
        """
        
        user_prompt = "Generate funny top and bottom text for this meme image."
        if context:
            user_prompt += f" This is what the image shows: {context}"
            
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
                top_text = self._remove_emojis(result.get("top_text", ""))
                bottom_text = self._remove_emojis(result.get("bottom_text", ""))
                return top_text, bottom_text
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from OpenAI response: {content}")
                # Fallback to simple text extraction
                lines = content.strip().split('\n')
                top_text = self._remove_emojis(lines[0] if lines else "")
                bottom_text = self._remove_emojis(lines[-1] if len(lines) > 1 else "")
                return top_text, bottom_text
                
        except Exception as e:
            logger.error(f"Error generating meme text with OpenAI: {str(e)}")
            raise
    
    def generate_band_meme_text(self, band_name: str, image_path: str = None, context: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate band-themed meme text using OpenAI.
        
        Args:
            band_name: Name of the band to reference in the meme
            image_path: Path to the image file or URL (if provided, will analyze the image)
            context: Optional context about the meme or image
            
        Returns:
            Tuple containing top and bottom text for the band-themed meme
        """
        if not self.client:
            logger.error("OpenAI client not initialized. Cannot generate text.")
            raise ValueError("OpenAI API key is not configured")
        
        # Build the prompt
        system_prompt = f"""
        You are a music meme generator specialized in creating music and band humor. 
        Your task is to create funny top and bottom text for a meme about the band "{band_name}".
        These memes need to make sense within the context of the image, also it needs to be funny and make sense.
        The humor should reference their music style, famous songs, band members, or iconic moments.
        
        VERY IMPORTANT:
        - Focus PRIMARILY on what can be seen in the image itself, not any titles or descriptions that might have come with it
        - Create meme text that directly relates to the visual elements in the image AND connects them to {band_name}
        - The viewer of the meme will ONLY see the image, not any Reddit post titles or descriptions
        - Make specific references to things visible in the image and connect them to the band
        - DO NOT include any emojis or special characters in the text, as they cause rendering issues
        - Stick to plain text only with standard punctuation
        
        Be creative, clever, and make sure the joke would be understood by fans of {band_name}.
        Your captions should clearly reference BOTH what's in the image AND something about {band_name}.
        
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
            # If image path is provided, include the image in the prompt
            if image_path:
                try:
                    # Extract image data
                    image_data = self._extract_image_data(image_path)
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                    
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
                except Exception as e:
                    logger.error(f"Error processing image for band meme: {str(e)}")
                    # Fall back to text-only prompt
                    response = self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        response_format={"type": "json_object"}
                    )
            else:
                # Text-only prompt if no image is provided
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
                top_text = self._remove_emojis(result.get("top_text", ""))
                bottom_text = self._remove_emojis(result.get("bottom_text", ""))
                return top_text, bottom_text
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from OpenAI response: {content}")
                # Fallback to simple text extraction
                lines = content.strip().split('\n')
                top_text = self._remove_emojis(lines[0] if lines else "")
                bottom_text = self._remove_emojis(lines[-1] if len(lines) > 1 else "")
                return top_text, bottom_text
                
        except Exception as e:
            logger.error(f"Error generating band meme text with OpenAI: {str(e)}")
            raise
    
    def generate_genre_meme_text(self, genre: str, image_path: str = None, context: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate genre-specific meme text using OpenAI.
        
        Args:
            genre: Music genre to generate meme for (e.g., "60s rock", "jazz", "90s rock", "rave", "2010s pop")
            image_path: Path to the image file or URL (if provided, will analyze the image)
            context: Optional context about the meme or image
            
        Returns:
            Tuple containing top and bottom text for the genre-themed meme
        """
        if not self.client:
            logger.error("OpenAI client not initialized. Cannot generate text.")
            raise ValueError("OpenAI API key is not configured")
        
        # Define genre-specific personalities and characteristics
        genre_templates = {
            "60s rock": {
                "personality": "nostalgic Baby Boomer",
                "tone": "peace and love but secretly judgmental",
                "references": "Woodstock, The Beatles, Rolling Stones, Jimi Hendrix, psychedelic experiences, Vietnam War",
                "style": "uses phrases like 'back in my day' and complains about modern music"
            },
            "jazz": {
                "personality": "pretentious jazz aficionado",
                "tone": "intellectually superior and deliberately obscure",
                "references": "bebop, Miles Davis, John Coltrane, chord progressions, improvisational tangents",
                "style": "uses unnecessarily complex musical terminology and scoffs at mainstream listeners"
            },
            "90s rock": {
                "personality": "cynical Gen-X slacker",
                "tone": "ironic, disaffected, nihilistic",
                "references": "grunge, Nirvana, Pearl Jam, flannel shirts, MTV, existential crisis",
                "style": "uses sarcasm heavily, makes references to selling out and corporate music"
            },
            "rave": {
                "personality": "sleep-deprived raver who's seen things",
                "tone": "manic enthusiasm with bizarre tangents",
                "references": "PLUR, glow sticks, DJ culture, questionable substances, warehouse parties, electronic music genres",
                "style": "excessive use of ALL CAPS, repetition, and onomatopoeic UNTZ UNTZ UNTZ sounds"
            },
            "2010s pop": {
                "personality": "extremely online social media addict",
                "tone": "highly dramatic with stan culture vibes",
                "references": "Taylor Swift, Instagram aesthetics, TikTok dances, cancel culture, streaming stats",
                "style": "uses Gen Z slang and keyboard smashing"
            }
        }
        
        # Get the template for the selected genre (default to a generic one if not found)
        template = genre_templates.get(genre.lower(), {
            "personality": "music expert",
            "tone": "humorous and slightly pretentious",
            "references": "iconic artists, songs, and cultural moments",
            "style": "uses genre-appropriate slang and references"
        })
        
        # Build the prompt
        system_prompt = f"""
        You are a {template["personality"]} meme creator who specializes in {genre} music humor.
        Your tone is {template["tone"]} and you often reference {template["references"]}.
        Your writing style {template["style"]}.
        
        Your task is to create FUNNY and CREATIVE top and bottom text for a meme about {genre} music.
        The humor should be specific to the culture, fans, and stereotypes of {genre} music, making
        references that true fans would appreciate.
        
        VERY IMPORTANT:
        - Focus ONLY on what can be seen in the image itself, not any titles or descriptions that might have come with it
        - Create meme text that directly relates to the visual elements in the image
        - The viewer of the meme will ONLY see the image, not any Reddit post titles or descriptions
        - Make specific references to things visible in the image and connect them to {genre} music culture
        - DO NOT include any emojis or special characters in the text, as they cause rendering issues
        - Stick to plain text only with standard punctuation
        
        Make sure the meme text:
        1. Is concise and punchy (typical meme format)
        2. Contains humor that specifically resonates with {genre} fans
        3. References genre-specific tropes, artists, or cultural moments
        4. Has the specific voice and style of a {genre} fan or critic
        5. Directly relates to what is visible in the image
        
        Respond with JSON in the format:
        {{
            "top_text": "The top text for the meme",
            "bottom_text": "The bottom text for the meme"
        }}
        """
        
        user_prompt = f"Generate funny top and bottom text for a meme about {genre} music culture."
        if context:
            user_prompt += f" Additional context: {context}"
        
        # If image path is provided, include the image in the prompt
        if image_path:
            try:
                # Extract image data
                image_data = self._extract_image_data(image_path)
                base64_image = base64.b64encode(image_data).decode('utf-8')
                
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
            except Exception as e:
                logger.error(f"Error processing image for genre meme: {str(e)}")
                # Fall back to text-only prompt
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"}
                )
        else:
            # Text-only prompt
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
        logger.debug(f"OpenAI response for genre meme: {content}")
        
        try:
            result = json.loads(content)
            top_text = self._remove_emojis(result.get("top_text", ""))
            bottom_text = self._remove_emojis(result.get("bottom_text", ""))
            return top_text, bottom_text
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from OpenAI response: {content}")
            # Fallback to simple text extraction
            lines = content.strip().split('\n')
            top_text = self._remove_emojis(lines[0] if lines else "")
            bottom_text = self._remove_emojis(lines[-1] if len(lines) > 1 else "")
            return top_text, bottom_text
    
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
        top_text, bottom_text = self.generate_band_meme_text(band_name, image_path, context)
        
        # Use the image editor to create the meme
        output_path = image_editor.generate_meme(
            image_path=image_path,
            top_text=top_text,
            bottom_text=bottom_text
        )
        
        return output_path
    
    def generate_genre_themed_meme(self, image_path: str, genre: str, 
                                image_editor, context: Optional[str] = None) -> str:
        """
        Generate a complete genre-themed meme from an image.
        
        Args:
            image_path: Path to the image file or URL
            genre: Music genre to use for the meme (e.g., "60s rock", "jazz")
            image_editor: ImageEditor instance to create the final meme
            context: Optional context about the meme or image
            
        Returns:
            Path to the generated meme image
        """
        # Generate genre-specific text
        top_text, bottom_text = self.generate_genre_meme_text(genre, image_path, context)
        
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
            top_text, bottom_text = self.generate_band_meme_text(band_name, temp_image_path, band_context)
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