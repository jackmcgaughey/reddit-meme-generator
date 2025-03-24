#!/usr/bin/env python
"""
Reset Template Metadata Script

This script clears and resets the template metadata files to fix mismatches between
template images and their descriptions. It:
1. Removes all custom metadata entries
2. Creates a clean template cache file with minimal metadata
3. Prepares the system for regenerating accurate descriptions
"""

import os
import json
import sys
import logging
import requests
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CACHE_DIR = "cache"
CUSTOM_METADATA_PATH = os.path.join(CACHE_DIR, "custom_template_metadata.json")
TEMPLATES_CACHE_PATH = os.path.join(CACHE_DIR, "templates_cache.json")
IMGFLIP_API_URL = "https://api.imgflip.com/get_memes"

def get_templates_from_api() -> List[Dict[str, Any]]:
    """Fetch templates directly from the ImgFlip API."""
    try:
        response = requests.get(IMGFLIP_API_URL)
        response.raise_for_status()
        data = response.json()
        
        if data["success"]:
            templates = data["data"]["memes"]
            logger.info(f"Retrieved {len(templates)} templates from ImgFlip API")
            return templates
        else:
            logger.error(f"ImgFlip API error: {data.get('error_message', 'Unknown error')}")
            return []
    except Exception as e:
        logger.error(f"Error retrieving templates from ImgFlip API: {str(e)}")
        return []

def reset_custom_metadata():
    """Reset the custom metadata file to an empty object."""
    try:
        with open(CUSTOM_METADATA_PATH, 'w') as f:
            json.dump({}, f, indent=2)
        logger.info(f"Reset custom metadata file at {CUSTOM_METADATA_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error resetting custom metadata: {str(e)}")
        return False

def reset_templates_cache(templates: List[Dict[str, Any]]):
    """Reset the templates cache with fresh data from the API."""
    try:
        # Keep only essential template data without custom_metadata
        clean_templates = []
        for template in templates:
            clean_template = {
                "id": template["id"],
                "name": template["name"],
                "url": template["url"],
                "width": template["width"],
                "height": template["height"],
                "box_count": template["box_count"],
                "captions": template.get("captions", 0)
            }
            clean_templates.append(clean_template)
            
        with open(TEMPLATES_CACHE_PATH, 'w') as f:
            json.dump(clean_templates, f, indent=2)
            
        logger.info(f"Reset templates cache with {len(clean_templates)} templates")
        return True
    except Exception as e:
        logger.error(f"Error resetting templates cache: {str(e)}")
        return False

def main():
    """Main entry point for the script."""
    logger.info("Starting metadata reset process")
    
    # Make sure cache directory exists
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # Fetch templates from API
    templates = get_templates_from_api()
    if not templates:
        logger.error("Could not retrieve templates from API. Aborting.")
        sys.exit(1)
    
    # Reset the metadata files
    custom_reset = reset_custom_metadata()
    templates_reset = reset_templates_cache(templates)
    
    if custom_reset and templates_reset:
        logger.info("Successfully reset all template metadata")
        logger.info("You can now restart the application and regenerate metadata for each template")
    else:
        logger.error("Failed to reset template metadata")
        sys.exit(1)

if __name__ == "__main__":
    main() 