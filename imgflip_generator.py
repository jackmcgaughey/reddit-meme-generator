"""
ImgFlip Generator Module

This module provides a wrapper to generate memes using the ImgFlip API.
It includes functionality for:
1. Fetching popular templates
2. Generating memes from templates
3. Managing template metadata and context analysis
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImgFlipGenerator:
    """
    A client for generating memes using the ImgFlip API.
    """
    
    def __init__(self, 
                 username: str = None, 
                 password: str = None, 
                 api_url: str = "https://api.imgflip.com",
                 cache_dir: str = "cache"):
        """
        Initialize the ImgFlip Generator.
        
        Args:
            username: ImgFlip username (optional)
            password: ImgFlip password (optional)
            api_url: ImgFlip API URL
            cache_dir: Directory for caching and metadata
        """
        self.username = username
        self.password = password
        self.api_url = api_url
        
        # Set up cache directory
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cache file paths
        self.templates_cache_path = os.path.join(self.cache_dir, "templates_cache.json")
        self.custom_metadata_path = os.path.join(self.cache_dir, "custom_template_metadata.json")
        
        # Load existing data
        self.templates_cache = self._load_templates_cache()
        self.custom_metadata = self._load_custom_metadata()
        
        # Define known template box mappings for common templates
        # These mappings override the default box ordering to ensure correct placement
        # Format: template_id: {UI box order: API box number}
        self.template_box_mappings = {
            # Two Buttons template - box 0 should be the top text, box 1 and 2 are the button labels
            "87743020": {
                0: 0,  # Top text about the character
                1: 2,  # First button label (bottom button)
                2: 1,  # Second button label (middle button)
            },
            # Drake Hotline Bling - standard order
            "181913649": {
                0: 0,  # Top panel text (rejected option)
                1: 1,  # Bottom panel text (preferred option)
            },
            # Distracted Boyfriend - text out of order
            "112126428": {
                0: 1,  # Boyfriend
                1: 0,  # Girlfriend
                2: 2,  # Other woman
            },
            # Expanding Brain - text from simple (top) to complex (bottom)
            "93895088": {
                0: 0,  # Smallest brain
                1: 1,  # Larger brain
                2: 2,  # Even larger brain
                3: 3,  # Cosmic brain
            },
            # UNO Draw 25 Cards - only one text box needed (for the action)
            "217743513": {
                0: 0,  # The action to avoid (left side)
            }
        }
        
        # Verify template metadata cache integrity
        repairs = self.verify_template_metadata_cache()
        if repairs > 0:
            logger.info(f"Fixed {repairs} template metadata mismatches during initialization")
        
    def set_credentials(self, username: str, password: str) -> None:
        """
        Set ImgFlip API credentials.
        
        Args:
            username: ImgFlip username
            password: ImgFlip password
        """
        self.username = username
        self.password = password
    
    def get_popular_templates(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get a list of popular meme templates from ImgFlip.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            List of template dictionaries with id, name, url, width, height, box_count
        """
        # Check if we have cached templates and they're not expired (< 24 hours old)
        cache_valid = False
        if not force_refresh and self.templates_cache:
            cache_time = self.templates_cache.get("timestamp", 0)
            # Cache is valid for 24 hours
            if time.time() - cache_time < 24 * 60 * 60:
                cache_valid = True
                logger.info(f"Using cached templates ({len(self.templates_cache['templates'])} items)")
                return self.templates_cache["templates"]
        
        if force_refresh or not cache_valid:
            try:
                # Fetch templates from ImgFlip API
                response = requests.get(f"{self.api_url}/get_memes")
                response.raise_for_status()
                data = response.json()
                
                if data["success"]:
                    templates = data["data"]["memes"]
                    
                    # Update cache
                    self.templates_cache = {
                        "timestamp": time.time(),
                        "templates": templates
                    }
                    self._save_templates_cache()
                    
                    logger.info(f"Fetched {len(templates)} templates from ImgFlip API")
                    return templates
                else:
                    logger.error("Failed to fetch templates from ImgFlip API")
                    # Return empty cache if it exists
                    return self.templates_cache.get("templates", [])
            except Exception as e:
                logger.error(f"Error fetching templates: {str(e)}")
                # Return empty cache if it exists
                return self.templates_cache.get("templates", [])
        
        return []
    
    def generate_from_template(self, 
                             template_id: str, 
                             texts: Union[Dict[str, str], List[str]], 
                             output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a meme from a template using the ImgFlip API.
        
        Args:
            template_id: The ImgFlip template ID
            texts: Dictionary of box indices to text, or a list of text strings
            output_path: Optional path to save the generated meme
            
        Returns:
            Dictionary with results, including success status, URL, and error message if applicable
        """
        # Validate credentials
        if not self.username or not self.password:
            logger.error("ImgFlip credentials not set")
            return {"success": False, "error_message": "ImgFlip username and password are required"}
            
        # Prepare API parameters
        params = {
            "template_id": template_id,
            "username": self.username,
            "password": self.password
        }
        
        # Apply template-specific box mappings if available
        if isinstance(texts, list) and template_id in self.template_box_mappings:
            # Create a new array with the correct mapping
            mapped_texts = [""] * len(texts)  # Initialize with empty strings
            mapping = self.template_box_mappings[template_id]
            
            for ui_box, api_box in mapping.items():
                if ui_box < len(texts):
                    # Get text from the UI position and assign it to the correct API position
                    text_content = texts[ui_box]
                    if api_box < len(mapped_texts):
                        mapped_texts[api_box] = text_content
            
            logger.info(f"Applied template-specific box mapping for template {template_id}")
            texts = mapped_texts
        
        # Process text inputs
        if isinstance(texts, list):
            # Handle list format by converting to box format
            for i, text in enumerate(texts):
                params[f"boxes[{i}][text]"] = text
        elif isinstance(texts, dict):
            # Handle dictionary format with explicit box indices
            for box_index, text in texts.items():
                params[f"boxes[{box_index}][text]"] = text
        else:
            logger.error("Invalid texts format. Must be a list or dictionary.")
            return {"success": False, "error_message": "Invalid texts format"}
        
        try:
            # Make the API request
            response = requests.post(f"{self.api_url}/caption_image", data=params)
            response.raise_for_status()
            data = response.json()
            
            if data["success"]:
                meme_url = data["data"]["url"]
                logger.info(f"Meme successfully generated at URL: {meme_url}")
                
                # Save the meme locally if output path is provided
                if output_path:
                    saved = self._save_image_from_url(meme_url, output_path)
                    if saved:
                        return {
                            "success": True, 
                            "url": meme_url, 
                            "local_path": output_path
                        }
                    else:
                        return {
                            "success": True, 
                            "url": meme_url, 
                            "local_path": None,
                            "warning": "Could not save meme locally"
                        }
                
                return {"success": True, "url": meme_url}
            else:
                error_message = data.get("error_message", "Unknown error")
                logger.error(f"ImgFlip API error: {error_message}")
                return {"success": False, "error_message": error_message}
                
        except requests.RequestException as e:
            logger.error(f"Error making request to ImgFlip API: {str(e)}")
            return {"success": False, "error_message": f"API request error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error generating meme: {str(e)}")
            return {"success": False, "error_message": f"Unexpected error: {str(e)}"}
    
    def get_template_metadata(self, template_id: str) -> Dict[str, Any]:
        """
        Get metadata for a specific template, including any custom analysis.
        
        Args:
            template_id: The template ID
            
        Returns:
            Dictionary of template metadata and analysis
        """
        result = {}
        
        # Check in custom metadata first
        if template_id in self.custom_metadata:
            result = self.custom_metadata[template_id]
            
        # Check in templates cache if not found in custom metadata
        if not result:
            for template in self.templates_cache.get("templates", []):
                if str(template["id"]) == str(template_id):
                    result = template
                    break
                    
        # If still empty, return a default dictionary
        if not result:
            result = {
                "name": f"Template {template_id}",
                "box_count": 2
            }
            
        # Override box_count with template_box_mappings if available
        if template_id in self.template_box_mappings:
            # Use the number of entries in the mapping to determine the box count
            mapping_box_count = len(self.template_box_mappings[template_id])
            result["box_count"] = mapping_box_count
            logger.debug(f"Overriding box count for template {template_id} to {mapping_box_count} based on template mapping")
            
        return result
        
    def save_template_metadata(self, template_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Save custom metadata for a template.
        
        Args:
            template_id: The template ID
            metadata: Dictionary of metadata to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify template ID matches the correct template
            template_in_cache = None
            for template in self.templates_cache.get("templates", []):
                if str(template["id"]) == str(template_id):
                    template_in_cache = template
                    break
                    
            if template_in_cache:
                # Ensure metadata name matches the template cache name to prevent mismatched templates
                if metadata.get("name") and template_in_cache.get("name") and metadata["name"] != template_in_cache["name"]:
                    logger.warning(f"Template name mismatch: expected '{template_in_cache['name']}' for ID {template_id}, but got '{metadata['name']}' in analysis")
                    
                    # Override the metadata name to match the template cache
                    metadata["name"] = template_in_cache["name"]
                    logger.info(f"Corrected template name to '{template_in_cache['name']}' for ID {template_id}")
                    
                # Add additional template data from cache for consistency
                if not metadata.get("url") and template_in_cache.get("url"):
                    metadata["url"] = template_in_cache["url"]
                if not metadata.get("box_count") and template_in_cache.get("box_count"):
                    metadata["box_count"] = template_in_cache["box_count"]
            
            # Update metadata
            self.custom_metadata[template_id] = metadata
            
            # Save to file
            with open(self.custom_metadata_path, 'w') as f:
                json.dump(self.custom_metadata, f, indent=2)
                
            logger.info(f"Saved custom metadata for template {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving custom metadata: {str(e)}")
            return False
            
    def is_template_analyzed(self, template_id: str) -> bool:
        """
        Check if a template has been analyzed for context and usage.
        
        Args:
            template_id: The template ID
            
        Returns:
            True if the template has been analyzed, False otherwise
        """
        metadata = self.get_template_metadata(template_id)
        return metadata.get("analyzed", False)
    
    def create_template_analysis_prompt(self, template_id: str, box_count: int, template_url: str) -> str:
        """
        Create a prompt for analyzing a meme template.
        
        Args:
            template_id: The template ID
            box_count: Number of text boxes in the template
            template_url: URL of the template image
            
        Returns:
            Prompt string for template analysis
        """
        # Get the template name from cache if available
        template_name = f"Template {template_id}"
        for template in self.templates_cache.get("templates", []):
            if str(template["id"]) == str(template_id):
                template_name = template["name"]
                break
        
        prompt = f"""
Analyze this specific meme template: "{template_name}" (ID: {template_id}, Box Count: {box_count})
URL: {template_url}

IMPORTANT: Your analysis must be for THIS EXACT TEMPLATE shown in the URL, not any other meme. Look carefully at the image.

For the "{template_name}" meme template:

1. Full Name: Verify this is indeed the "{template_name}" meme before proceeding
   - If this is not a "{template_name}" meme, please indicate that it appears to be something else

2. Description: Provide a detailed description focusing on:
   - The exact visual elements visible in the image (people, objects, scene, expressions)
   - The conventional meaning/usage of this specific template in internet meme culture
   - What makes this template instantly recognizable or unique

3. Format: Explain precisely how this template with {box_count} text boxes is conventionally used:
   - What specific content typically appears in each text area (be explicit about each box)
   - The exact position of each text box (top, bottom, left, right, middle, etc.)
   - The order in which text boxes are typically assigned in meme generators (Box 0, Box 1, etc.)
   - The relationship between the text areas (contrast, progression, cause-effect, etc.)
   - The specific format or pattern that makes this meme template effective
   - Whether each text area represents different perspectives, concepts, or time frames

4. Box Placement: For each box, specify:
   - EXACT position on the image (top-left, bottom-center, etc.)
   - What this specific box should be used for
   - If this is a multi-panel meme, which panel contains this box
   - The order in which users should fill these boxes when creating a meme

5. Example: Provide 2 authentic examples of text that would typically be used in this meme
   - Show exactly what text would go in each area
   - Use examples that follow the established convention for this specific meme
   - Explicitly indicate which text goes in which position (e.g., "Box 1 (top): text")

6. Tone: The emotional tone this meme is typically used with (humorous, ironic, sarcastic, etc.)
   - Explain any subtleties in how the tone works with this specific template

Your analysis must accurately reflect this specific template's actual usage in meme culture.
Format your response as a JSON structure with these keys: name, description, format, box_placement, example, tone
"""
        return prompt
    
    def search_templates(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for templates matching a query.
        
        Args:
            query: Search term to match against template names
            
        Returns:
            List of matching templates
        """
        templates = self.get_popular_templates()
        
        # Perform case-insensitive search on template names
        query = query.lower()
        results = [t for t in templates if query in t["name"].lower()]
        
        logger.info(f"Found {len(results)} templates matching query: '{query}'")
        return results
    
    def filter_templates_by_box_count(self, box_count: int) -> List[Dict[str, Any]]:
        """
        Filter templates by number of text boxes.
        
        Args:
            box_count: Number of text boxes required
            
        Returns:
            List of matching templates
        """
        templates = self.get_popular_templates()
        results = [t for t in templates if t["box_count"] == box_count]
        
        logger.info(f"Found {len(results)} templates with {box_count} text boxes")
        return results
    
    def _save_image_from_url(self, url: str, output_path: str) -> bool:
        """
        Download and save an image from a URL.
        
        Args:
            url: URL of the image to download
            output_path: Path to save the image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Make the request to get the image
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Save the image
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logger.info(f"Image saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving image from URL: {str(e)}")
            return False
    
    def _load_templates_cache(self) -> Dict[str, Any]:
        """
        Load templates cache from file.
        
        Returns:
            Dictionary with templates and timestamp
        """
        try:
            if os.path.exists(self.templates_cache_path):
                with open(self.templates_cache_path, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data.get('templates', []))} templates from cache")
                    return data
        except Exception as e:
            logger.error(f"Error loading templates cache: {str(e)}")
        
        return {"timestamp": 0, "templates": []}
    
    def _save_templates_cache(self) -> bool:
        """
        Save templates cache to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.templates_cache_path, 'w') as f:
                json.dump(self.templates_cache, f, indent=2)
                
            logger.info(f"Saved {len(self.templates_cache.get('templates', []))} templates to cache")
            return True
            
        except Exception as e:
            logger.error(f"Error saving templates cache: {str(e)}")
            return False
            
    def _load_custom_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Load custom metadata from file.
        
        Returns:
            Dictionary of template IDs to metadata dictionaries
        """
        try:
            if os.path.exists(self.custom_metadata_path):
                with open(self.custom_metadata_path, 'r') as f:
                    metadata = json.load(f)
                    logger.info(f"Loaded custom metadata for {len(metadata)} templates")
                    return metadata
        except Exception as e:
            logger.error(f"Error loading custom metadata: {str(e)}")
        
        return {} 
    
    def verify_template_metadata_cache(self) -> int:
        """
        Verify all templates in the metadata cache to ensure they match their corresponding
        entries in the templates cache, and repair any inconsistencies found.
        
        Returns:
            Number of templates that were repaired
        """
        if not self.custom_metadata or not self.templates_cache.get("templates"):
            logger.warning("Cannot verify metadata cache: either custom metadata or templates cache is empty")
            return 0
            
        repairs_count = 0
        templates_by_id = {str(t["id"]): t for t in self.templates_cache.get("templates", [])}
        
        for template_id, metadata in list(self.custom_metadata.items()):
            # Skip if not in templates cache
            if template_id not in templates_by_id:
                logger.warning(f"Template ID {template_id} not found in templates cache")
                continue
                
            template = templates_by_id[template_id]
            
            # Check for name mismatch
            if metadata.get("name") and template.get("name") and metadata["name"] != template["name"]:
                logger.warning(f"Template name mismatch: ID {template_id} has name '{metadata['name']}' in metadata but '{template['name']}' in templates cache")
                
                # Fix the metadata
                old_name = metadata["name"]
                metadata["name"] = template["name"]
                repairs_count += 1
                
                logger.info(f"Repaired template {template_id}: renamed from '{old_name}' to '{template['name']}'")
                
                # Update metadata with correct template info
                if not metadata.get("url") and template.get("url"):
                    metadata["url"] = template["url"]
                if not metadata.get("box_count") and template.get("box_count"):
                    metadata["box_count"] = template["box_count"]
                    
                # Save the updated metadata
                self.custom_metadata[template_id] = metadata
        
        # Save changes to file if any repairs were made
        if repairs_count > 0:
            try:
                with open(self.custom_metadata_path, 'w') as f:
                    json.dump(self.custom_metadata, f, indent=2)
                logger.info(f"Saved {repairs_count} metadata repairs to {self.custom_metadata_path}")
            except Exception as e:
                logger.error(f"Error saving metadata repairs: {str(e)}")
                
        return repairs_count 