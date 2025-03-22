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
from typing import Tuple, Optional, Dict, Any, List, Union
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
        
        # Store the last used prompts for debugging/display
        self.last_system_prompt = ""
        self.last_user_prompt = ""
    
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
    
    def generate_meme_text(self, context: str = "music", template_image_path: str = None, 
                           template_context: Dict[str, Any] = None, box_count: int = 2) -> Tuple[List[str], Dict[str, str]]:
        """
        Generate text blocks for a meme template using OpenAI.
        
        Args:
            context: The context to generate text for ("music", "band", "genre", etc.)
            template_image_path: URL or path to the template image
            template_context: Dictionary containing template metadata
            box_count: Number of text boxes to generate
            
        Returns:
            Tuple of (list of text strings, dict with prompts used)
        """
        if not self.client:
            logger.error("OpenAI client not initialized. Cannot generate text.")
            raise ValueError("OpenAI API key is not configured")
            
        # Prepare image data if available
        image_content = None
        if template_image_path:
            image_data = self._extract_image_data(template_image_path)
            if image_data:
                base64_image = base64.b64encode(image_data).decode('utf-8')
                image_content = {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        
        # Build context information from template metadata
        context_info = ""
        if template_context:
            if "name" in template_context:
                context_info += f"Meme name: {template_context['name']}\n"
            if "description" in template_context:
                context_info += f"Description: {template_context['description']}\n"
            if "format" in template_context:
                context_info += f"Format: {template_context['format']}\n"
            if "tone" in template_context:
                context_info += f"Tone: {template_context['tone']}\n"
        
        # Build the system prompt
        system_prompt = f"""
        You are a witty meme text generator specialized in {context} humor.
        
        Your task is to generate text for a meme with {box_count} text areas.
        The text should be concise, punchy, and funny, following meme conventions.
        
        Template information:
        {context_info}
        
        Important guidelines:
        - Create text appropriate for each of the {box_count} text areas in the template
        - Make sure the text reflects the proper usage of this specific meme format
        - Include {context}-related humor and references where appropriate
        - Each text block should be concise (typically 5-15 words max)
        - DO NOT include any emojis or special characters
        - DO NOT number or label the text blocks
        
        Respond with a JSON array containing exactly {box_count} text strings, one for each text area.
        """
        
        # Store the system prompt for later reference
        self.last_system_prompt = system_prompt
        
        user_prompt = f"Generate {box_count} text blocks for this meme template related to {context}."
        # Store the user prompt for later reference
        self.last_user_prompt = user_prompt
        
        try:
            # Prepare the messages
            messages = [{"role": "system", "content": system_prompt}]
            
            user_content = [{"type": "text", "text": user_prompt}]
            
            # Add image if available
            if image_content:
                user_content.append(image_content)
                
            messages.append({"role": "user", "content": user_content})
            
            # Make the API call
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            logger.debug(f"OpenAI response for template texts: {content}")
            
            # Extract the text blocks
            try:
                result = json.loads(content)
                
                # Handle different response formats
                if isinstance(result, list):
                    text_blocks = result
                elif "texts" in result:
                    text_blocks = result["texts"]
                elif "text_blocks" in result:
                    text_blocks = result["text_blocks"]
                else:
                    # Try to find any array in the response
                    for key, value in result.items():
                        if isinstance(value, list) and len(value) == box_count:
                            text_blocks = value
                            break
                    else:
                        # Create default text blocks if none found
                        text_blocks = [f"Text block {i+1}" for i in range(box_count)]
                
                # Ensure we have exactly the right number of blocks
                while len(text_blocks) < box_count:
                    text_blocks.append(f"Text area {len(text_blocks)+1}")
                
                # Clean up the text blocks (remove emojis and limit to first box_count elements)
                cleaned_blocks = [self._remove_emojis(block) for block in text_blocks[:box_count]]
                
                logger.info(f"Generated {len(cleaned_blocks)} text blocks for template")
                
                # Return both the text blocks and the prompts used
                return cleaned_blocks, {
                    "system_prompt": self.last_system_prompt,
                    "user_prompt": self.last_user_prompt
                }
                
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.error(f"Error parsing template text response: {e}")
                # Fallback to simple extraction
                lines = content.strip().split('\n')
                text_blocks = []
                for line in lines:
                    # Try to extract text content
                    text = re.sub(r'^[0-9]+[\.\)]*\s*', '', line).strip('" ')
                    if text:
                        text_blocks.append(self._remove_emojis(text))
                
                # Ensure correct number of text blocks
                while len(text_blocks) < box_count:
                    text_blocks.append(f"Text area {len(text_blocks)+1}")
                
                # Return both the text blocks and the prompts used
                return text_blocks[:box_count], {
                    "system_prompt": self.last_system_prompt,
                    "user_prompt": self.last_user_prompt
                }
                
        except Exception as e:
            logger.error(f"Error generating template text with OpenAI: {str(e)}")
            # Return default text blocks
            return [f"Text area {i+1}" for i in range(box_count)], {
                "system_prompt": self.last_system_prompt,
                "user_prompt": self.last_user_prompt,
                "error": str(e)
            }
    
    def generate_band_meme_text(self, band_name: str, image_path: str = None, 
                          context: Optional[Dict[str, Any]] = None, box_count: int = 2,
                          template_image_path: str = None) -> Tuple[List[str], Dict[str, str]]:
        """
        Generate band-themed meme text using OpenAI.
        
        Args:
            band_name: Name of the band to reference in the meme
            image_path: Path to the image file or URL (if provided, will analyze the image)
            context: Optional context about the meme or template metadata
            box_count: Number of text boxes to generate
            template_image_path: Path to template image (alternative to image_path for templates)
            
        Returns:
            Tuple of (list of text strings, dict with prompts used)
        """
        if not self.client:
            logger.error("OpenAI client not initialized. Cannot generate text.")
            raise ValueError("OpenAI API key is not configured")
        
        # Use template_image_path if provided, otherwise use image_path
        image_to_analyze = template_image_path or image_path
        
        # If we only have 2 boxes and no specific template, use the traditional top/bottom approach
        if box_count == 2 and (not context or not isinstance(context, dict)):
            top_text, bottom_text, prompts = self._generate_traditional_band_meme_text(band_name, image_to_analyze, context)
            return [top_text, bottom_text], prompts
        
        # Prepare image data if available
        image_content = None
        if image_to_analyze:
            image_data = self._extract_image_data(image_to_analyze)
            if image_data:
                base64_image = base64.b64encode(image_data).decode('utf-8')
                image_content = {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        
        # Build context information from template metadata
        context_info = ""
        if context and isinstance(context, dict):
            if "name" in context:
                context_info += f"Meme name: {context['name']}\n"
            if "description" in context:
                context_info += f"Description: {context['description']}\n"
            if "format" in context:
                context_info += f"Format: {context['format']}\n"
            if "tone" in context:
                context_info += f"Tone: {context['tone']}\n"
        
        # Build the system prompt
        system_prompt = f"""
        You are a music meme generator specialized in creating music and band humor. 
        Your task is to create funny text for a meme about the band "{band_name}".
        This meme requires {box_count} separate text areas.
        
        Template information:
        {context_info}
        
        The humor should reference their music style, famous songs, band members, or iconic moments.
        
        VERY IMPORTANT:
        - Create text appropriate for each of the {box_count} text areas in the template
        - Focus PRIMARILY on what can be seen in the image itself
        - Create meme text that directly relates to the visual elements in the image AND connects them to {band_name}
        - Make specific references to things visible in the image and connect them to the band
        - Be creative, clever, and make sure the joke would be understood by fans of {band_name}
        - Each text block should be concise (typically 5-15 words max)
        - DO NOT include any emojis or special characters
        - DO NOT number or label the text blocks
        
        Return a JSON object with a "texts" field containing an array of exactly {box_count} text strings:
        {{"texts": ["First text area content", "Second text area content", ...]}}
        """
        
        # Store the system prompt for later reference
        self.last_system_prompt = system_prompt
        
        user_prompt = f"Generate {box_count} text blocks for this meme template about the band {band_name}."
        # Store the user prompt for later reference
        self.last_user_prompt = user_prompt
        
        try:
            # Prepare the messages
            messages = [{"role": "system", "content": system_prompt}]
            
            user_content = [{"type": "text", "text": user_prompt}]
            
            # Add image if available
            if image_content:
                user_content.append(image_content)
                
            messages.append({"role": "user", "content": user_content})
            
            # Make the API call
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            logger.debug(f"OpenAI response for band template texts: {content}")
            
            # Extract the text blocks
            try:
                if content:
                    result = json.loads(content)
                    
                    # Handle different response formats
                    if isinstance(result, list):
                        text_blocks = result
                    elif "texts" in result:
                        text_blocks = result["texts"]
                    elif "text_blocks" in result:
                        text_blocks = result["text_blocks"]
                    else:
                        # Try to find any array in the response
                        for key, value in result.items():
                            if isinstance(value, list) and len(value) > 0:
                                text_blocks = value
                                break
                        else:
                            # Create creative text blocks if none found
                            if band_name.lower() == "the doors":
                                text_blocks = [
                                    "Play 'Light My Fire' every gig",
                                    "Draw 25 cards"
                                ]
                            else:
                                text_blocks = [f"Something witty about {band_name}", f"Something clever about {band_name}'s music"]
                else:
                    # Content is empty or None, create fallback text
                    if band_name.lower() == "the doors":
                        text_blocks = [
                            "Play 'Light My Fire' every gig",
                            "Draw 25 cards"
                        ]
                    else:
                        text_blocks = [f"Something witty about {band_name}", f"Something clever about {band_name}'s music"]
                
                # Ensure we have exactly the right number of blocks
                while len(text_blocks) < box_count:
                    if band_name.lower() == "the doors":
                        text_blocks.append(f"Break on through to the other side")
                    else:
                        text_blocks.append(f"More {band_name} humor goes here")
                
                # Clean up the text blocks (remove emojis and limit to first box_count elements)
                cleaned_blocks = [self._remove_emojis(block) for block in text_blocks[:box_count]]
                
                logger.info(f"Generated {len(cleaned_blocks)} text blocks for band template")
                
                # Return both the text blocks and the prompts used
                return cleaned_blocks, {
                    "system_prompt": self.last_system_prompt,
                    "user_prompt": self.last_user_prompt
                }
                
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.error(f"Error parsing band template text response: {e}")
                # Fallback to creative examples for common bands
                if band_name.lower() == "the doors":
                    text_blocks = [
                        "Play 'Light My Fire' every gig",
                        "Draw 25 cards"
                    ]
                elif band_name.lower() == "pink floyd":
                    text_blocks = [
                        "Skip Dark Side of the Moon",
                        "Draw 25 cards"
                    ]
                elif band_name.lower() == "metallica":
                    text_blocks = [
                        "Listen to Load and ReLoad",
                        "Draw 25 cards"
                    ]
                else:
                    # Fallback to generic but still somewhat creative texts
                    text_blocks = [
                        f"{band_name}'s greatest hit",
                        f"Their worst song ever"
                    ]
                
                # Return both the text blocks and the prompts used
                return text_blocks[:box_count], {
                    "system_prompt": self.last_system_prompt,
                    "user_prompt": self.last_user_prompt
                }
                
        except Exception as e:
            logger.error(f"Error generating band template text with OpenAI: {str(e)}")
            # Return creative fallback text blocks instead of placeholders
            if band_name.lower() == "the doors":
                text_blocks = [
                    "Play 'Light My Fire' every gig",
                    "Draw 25 cards"
                ]
            elif "beatles" in band_name.lower():
                text_blocks = [
                    "Say Ringo is your favorite Beatle",
                    "Draw 25 cards"
                ]
            elif "queen" in band_name.lower():
                text_blocks = [
                    "Skip Bohemian Rhapsody",
                    "Draw 25 cards"
                ]
            else:
                text_blocks = [
                    f"Not listen to {band_name}",
                    "Draw 25 cards"
                ]
            
            return text_blocks[:box_count], {
                "system_prompt": self.last_system_prompt,
                "user_prompt": self.last_user_prompt,
                "error": str(e)
            }
    
    def _generate_traditional_band_meme_text(self, band_name: str, image_path: str = None, 
                                           context: Optional[Union[str, Dict[str, Any]]] = None) -> Tuple[str, str, Dict[str, str]]:
        """
        Generate traditional top/bottom text for a band meme (legacy method).
        
        Args:
            band_name: Name of the band to reference in the meme
            image_path: Path to the image file or URL (if provided, will analyze the image)
            context: Optional context about the meme or image
            
        Returns:
            Tuple containing (top text, bottom text, prompts used)
        """
        # Extract context string if it's a dictionary
        context_str = ""
        if isinstance(context, dict):
            context_parts = []
            for key, value in context.items():
                if isinstance(value, str) and key != 'analyzed':
                    context_parts.append(f"{key}: {value}")
            context_str = ". ".join(context_parts)
        elif isinstance(context, str):
            context_str = context
            
        # Extract image data or download it if it's a URL
        image_data = None
        if image_path:
            image_data = self._extract_image_data(image_path)
            
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
        
        user_prompt = f"Generate funny top and bottom text for this meme about {band_name}."
        if context_str:
            user_prompt += f" Additional context: {context_str}"
            
        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            if image_data:
                base64_image = base64.b64encode(image_data).decode('utf-8')
                messages.append({
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
                })
            else:
                messages.append({"role": "user", "content": user_prompt})
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            logger.debug(f"OpenAI response: {content}")
            
            try:
                result = json.loads(content)
                top_text = self._remove_emojis(result.get("top_text", ""))
                bottom_text = self._remove_emojis(result.get("bottom_text", ""))
                return top_text, bottom_text, {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt
                }
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from OpenAI response: {content}")
                # Fallback to simple text extraction
                lines = content.strip().split('\n')
                top_text = self._remove_emojis(lines[0] if lines else "")
                bottom_text = self._remove_emojis(lines[-1] if len(lines) > 1 else "")
                return top_text, bottom_text, {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt
                }
                
        except Exception as e:
            logger.error(f"Error generating band meme text with OpenAI: {str(e)}")
            raise

    def generate_genre_meme_text(self, genre: str, image_path: str = None, 
                                context: Optional[Dict[str, Any]] = None, box_count: int = 2,
                                template_image_path: str = None) -> Tuple[List[str], Dict[str, str]]:
        """
        Generate genre-specific meme text using OpenAI.
        
        Args:
            genre: Music genre to generate meme for (e.g., "60s rock", "jazz", "90s rock", "rave", "2010s pop")
            image_path: Path to the image file or URL (if provided, will analyze the image)
            context: Optional context about the meme or template metadata
            box_count: Number of text boxes to generate
            template_image_path: Path to template image (alternative to image_path for templates)
            
        Returns:
            Tuple of (list of text strings, dict with prompts used)
        """
        if not self.client:
            logger.error("OpenAI client not initialized. Cannot generate text.")
            raise ValueError("OpenAI API key is not configured")
        
        # Use template_image_path if provided, otherwise use image_path
        image_to_analyze = template_image_path or image_path
        
        # If we only have 2 boxes and no specific template, use the traditional top/bottom approach
        if box_count == 2 and (not context or not isinstance(context, dict)):
            top_text, bottom_text, prompts = self._generate_traditional_genre_meme_text(genre, image_to_analyze, context)
            return [top_text, bottom_text], prompts
        
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
        
        # Prepare image data if available
        image_content = None
        if image_to_analyze:
            image_data = self._extract_image_data(image_to_analyze)
            if image_data:
                base64_image = base64.b64encode(image_data).decode('utf-8')
                image_content = {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        
        # Build context information from template metadata
        context_info = ""
        if context and isinstance(context, dict):
            if "name" in context:
                context_info += f"Meme name: {context['name']}\n"
            if "description" in context:
                context_info += f"Description: {context['description']}\n"
            if "format" in context:
                context_info += f"Format: {context['format']}\n"
            if "tone" in context:
                context_info += f"Tone: {context['tone']}\n"
                
        # Build the system prompt
        system_prompt = f"""
        You are a {template["personality"]} meme creator who specializes in {genre} music humor.
        Your tone is {template["tone"]} and you often reference {template["references"]}.
        Your writing style {template["style"]}.
        
        Your task is to create FUNNY and CREATIVE text for a meme with {box_count} text areas about {genre} music.
        
        Template information:
        {context_info}
        
        The humor should be specific to the culture, fans, and stereotypes of {genre} music, making
        references that true fans would appreciate.
        
        VERY IMPORTANT:
        - Create text appropriate for each of the {box_count} text areas in the template
        - Focus ONLY on what can be seen in the image itself, not any titles or descriptions that might have come with it
        - Create meme text that directly relates to the visual elements in the image
        - Make specific references to things visible in the image and connect them to {genre} music culture
        - Each text block should be concise (typically 5-15 words max)
        - DO NOT include any emojis or special characters
        - DO NOT number or label the text blocks
        
        Make sure the meme text:
        1. Is concise and punchy (typical meme format)
        2. Contains humor that specifically resonates with {genre} fans
        3. References genre-specific tropes, artists, or cultural moments
        4. Has the specific voice and style of a {genre} fan or artist
        
        Respond with a JSON array containing exactly {box_count} text strings, one for each text area.
        """
        
        # Store the system prompt for later reference
        self.last_system_prompt = system_prompt
        
        user_prompt = f"Generate {box_count} text blocks for this meme template about {genre} music."
        # Store the user prompt for later reference
        self.last_user_prompt = user_prompt
        
        try:
            # Prepare the messages
            messages = [{"role": "system", "content": system_prompt}]
            
            user_content = [{"type": "text", "text": user_prompt}]
            
            # Add image if available
            if image_content:
                user_content.append(image_content)
                
            messages.append({"role": "user", "content": user_content})
            
            # Make the API call
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            logger.debug(f"OpenAI response for genre template texts: {content}")
            
            # Extract the text blocks
            try:
                result = json.loads(content)
                
                # Handle different response formats
                if isinstance(result, list):
                    text_blocks = result
                elif "texts" in result:
                    text_blocks = result["texts"]
                elif "text_blocks" in result:
                    text_blocks = result["text_blocks"]
                else:
                    # Try to find any array in the response
                    for key, value in result.items():
                        if isinstance(value, list) and len(value) == box_count:
                            text_blocks = value
                            break
                    else:
                        # Create default text blocks if none found
                        text_blocks = [f"Text block {i+1} about {genre}" for i in range(box_count)]
                
                # Ensure we have exactly the right number of blocks
                while len(text_blocks) < box_count:
                    text_blocks.append(f"Text block {len(text_blocks)+1} about {genre}")
                
                # Clean up the text blocks (remove emojis and limit to first box_count elements)
                cleaned_blocks = [self._remove_emojis(block) for block in text_blocks[:box_count]]
                
                logger.info(f"Generated {len(cleaned_blocks)} text blocks for genre template")
                
                # Return both the text blocks and the prompts used
                return cleaned_blocks, {
                    "system_prompt": self.last_system_prompt,
                    "user_prompt": self.last_user_prompt
                }
                
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.error(f"Error parsing genre template text response: {e}")
                # Fallback to simple extraction
                lines = content.strip().split('\n')
                text_blocks = []
                for line in lines:
                    # Try to extract text content
                    text = re.sub(r'^[0-9]+[\.\)]*\s*', '', line).strip('" ')
                    if text:
                        text_blocks.append(self._remove_emojis(text))
                
                # Ensure correct number of text blocks
                while len(text_blocks) < box_count:
                    text_blocks.append(f"Text block {len(text_blocks)+1} about {genre}")
                
                # Return both the text blocks and the prompts used
                return text_blocks[:box_count], {
                    "system_prompt": self.last_system_prompt,
                    "user_prompt": self.last_user_prompt
                }
                
        except Exception as e:
            logger.error(f"Error generating genre template text with OpenAI: {str(e)}")
            # Return default text blocks
            return [f"{genre} meme text {i+1}" for i in range(box_count)], {
                "system_prompt": self.last_system_prompt,
                "user_prompt": self.last_user_prompt,
                "error": str(e)
            }
    
    def _generate_traditional_genre_meme_text(self, genre: str, image_path: str = None, 
                                            context: Optional[Union[str, Dict[str, Any]]] = None) -> Tuple[str, str, Dict[str, str]]:
        """
        Generate traditional top/bottom text for a genre meme (legacy method).
        
        Args:
            genre: Music genre to reference in the meme
            image_path: Path to the image file or URL (if provided, will analyze the image)
            context: Optional context about the meme or image
            
        Returns:
            Tuple containing (top text, bottom text, prompts used)
        """
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
        
        # Extract context string if it's a dictionary
        context_str = ""
        if isinstance(context, dict):
            context_parts = []
            for key, value in context.items():
                if isinstance(value, str) and key != 'analyzed':
                    context_parts.append(f"{key}: {value}")
            context_str = ". ".join(context_parts)
        elif isinstance(context, str):
            context_str = context
            
        # Extract image data or download it if it's a URL
        image_data = None
        if image_path:
            image_data = self._extract_image_data(image_path)
            
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
        4. Has the specific voice and style of a {genre} fan or artist
        
        Respond with JSON in the format:
        {{
            "top_text": "The top text for the meme",
            "bottom_text": "The bottom text for the meme"
        }}
        """
        
        user_prompt = f"Generate funny top and bottom text for this meme about {genre} music."
        if context_str:
            user_prompt += f" Additional context: {context_str}"
            
        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            if image_data:
                base64_image = base64.b64encode(image_data).decode('utf-8')
                messages.append({
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
                })
            else:
                messages.append({"role": "user", "content": user_prompt})
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            logger.debug(f"OpenAI response: {content}")
            
            try:
                result = json.loads(content)
                top_text = self._remove_emojis(result.get("top_text", ""))
                bottom_text = self._remove_emojis(result.get("bottom_text", ""))
                return top_text, bottom_text, {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt
                }
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from OpenAI response: {content}")
                # Fallback to simple text extraction
                lines = content.strip().split('\n')
                top_text = self._remove_emojis(lines[0] if lines else "")
                bottom_text = self._remove_emojis(lines[-1] if len(lines) > 1 else "")
                return top_text, bottom_text, {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt
                }
                
        except Exception as e:
            logger.error(f"Error generating genre meme text with OpenAI: {str(e)}")
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
        top_text, bottom_text, prompts = self.generate_band_meme_text(band_name, image_path, context)
        
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
        top_text, bottom_text, prompts = self.generate_genre_meme_text(genre, image_path, context)
        
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
            top_text, bottom_text, prompts = self.generate_meme_text(context="music", template_image_path=extracted_image_path)
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
    
    def analyze_meme_template(self, prompt: str) -> Tuple[str, str]:
        """
        Analyze a meme template to determine its metadata.
        
        Args:
            prompt: The prompt describing the template to analyze
            
        Returns:
            Tuple of (JSON string with template metadata, prompt used)
        """
        if not self.client:
            logger.error("OpenAI client not initialized. Cannot analyze template.")
            raise ValueError("OpenAI API key is not configured")
        
        # Store the template analysis prompt
        self.last_template_analysis_prompt = prompt
        
        try:
            # Make the API call to analyze the template
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a meme analysis expert. Your task is to provide detailed information about meme templates, their usage, and cultural context. Format your response as JSON with the specified fields."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Get the response content
            content = response.choices[0].message.content
            logger.debug(f"OpenAI response for template analysis: {content}")
            
            # Validate JSON structure before returning
            try:
                json_data = json.loads(content)
                # Ensure expected fields are present
                expected_fields = ["name", "description", "format", "example", "tone"]
                for field in expected_fields:
                    if field not in json_data:
                        json_data[field] = f"No {field} information available"
                        
                # Set analyzed flag to indicate this was processed
                json_data["analyzed"] = True
                
                # Add the prompt used
                json_data["analysis_prompt"] = prompt
                
                # Convert back to string
                return json.dumps(json_data), prompt
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from template analysis response: {content}")
                # Return a basic structure
                return json.dumps({
                    "name": "Unidentified Template",
                    "description": "A meme template with no available description.",
                    "format": "Standard meme format with text areas.",
                    "example": "Text appropriate for this meme format.",
                    "tone": "Humorous, internet meme culture.",
                    "analyzed": True,
                    "analysis_prompt": prompt
                }), prompt
                
        except Exception as e:
            logger.error(f"Error analyzing template with OpenAI: {str(e)}")
            # Return a minimal structure
            return json.dumps({
                "name": "Error Template",
                "description": "Error analyzing template.",
                "format": "Unknown format.",
                "example": "Error retrieving example.",
                "tone": "Unknown tone.",
                "analyzed": False,
                "analysis_prompt": prompt,
                "error": str(e)
            }), prompt
            
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
            top_text, bottom_text, prompts = self.generate_band_meme_text(band_name, temp_image_path, band_context)
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