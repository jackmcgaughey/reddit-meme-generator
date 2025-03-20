"""
Configuration manager for the meme generator.
"""
import os
import json
import logging
from typing import Dict, Any, Optional

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConfigManager:
    """Manager for meme generator configuration."""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the config manager.
        
        Args:
            config_file: Path to the config file
        """
        self.config_file = config_file
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default if it doesn't exist.
        
        Returns:
            Dict containing configuration
        """
        default_config = {
            "reddit": {
                "client_id": "",
                "client_secret": "",
                "user_agent": "MemeGenerator/1.0"
            },
            "image_editor": {
                "font_path": "",  # Will auto-detect system fonts if empty
                "output_dir": "generated_memes"
            },
            "ai": {
                "enabled": False,
                "temp_dir": "temp_images",
                "model": "gpt-4o"
            },
            "default_subreddits": [
                "memes",
                "dankmemes",
                "wholesomememes",
                "MemeEconomy",
                "AdviceAnimals"
            ],
            "default_categories": [
                "hot",
                "new",
                "top",
                "rising"
            ]
        }
        
        # Create config file if it doesn't exist
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default configuration at {self.config_file}")
            return default_config
        
        # Load existing config
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {self.config_file}")
            
            # Add AI settings if not present (for backward compatibility)
            if "ai" not in config:
                config["ai"] = default_config["ai"]
                self.config = config
                self.save_config()
                
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}. Using defaults.")
            return default_config
    
    def save_config(self) -> bool:
        """
        Save current configuration to file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def is_reddit_configured(self) -> bool:
        """
        Check if Reddit API is configured.
        
        Returns:
            True if Reddit API credentials are set
        """
        return (
            self.config.get("reddit", {}).get("client_id", "") != "" and
            self.config.get("reddit", {}).get("client_secret", "") != ""
        )
    
    def update_reddit_credentials(
        self, 
        client_id: str, 
        client_secret: str, 
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Update Reddit API credentials.
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: Optional user agent string
            
        Returns:
            True if updated successfully
        """
        if "reddit" not in self.config:
            self.config["reddit"] = {}
        
        self.config["reddit"]["client_id"] = client_id
        self.config["reddit"]["client_secret"] = client_secret
        
        if user_agent:
            self.config["reddit"]["user_agent"] = user_agent
        elif "user_agent" not in self.config["reddit"]:
            self.config["reddit"]["user_agent"] = "MemeGenerator/1.0"
            
        return self.save_config()
    
    def get_reddit_credentials(self) -> Dict[str, str]:
        """
        Get Reddit API credentials.
        
        Returns:
            Dict with client_id, client_secret, and user_agent
        """
        reddit_config = self.config.get("reddit", {})
        return {
            "client_id": reddit_config.get("client_id", ""),
            "client_secret": reddit_config.get("client_secret", ""),
            "user_agent": reddit_config.get("user_agent", "MemeGenerator/1.0")
        }
    
    def get_default_subreddits(self) -> list:
        """Get list of default subreddits."""
        return self.config.get("default_subreddits", ["memes", "dankmemes"])
    
    def get_guitar_subreddits(self) -> list:
        """Get list of guitar-related subreddits."""
        return self.config.get("guitar_subreddits", [
            "guitar", 
            "guitarmemes", 
            "guitarcirclejerk", 
            "guitarplaying", 
            "guitars"
        ])
    
    def get_image_editor_config(self) -> Dict[str, str]:
        """Get image editor configuration."""
        return self.config.get("image_editor", {
            "font_path": "",
            "output_dir": "generated_memes"
        })
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI configuration."""
        return self.config.get("ai", {
            "enabled": False,
            "temp_dir": "temp_images",
            "model": "gpt-4o"
        })
    
    def update_ai_settings(self, enabled: bool, temp_dir: Optional[str] = None, model: Optional[str] = None) -> bool:
        """
        Update AI settings.
        
        Args:
            enabled: Whether AI features are enabled
            temp_dir: Directory for temporary image storage
            model: OpenAI model to use
            
        Returns:
            True if updated successfully
        """
        if "ai" not in self.config:
            self.config["ai"] = {
                "enabled": False,
                "temp_dir": "temp_images",
                "model": "gpt-4o"
            }
        
        self.config["ai"]["enabled"] = enabled
        
        if temp_dir:
            self.config["ai"]["temp_dir"] = temp_dir
            
        if model:
            self.config["ai"]["model"] = model
            
        return self.save_config() 