"""
ImgFlip API Integration Module

This module provides a wrapper around the ImgFlip API for fetching meme templates
and interacting with their service. It includes functionality to:
1. Fetch popular meme templates
2. Categorize templates
3. Cache template data
4. Manage custom metadata for templates
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

class ImgFlipAPI:
    """
    A wrapper for the ImgFlip API that provides functionality for retrieving
    and managing meme templates.
    """
    
    def __init__(self, 
                 username: str = None, 
                 password: str = None, 
                 api_url: str = "https://api.imgflip.com", 
                 cache_dir: str = "cache"):
        """
        Initialize the ImgFlip API client.
        
        Args:
            username: ImgFlip username (optional)
            password: ImgFlip password (optional)
            api_url: ImgFlip API URL
            cache_dir: Directory to cache templates and metadata
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
        
        # Default categories with common templates
        self.default_categories = {
            "music": [
                "21735", # The Rock Driving
                "61516", # Grandfather Finds The Internet
                "61520", # Futurama Fry
                "101470", # Ancient Aliens
                "61539", # First World Problems
                "163573", # Imagination Spongebob
                "28251", # Skeptical Third World Kid
                "61533", # X All The Y
                "101288", # Third World Success Kid
                "405658", # Grumpy Cat
                "4173692", # Scared Cat
                "16464531", # Music Band Fellow Kids
                "91538330", # Roll Safe Think About It
                "27813981", # Hide the Pain Harold
                "61527", # Y U No
                "61585", # Bad Luck Brian
                "235589", # Evil Toddler
                "14371066", # Star Wars Yoda
                "124822590", # Left Exit 12 Off Ramp
                "61546", # Brace Yourselves X is Coming
                "61556", # Grandma Finds The Internet
                "5496396", # Leonardo Dicaprio Cheers
                "93895088", # Expanding Brain
                "155067746", # Surprised Pikachu
                "89370399", # Roll Safe Think About It
                "119139145", # Blank Nut Button
                "195515965", # Clown Applying Makeup
                "21809375", # Drake Hotline Bling
                "102156234", # Mocking Spongebob
                "217743513", # UNO Draw 25 Cards
                "196652226", # Spongebob Ight Imma Head Out
                "131087935", # Running Away Balloon
                "178591752", # Tuxedo Winnie The Pooh
                "131940431", # Gru's Plan
                "222403160", # Bernie I Am Once Again Asking For Your Support
                "247375501", # Buff Doge vs. Cheems
                "143601528", # Monkey Puppet Side Eye
                "252758727", # Mother Ignoring Kid Drowning
                "252600902", # Always Has Been
                "322841258", # Anakin Padme 4 Panel
                "259237855", # Laughing Leo
                "101511", # Don't You Squidward
                "84341851", # Evil Kermit
                "61544", # Success Kid
                "61532", # The Most Interesting Man In The World
                "8072285", # Doge
                "1367068", # Joker
                "135678846", # Who Killed Hannibal
                "61522", # Skeptical Baby
                "145838333", # Krusty Krab vs Chum Bucket
                "135256802", # Epic Handshake
                "110163934", # I Bet He's Thinking About Other Women
                "188390779", # Woman Yelling At Cat
                "129242436", # Change My Mind
                "438680", # Batman Slapping Robin
                "124055727", # Y'all Got Any More Of That
                "563423", # That Would Be Great
                "4087833", # Waiting Skeleton
                "114585149", # Inhaling Seagull
                "89655"  # Uncle Sam
            ],
            "reaction": [
                "21735", # The Rock Driving
                "61520", # Futurama Fry
                "61539", # First World Problems
                "163573", # Imagination Spongebob
                "405658", # Grumpy Cat
                "4173692", # Scared Cat
                "27813981", # Hide the Pain Harold
                "235589", # Evil Toddler
                "124822590", # Left Exit 12 Off Ramp
                "5496396", # Leonardo Dicaprio Cheers
                "155067746", # Surprised Pikachu
                "89370399", # Roll Safe Think About It
                "119139145", # Blank Nut Button
                "195515965", # Clown Applying Makeup
                "102156234", # Mocking Spongebob
                "196652226", # Spongebob Ight Imma Head Out
                "131087935", # Running Away Balloon
                "143601528", # Monkey Puppet Side Eye
                "252758727", # Mother Ignoring Kid Drowning
                "101511", # Don't You Squidward
                "84341851", # Evil Kermit
                "8072285", # Doge
                "1367068", # Joker
                "188390779", # Woman Yelling At Cat
                "114585149", # Inhaling Seagull
            ],
            "comparison": [
                "93895088", # Expanding Brain
                "178591752", # Tuxedo Winnie The Pooh
                "21809375", # Drake Hotline Bling
                "247375501", # Buff Doge vs. Cheems
                "252600902", # Always Has Been
                "145838333", # Krusty Krab vs Chum Bucket
                "135256802", # Epic Handshake
                "129242436", # Change My Mind
            ],
            "statement": [
                "61527", # Y U No
                "61585", # Bad Luck Brian
                "14371066", # Star Wars Yoda
                "61546", # Brace Yourselves X is Coming
                "61556", # Grandma Finds The Internet
                "217743513", # UNO Draw 25 Cards
                "131940431", # Gru's Plan
                "222403160", # Bernie I Am Once Again Asking For Your Support
                "61544", # Success Kid
                "61532", # The Most Interesting Man In The World
                "110163934", # I Bet He's Thinking About Other Women
                "438680", # Batman Slapping Robin
                "124055727", # Y'all Got Any More Of That
                "563423", # That Would Be Great
                "4087833", # Waiting Skeleton
                "89655"  # Uncle Sam
            ]
        }
        
        # Load cached templates if available
        self.templates_cache = self._load_templates_cache()
        self.custom_metadata = self._load_custom_metadata()
        
    def set_credentials(self, username: str, password: str) -> None:
        """
        Set ImgFlip API credentials.
        
        Args:
            username: ImgFlip username
            password: ImgFlip password
        """
        self.username = username
        self.password = password
        
    def get_templates(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get all available meme templates from ImgFlip.
        
        Args:
            force_refresh: Force refresh of cached templates
            
        Returns:
            List of template dictionaries
        """
        if not force_refresh and self.templates_cache:
            logger.info("Using cached templates")
            return self.templates_cache
            
        try:
            # Make API request to ImgFlip
            response = requests.get(f"{self.api_url}/get_memes")
            response.raise_for_status()
            data = response.json()
            
            if data["success"]:
                templates = data["data"]["memes"]
                logger.info(f"Retrieved {len(templates)} templates from ImgFlip API")
                
                # Add custom metadata to templates
                for template in templates:
                    template_id = template.get("id")
                    if template_id in self.custom_metadata:
                        template["custom_metadata"] = self.custom_metadata[template_id]
                
                # Cache the templates
                self.templates_cache = templates
                self._save_templates_cache()
                
                return templates
            else:
                logger.error(f"ImgFlip API error: {data.get('error_message', 'Unknown error')}")
                return []
                
        except Exception as e:
            logger.error(f"Error retrieving templates from ImgFlip API: {str(e)}")
            
            # Return cached templates as fallback if available
            if self.templates_cache:
                logger.info("Using cached templates as fallback")
                return self.templates_cache
            
            return []
    
    def get_templates_by_category(self, category: str = "music") -> List[Dict[str, Any]]:
        """
        Get templates filtered by category.
        
        Args:
            category: Category name ('music', 'reaction', 'comparison', 'statement')
            
        Returns:
            List of template dictionaries in the specified category
        """
        all_templates = self.get_templates()
        
        if category not in self.default_categories:
            # Return all templates if category not recognized
            logger.warning(f"Unknown category: {category}. Returning all templates.")
            return all_templates
            
        # Filter templates by ID in the category
        category_ids = set(self.default_categories[category])
        return [template for template in all_templates if template.get("id") in category_ids]
    
    def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific template by ID.
        
        Args:
            template_id: The template ID to look for
            
        Returns:
            Template dictionary or None if not found
        """
        all_templates = self.get_templates()
        
        for template in all_templates:
            if template.get("id") == template_id:
                # Merge with custom metadata if available
                if template_id in self.custom_metadata:
                    template["custom_metadata"] = self.custom_metadata[template_id]
                return template
                
        logger.warning(f"Template with ID {template_id} not found")
        return None
    
    def get_template_metadata(self, template_id: str) -> Dict[str, Any]:
        """
        Get metadata for a specific template.
        
        Args:
            template_id: The template ID
            
        Returns:
            Dictionary of template metadata
        """
        # First try to find the template from the API cache to get the official name
        template = self.get_template_by_id(template_id)
        template_name = None
        if template:
            template_name = template.get("name", f"Template {template_id}")
        
        # Check custom metadata
        metadata = {}
        if template_id in self.custom_metadata:
            metadata = self.custom_metadata[template_id].copy()
            
            # Validate that the metadata matches the template
            # This prevents mismatches between templates and descriptions
            if template_name and 'name' in metadata:
                metadata_name = metadata['name']
                
                # If the names don't match, there's likely a metadata mismatch
                # In this case, we'll consider the metadata invalid
                if template_name != metadata_name:
                    logger.warning(f"Template name mismatch: template '{template_name}' vs metadata '{metadata_name}'")
                    # Return empty metadata so it will be regenerated
                    return {}
        
        # Always use the official template name from API if available
        if template_name:
            metadata["name"] = template_name
        
        # If we have metadata, return it
        if metadata:
            return metadata
        
        # No custom metadata, create basic metadata from template
        if template:
            return {
                "name": template_name,
                "box_count": template.get("box_count", 2),
                "width": template.get("width", 0),
                "height": template.get("height", 0)
            }
        
        # Return default metadata
        return {
            "name": f"Template {template_id}",
            "box_count": 2
        }
    
    def save_custom_metadata(self, template_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Save custom metadata for a template.
        
        Args:
            template_id: The template ID
            metadata: Dictionary of metadata to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing metadata
            self.custom_metadata = self._load_custom_metadata()
            
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
    
    def _load_templates_cache(self) -> List[Dict[str, Any]]:
        """
        Load templates from cache file.
        
        Returns:
            List of template dictionaries or empty list if cache doesn't exist
        """
        try:
            if os.path.exists(self.templates_cache_path):
                with open(self.templates_cache_path, 'r') as f:
                    templates = json.load(f)
                    logger.info(f"Loaded {len(templates)} templates from cache")
                    return templates
        except Exception as e:
            logger.error(f"Error loading templates cache: {str(e)}")
        
        return []
    
    def _save_templates_cache(self) -> bool:
        """
        Save templates to cache file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.templates_cache_path, 'w') as f:
                json.dump(self.templates_cache, f, indent=2)
                
            logger.info(f"Saved {len(self.templates_cache)} templates to cache")
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