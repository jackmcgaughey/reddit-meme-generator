"""
Main entry point for the Reddit Meme Generator.
"""
import os
import sys
import logging
import dotenv
from typing import Optional, Tuple, List

from reddit_api import RedditMemeAPI
from image_editor import MemeEditor
from config_manager import ConfigManager
from ui import MemeGeneratorUI

# Optional import for AI features
try:
    from ai_meme_generator import AIMemeGenerator
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# Load environment variables
dotenv.load_dotenv()

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("meme_generator.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MemeGeneratorApp:
    """Main application class for Reddit Meme Generator."""
    
    def __init__(self):
        """Initialize the application and its components."""
        self.ui = MemeGeneratorUI()
        self.config_manager = ConfigManager()
        
        # These will be initialized on demand
        self.reddit_api = None
        self.image_editor = None
        self.ai_generator = None
        
        # Initialize image editor
        image_config = self.config_manager.get_image_editor_config()
        self.image_editor = MemeEditor(
            font_path=image_config.get("font_path", ""),
            output_dir=image_config.get("output_dir", "generated_memes")
        )
        
        # Initialize AI generator if available
        self._init_ai_generator()
        
        logger.info("Application initialized")
    
    def _init_ai_generator(self) -> bool:
        """
        Initialize AI meme generator if API key is available.
        
        Returns:
            True if initialized successfully
        """
        if not AI_AVAILABLE:
            logger.warning("AI module not available. Cannot use AI features.")
            return False
            
        # Check if AI is enabled in config
        ai_config = self.config_manager.get_ai_config()
        if not ai_config.get("enabled", False):
            return False
            
        # Get OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return False
            
        try:
            self.ai_generator = AIMemeGenerator(
                api_key=api_key,
                temp_dir=ai_config.get("temp_dir", "temp_images")
            )
            logger.info("AI meme generator initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize AI generator: {e}")
            return False
    
    def _init_reddit_api(self) -> bool:
        """
        Initialize Reddit API if credentials are configured.
        
        Returns:
            True if initialized successfully
        """
        if self.reddit_api:
            return True
            
        if not self.config_manager.is_reddit_configured():
            self.ui.display_error(
                "Reddit API credentials are not configured.\n"
                "Please update your credentials first."
            )
            return False
        
        try:
            creds = self.config_manager.get_reddit_credentials()
            self.reddit_api = RedditMemeAPI(
                client_id=creds["client_id"],
                client_secret=creds["client_secret"],
                user_agent=creds["user_agent"]
            )
            logger.info("Reddit API initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Reddit API: {e}")
            self.ui.display_error(f"Failed to initialize Reddit API: {e}")
            return False
    
    def update_reddit_credentials(self):
        """Prompt for and update Reddit API credentials."""
        client_id, client_secret = self.ui.get_reddit_credentials()
        
        if client_id and client_secret:
            if self.config_manager.update_reddit_credentials(client_id, client_secret):
                self.ui.display_info("Reddit API credentials updated successfully!")
                # Reset Reddit API to reinitialize with new credentials
                self.reddit_api = None
            else:
                self.ui.display_error("Failed to save Reddit API credentials.")
        else:
            self.ui.display_error("Reddit API credentials cannot be empty.")
    
    def browse_subreddits(self):
        """Browse popular meme subreddits."""
        if not self._init_reddit_api():
            return
        
        # Get trending subreddits
        subreddits = self.reddit_api.get_trending_meme_subreddits()
        
        if not subreddits:
            self.ui.display_error("Failed to retrieve meme subreddits. Please try again later.")
            return
        
        # Show subreddit selection
        selected_subreddit = self.ui.select_subreddit(subreddits)
        if not selected_subreddit:
            return
        
        # Show category selection
        categories = self.config_manager.config.get("default_categories", 
                                                 ["hot", "new", "top", "rising"])
        selected_category = self.ui.select_category(categories)
        if not selected_category:
            return
        
        # Fetch memes from selected subreddit
        memes = self.reddit_api.fetch_memes_from_subreddit(
            subreddit_name=selected_subreddit,
            category=selected_category
        )
        
        self._handle_meme_selection(memes)
    
    def search_memes(self):
        """Search for memes by keyword."""
        if not self._init_reddit_api():
            return
        
        # Get search keyword
        keyword = self.ui.get_search_keyword()
        if not keyword:
            return
        
        # Search for memes
        memes = self.reddit_api.search_memes_by_keyword(keyword=keyword)
        
        # Convert to standard format for UI
        # (title, url, score, post_id)
        standard_memes = [(m[0], m[1], m[2], m[4]) for m in memes]
        
        self._handle_meme_selection(standard_memes)
    
    def generate_custom_meme(self):
        """Generate a custom meme from scratch."""
        self.ui.display_info(
            "To generate a custom meme, first select a meme template from Reddit.\n"
            "You can browse subreddits or search for specific memes."
        )
    
    def view_generated_memes(self):
        """View previously generated memes."""
        output_dir = self.config_manager.config.get("image_editor", {}).get("output_dir", "generated_memes")
        selected_meme = self.ui.browse_generated_memes(output_dir)
        
        if selected_meme:
            # Try to open the selected meme
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(selected_meme)
                elif os.name == 'posix':  # macOS and Linux
                    import subprocess
                    if os.uname().sysname == 'Darwin':  # macOS
                        subprocess.run(['open', selected_meme], check=True)
                    else:  # Linux
                        subprocess.run(['xdg-open', selected_meme], check=True)
            except Exception as e:
                self.ui.display_error(f"Could not open the image: {e}")
    
    def _handle_meme_selection(self, memes: List[Tuple[str, str, int, str]]):
        """
        Handle meme selection and generation.
        
        Args:
            memes: List of (title, image_url, score, identifier) tuples
        """
        selected_meme = self.ui.select_meme(memes)
        if not selected_meme:
            return
        
        title, image_url = selected_meme
        
        # Get meme text
        top_text, bottom_text = self.ui.get_meme_text()
        
        # Generate meme
        output_path = self.image_editor.generate_meme(
            image_url=image_url,
            top_text=top_text,
            bottom_text=bottom_text
        )
        
        # Display result
        self.ui.display_generated_meme(output_path)
    
    def handle_ai_meme_regeneration(self):
        """Handle AI meme regeneration functionality."""
        if not AI_AVAILABLE:
            self.ui.display_error(
                "AI meme generation is not available. The 'openai' package is missing.\n"
                "Try running 'pip install openai python-dotenv' to install the required dependencies."
            )
            return
            
        # Get current AI settings
        ai_config = self.config_manager.get_ai_config()
        
        while True:
            choice = self.ui.display_ai_menu()
            
            if choice == 1:  # Regenerate existing meme
                self._regenerate_meme_with_ai()
            elif choice == 2:  # Update OpenAI API Key
                self._update_openai_api_key()
            elif choice == 3:  # Configure AI settings
                new_settings = self.ui.configure_ai_settings(ai_config)
                if self.config_manager.update_ai_settings(
                    enabled=new_settings["enabled"],
                    temp_dir=new_settings["temp_dir"],
                    model=new_settings["model"]
                ):
                    self.ui.display_info("AI settings updated successfully!")
                    
                    # Re-initialize AI generator with new settings
                    if new_settings["enabled"]:
                        if not os.getenv("OPENAI_API_KEY"):
                            self._update_openai_api_key()
                        
                        self._init_ai_generator()
                    
                else:
                    self.ui.display_error("Failed to update AI settings.")
            elif choice == 4:  # Back to main menu
                break
    
    def _regenerate_meme_with_ai(self):
        """Regenerate an existing meme with AI."""
        # Check if OpenAI API key is set
        if not os.getenv("OPENAI_API_KEY"):
            self.ui.display_info(
                "OpenAI API key is required for AI features.\n"
                "Please provide your API key."
            )
            self._update_openai_api_key()
            if not os.getenv("OPENAI_API_KEY"):
                return
        
        # Check if AI generator is available
        if not self.ai_generator:
            self.ui.display_error(
                "AI generator could not be initialized.\n"
                "Please check your OpenAI API key and try again."
            )
            return
            
        # Browse existing memes
        output_dir = self.config_manager.config.get("image_editor", {}).get("output_dir", "generated_memes")
        selected_meme = self.ui.browse_generated_memes(output_dir)
        
        if not selected_meme:
            return
            
        # Use AI to regenerate meme
        self.ui.display_info("Regenerating meme with AI... This may take a moment.")
        
        new_meme_path = self.ai_generator.regenerate_meme(
            original_meme_path=selected_meme,
            image_editor=self.image_editor
        )
        
        # Display result
        self.ui.display_ai_meme_result(selected_meme, new_meme_path)
    
    def _update_openai_api_key(self):
        """Update the OpenAI API key."""
        current_key = os.getenv("OPENAI_API_KEY") or "Not set"
        masked_key = current_key[:4] + "*" * 8 + current_key[-4:] if len(current_key) > 8 else "Not set"
        
        self.ui.display_info(f"Current OpenAI API Key: {masked_key}\n\nYou are about to update your OpenAI API key.")
        
        api_key = self.ui.get_openai_api_key()
        if not api_key:
            return
            
        # Check for existing .env file content
        env_content = ""
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                lines = f.readlines()
                # Keep any lines that don't set OPENAI_API_KEY
                env_content = "".join([line for line in lines if not line.startswith("OPENAI_API_KEY=")])
        
        # Add the new API key
        with open(".env", "w") as f:
            f.write(env_content)
            f.write(f"OPENAI_API_KEY={api_key}\n")
        
        # Reload environment variables
        dotenv.load_dotenv()
        
        # Re-initialize AI generator
        self._init_ai_generator()
        
        self.ui.display_info("OpenAI API key updated successfully!")
    
    def run(self):
        """Run the main application loop."""
        self.ui.display_welcome()
        
        # Check if Reddit credentials are configured
        if not self.config_manager.is_reddit_configured():
            self.ui.display_info(
                "Welcome to Reddit Meme Generator!\n\n"
                "It looks like this is your first time running the application.\n"
                "You'll need to configure your Reddit API credentials to get started."
            )
            self.update_reddit_credentials()
        
        # Main menu loop
        running = True
        while running:
            choice = self.ui.display_main_menu()
            
            if choice == 1:
                self.browse_subreddits()
            elif choice == 2:
                self.search_memes()
            elif choice == 3:
                self.generate_custom_meme()
            elif choice == 4:
                self.view_generated_memes()
            elif choice == 5:
                self.update_reddit_credentials()
            elif choice == 6:
                self.handle_ai_meme_regeneration()
            elif choice == 7:
                running = False
                self.ui.display_info("Thank you for using Reddit Meme Generator!")
        
        logger.info("Application exiting")

def main():
    """Entry point function."""
    try:
        app = MemeGeneratorApp()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        print(f"\nAn unexpected error occurred: {e}")
        print("Please check the log file for more details.")
        sys.exit(1)

if __name__ == "__main__":
    main() 