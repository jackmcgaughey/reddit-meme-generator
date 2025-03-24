#!/usr/bin/env python
"""
Regenerate Meme Template Descriptions

This script generates fresh descriptions for meme templates using OpenAI's API.
It processes each template one by one, generating an accurate description based on
the template image, and saves the descriptions to the custom metadata file.
"""

import os
import json
import time
import logging
import requests
import sys
from io import BytesIO
from PIL import Image
import base64
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

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
API_KEY = os.getenv("OPENAI_API_KEY")
CONCURRENT_REQUESTS = False  # Set to True if you want to process templates in parallel
DELAY_BETWEEN_REQUESTS = 3  # Seconds between API calls to avoid rate limits

# Initialize OpenAI client
client = OpenAI(api_key=API_KEY)

def load_templates() -> List[Dict[str, Any]]:
    """Load templates from the cache file."""
    try:
        with open(TEMPLATES_CACHE_PATH, 'r') as f:
            templates = json.load(f)
        logger.info(f"Loaded {len(templates)} templates from cache")
        return templates
    except Exception as e:
        logger.error(f"Error loading templates: {str(e)}")
        return []

def load_custom_metadata() -> Dict[str, Any]:
    """Load custom metadata from the file."""
    try:
        with open(CUSTOM_METADATA_PATH, 'r') as f:
            metadata = json.load(f)
        logger.info(f"Loaded custom metadata with {len(metadata)} entries")
        return metadata
    except FileNotFoundError:
        logger.warning(f"Custom metadata file not found, creating new one")
        return {}
    except Exception as e:
        logger.error(f"Error loading custom metadata: {str(e)}")
        return {}

def save_custom_metadata(metadata: Dict[str, Any]):
    """Save custom metadata to the file."""
    try:
        with open(CUSTOM_METADATA_PATH, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved custom metadata with {len(metadata)} entries")
    except Exception as e:
        logger.error(f"Error saving custom metadata: {str(e)}")

def download_image(url: str) -> Optional[Image.Image]:
    """Download an image from a URL and return a PIL Image object."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        return image
    except Exception as e:
        logger.error(f"Error downloading image from {url}: {str(e)}")
        return None

def encode_image_to_base64(image: Image.Image) -> str:
    """Convert a PIL Image to base64 encoding."""
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def generate_description(template_name: str, image_base64: str) -> Optional[str]:
    """Generate a description for a template using OpenAI API."""
    if not API_KEY:
        logger.error("OpenAI API key not found. Set OPENAI_API_KEY in .env file.")
        return None
    
    try:
        messages = [
            {"role": "system", "content": "You are an AI specialized in describing internet memes. Provide clear, concise, and accurate descriptions of meme templates that explain the format and how it's typically used."},
            {"role": "user", "content": [
                {"type": "text", "text": f"Please describe the '{template_name}' meme template shown in the image. Explain its format, origin if known, and how it's typically used. Keep it under 100 words."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]}
        ]
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Or another vision-capable model
            messages=messages,
            max_tokens=200
        )
        
        description = response.choices[0].message.content.strip()
        logger.info(f"Generated description for '{template_name}'")
        return description
    
    except Exception as e:
        logger.error(f"Error generating description for '{template_name}': {str(e)}")
        return None

def process_template(template: Dict[str, Any], custom_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single template to generate a description and update metadata."""
    template_id = template["id"]
    template_name = template["name"]
    
    # Check if template already has a description
    if template_id in custom_metadata and "description" in custom_metadata[template_id]:
        logger.info(f"Template '{template_name}' already has a description, skipping")
        return custom_metadata
    
    # Download the template image
    image = download_image(template["url"])
    if not image:
        logger.error(f"Could not download image for template '{template_name}'")
        return custom_metadata
    
    # Encode the image to base64
    image_base64 = encode_image_to_base64(image)
    
    # Generate a description for the template
    description = generate_description(template_name, image_base64)
    if not description:
        logger.error(f"Could not generate description for template '{template_name}'")
        return custom_metadata
    
    # Update custom metadata
    if template_id not in custom_metadata:
        custom_metadata[template_id] = {}
    
    custom_metadata[template_id]["description"] = description
    logger.info(f"Added description for template '{template_name}'")
    
    # Save custom metadata periodically
    save_custom_metadata(custom_metadata)
    
    return custom_metadata

def main():
    """Main entry point for the script."""
    logger.info("Starting description regeneration process")
    
    # Make sure cache directory exists
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # Load templates and custom metadata
    templates = load_templates()
    if not templates:
        logger.error("Could not load templates. Run reset_metadata.py first.")
        sys.exit(1)
    
    custom_metadata = load_custom_metadata()
    
    # Process templates one by one
    templates_processed = 0
    for template in templates:
        custom_metadata = process_template(template, custom_metadata)
        templates_processed += 1
        
        # Add delay between API calls
        if not CONCURRENT_REQUESTS and templates_processed < len(templates):
            logger.info(f"Waiting {DELAY_BETWEEN_REQUESTS} seconds before processing next template")
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Final save of custom metadata
    save_custom_metadata(custom_metadata)
    
    logger.info(f"Successfully processed {templates_processed} templates")
    logger.info("Description regeneration complete")

if __name__ == "__main__":
    main() 