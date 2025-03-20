"""
Main entry point for the Reddit Meme Generator.
"""
import os
import sys
import logging
import dotenv
from typing import Optional, Tuple, List
import getpass

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
        """Initialize the application."""
        # Set up logging
        global logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # File handler
        file_handler = logging.FileHandler('meme_generator.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Initialize components
        self.ui = MemeGeneratorUI()
        self.config_manager = ConfigManager()
        
        # Initialize Reddit API (without credentials for now)
        self.reddit_api = RedditMemeAPI(client_id="", client_secret="")
        
        # Initialize image editor
        editor_config = self.config_manager.get_image_editor_config()
        self.image_editor = MemeEditor(
            font_path=editor_config.get("font_path", ""),
            output_dir=editor_config.get("output_dir", "generated_memes")
        )
        
        # Initialize AI meme generator if available
        self.ai_generator = None
        try:
            # Load .env file if it exists
            dotenv.load_dotenv()
            
            # Check for OpenAI API key
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.ai_generator = AIMemeGenerator(api_key)
                logger.info("AI meme generator initialized")
            else:
                logger.info("OpenAI API key not found. AI features will be limited.")
                self.ai_generator = AIMemeGenerator()  # Initialize without API key
                logger.info("AI meme generator initialized")
        except ImportError:
            logger.warning("OpenAI package not available. AI features will be disabled.")
        except Exception as e:
            logger.error(f"Error initializing AI generator: {str(e)}")
        
        logger.info("Application initialized")
    
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
    
    def _initialize_reddit_api(self):
        """Initialize the Reddit API with credentials from config."""
        if not self.config_manager.is_reddit_configured():
            self.ui.display_info(
                "Welcome to Reddit Meme Generator!\n\n"
                "It looks like this is your first time running the application.\n"
                "You'll need to configure your Reddit API credentials to get started."
            )
            self._update_reddit_credentials()
            return
        
        credentials = self.config_manager.get_reddit_credentials()
        try:
            self.reddit_api.configure(
                client_id=credentials["client_id"],
                client_secret=credentials["client_secret"],
                user_agent=credentials.get("user_agent", "MemeGenerator/1.0")
            )
            logger.info("Reddit API initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit API: {str(e)}")
            self.ui.display_error(
                f"Failed to initialize Reddit API: {str(e)}\n"
                "Please update your credentials."
            )
            self._update_reddit_credentials()

    def _update_reddit_credentials(self):
        """Update Reddit API credentials in configuration."""
        client_id, client_secret = self.ui.get_reddit_credentials()
        self.config_manager.update_reddit_credentials(client_id, client_secret)
        self.ui.display_info("Reddit API credentials updated successfully!")
        
        # Re-initialize Reddit API with new credentials
        credentials = self.config_manager.get_reddit_credentials()
        self.reddit_api.configure(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            user_agent=credentials.get("user_agent", "MemeGenerator/1.0")
        )

    def _browse_subreddits(self):
        """Browse memes from popular subreddits."""
        default_subreddits = self.config_manager.get_default_subreddits()
        
        # Convert the simple string list to the expected format for select_subreddit
        formatted_subreddits = [(sub, f"Popular meme subreddit", 0) for sub in default_subreddits]
        
        subreddit = self.ui.select_subreddit(formatted_subreddits)
        if not subreddit:
            return
        
        category = self.ui.select_category(self.config_manager.get_default_categories())
        if not category:
            return
        
        try:
            # This should return (title, url, score, id) tuples
            memes = self.reddit_api.get_memes_from_subreddit(subreddit, category, limit=10)
            if not memes:
                self.ui.display_error(f"No memes found in r/{subreddit} under {category}.")
                return
                
            # The UI's select_meme method now handles different tuple formats
            title, image_url = self.ui.select_meme(memes)
            if not title or not image_url:
                return
                
            self._handle_meme_selection(title, image_url)
        except Exception as e:
            logger.error(f"Error browsing subreddit: {str(e)}")
            self.ui.display_error(f"Error browsing subreddit: {str(e)}")
            
    def _browse_guitar_subreddits(self):
        """Browse memes from guitar-related subreddits."""
        guitar_subreddits = self.config_manager.get_guitar_subreddits()
        
        # Convert the simple string list to the expected format for select_subreddit
        formatted_subreddits = [(sub, f"Guitar-related subreddit", 0) for sub in guitar_subreddits]
        
        subreddit = self.ui.select_subreddit(formatted_subreddits)
        if not subreddit:
            return
        
        category = self.ui.select_category(self.config_manager.get_default_categories())
        if not category:
            return
        
        try:
            memes = self.reddit_api.get_memes_from_subreddit(subreddit, category, limit=10)
            if not memes:
                self.ui.display_error(f"No memes found in r/{subreddit} under {category}.")
                return
                
            # The UI's select_meme method now handles different tuple formats
            title, image_url = self.ui.select_meme(memes)
            if not title or not image_url:
                return
                
            # Let user choose a band for this meme
            band_name = self.ui.get_band_name()
            if not band_name:
                # If no band name provided, proceed with regular meme generation
                self._handle_meme_selection(title, image_url)
            else:
                # Generate band-themed meme
                self._handle_band_meme_selection(title, image_url, band_name)
                
        except Exception as e:
            logger.error(f"Error browsing guitar subreddit: {str(e)}")
            self.ui.display_error(f"Error browsing guitar subreddit: {str(e)}")

    def _search_memes(self):
        """Search for memes by keyword."""
        keyword = self.ui.get_search_keyword()
        if not keyword:
            self.ui.display_error("No keyword provided.")
            return
            
        try:
            # The search_memes method returns 5-element tuples
            memes = self.reddit_api.search_memes(keyword, limit=10)
            if not memes:
                self.ui.display_error(f"No memes found for keyword '{keyword}'.")
                return
                
            # The UI's select_meme method now handles both tuple formats
            title, image_url = self.ui.select_meme(memes)
            if not title or not image_url:
                return
                
            self._handle_meme_selection(title, image_url)
        except Exception as e:
            logger.error(f"Error searching for memes: {str(e)}")
            self.ui.display_error(f"Error searching for memes: {str(e)}")

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
                    self.ui.display_info(f"Opened meme: {selected_meme}")
                elif os.name == 'posix':  # macOS and Linux
                    import subprocess
                    if os.uname().sysname == 'Darwin':  # macOS
                        subprocess.run(['open', selected_meme], check=True)
                        self.ui.display_info(f"Opened meme: {selected_meme}")
                    else:  # Linux
                        subprocess.run(['xdg-open', selected_meme], check=True)
                        self.ui.display_info(f"Opened meme: {selected_meme}")
            except Exception as e:
                self.ui.display_error(f"Could not open the image: {e}\nPath: {selected_meme}")
    
    def _handle_meme_selection(self, title: str, image_url: str):
        """
        Handle meme selection and generation.
        
        Args:
            title: Title of the meme
            image_url: URL of the meme image
        """
        # Get meme text
        top_text, bottom_text = self.ui.get_meme_text()
        
        # Generate meme
        output_path = self.image_editor.generate_meme(
            image_path=image_url,
            top_text=top_text,
            bottom_text=bottom_text
        )
        
        # Display result
        self.ui.display_generated_meme(output_path)
    
    def handle_guitar_band_memes(self):
        """Handle guitar-related meme generation with band customization."""
        # Check if Reddit API and AI are properly configured
        if not self.config_manager.is_reddit_configured():
            self.ui.display_info("Reddit API credentials are required to fetch guitar memes.")
            self._update_reddit_credentials()
            
        # Create guitar meme submenu
        running = True
        while running:
            option = self.ui.display_guitar_menu()
            
            if option == "Browse guitar subreddits":
                self._browse_guitar_subreddits()
                
            elif option == "Search for guitar memes":
                self._search_guitar_memes()
                
            elif option == "Generate band-themed meme":
                self._generate_band_meme()
                
            elif option == "Back to main menu":
                running = False
    
    def _search_guitar_memes(self):
        """Search for guitar-related memes."""
        keyword = self.ui.get_search_keyword("Enter guitar-related search term: ")
        if not keyword:
            # If no keyword provided, use a default guitar-related term
            keyword = "guitar"
            
        try:
            # The search_guitar_memes method also returns 5-element tuples
            memes = self.reddit_api.search_guitar_memes(keyword, limit=10)
            if not memes:
                self.ui.display_error(f"No guitar memes found for keyword '{keyword}'.")
                return
                
            # The UI's select_meme method now handles both tuple formats
            title, image_url = self.ui.select_meme(memes)
            if not title or not image_url:
                return
            
            # Let user choose a band for this meme
            band_name = self.ui.get_band_name()
            if not band_name:
                # If no band name provided, proceed with regular meme generation
                self._handle_meme_selection(title, image_url)
            else:
                # Generate band-themed meme
                self._handle_band_meme_selection(title, image_url, band_name)
        except Exception as e:
            logger.error(f"Error searching for guitar memes: {str(e)}")
            self.ui.display_error(f"Error searching for guitar memes: {str(e)}")
    
    def _generate_band_meme(self):
        """Generate a custom band-themed meme."""
        band_name = self.ui.get_band_name()
        if not band_name:
            self.ui.display_error("No band name provided.")
            return
            
        # Let the user choose to upload an image or search for one
        choice = input("Upload image (1) or search for band-related image (2)? ")
        
        image_url = None
        title = None
        
        if choice == "1":
            image_url = input("Enter path to local image or URL: ")
            title = f"Custom {band_name} meme"
        else:
            # Search for a band-related image
            try:
                self.ui.display_info(f"Searching for images related to '{band_name}'...")
                memes = self.reddit_api.search_band_images(band_name, limit=10)
                if not memes:
                    self.ui.display_info(f"No images found specifically for '{band_name}', falling back to guitar images...")
                    memes = self.reddit_api.search_guitar_memes("guitar", limit=10)
                    if not memes:
                        self.ui.display_error("No images found. Please try again.")
                        return
                    
                title, image_url = self.ui.select_meme(memes)
                if not title or not image_url:
                    return
            except Exception as e:
                logger.error(f"Error searching for band images: {str(e)}")
                self.ui.display_error(f"Error searching for images: {str(e)}")
                return
        
        # Generate band-themed meme
        if image_url:
            self._handle_band_meme_selection(title, image_url, band_name)
    
    def _handle_band_meme_selection(self, title: str, image_url: str, band_name: str):
        """
        Handle band-themed meme generation.
        
        Args:
            title: Title of the meme
            image_url: URL of the meme image
            band_name: Name of the band for the meme
        """
        # Check if AI generator is available for custom text generation
        if self.ai_generator and self.ai_generator.is_api_key_configured():
            # Use AI to generate band-themed meme text
            try:
                self.ui.display_info(f"Generating {band_name}-themed meme text with AI...")
                top_text, bottom_text = self.ai_generator.generate_band_meme_text(band_name, title)
                
                # Generate the actual meme
                output_path = self.image_editor.generate_meme(
                    image_path=image_url,
                    top_text=top_text,
                    bottom_text=bottom_text
                )
                self.ui.display_generated_meme(output_path)
                
                # Ask if user wants to regenerate with different text
                regenerate = input("\nWould you like to regenerate with different text? (y/n): ").lower() == "y"
                if regenerate:
                    self._regenerate_band_meme(image_url, band_name)
                    
            except Exception as e:
                self.ui.display_error(f"Error generating band meme: {str(e)}")
                # Fall back to manual text entry
                top_text, bottom_text = self.ui.get_meme_text()
                self._generate_regular_meme(image_url, top_text, bottom_text)
        else:
            # AI not available, use manual text entry
            self.ui.display_info(f"Enter text for your {band_name}-themed meme:")
            top_text, bottom_text = self.ui.get_meme_text()
            self._generate_regular_meme(image_url, top_text, bottom_text)
    
    def _regenerate_band_meme(self, image_url: str, band_name: str):
        """
        Regenerate a band meme with different AI-generated text.
        
        Args:
            image_url: URL of the meme image
            band_name: Name of the band for the meme
        """
        if not self.ai_generator or not self.ai_generator.is_api_key_configured():
            self.ui.display_error("AI generation not available. Please configure OpenAI API key.")
            return
            
        try:
            self.ui.display_info(f"Regenerating {band_name}-themed meme text...")
            top_text, bottom_text = self.ai_generator.generate_band_meme_text(band_name)
            
            output_path = self.image_editor.generate_meme(
                image_path=image_url,
                top_text=top_text,
                bottom_text=bottom_text
            )
            self.ui.display_generated_meme(output_path)
        except Exception as e:
            self.ui.display_error(f"Error regenerating band meme: {str(e)}")
    
    def _generate_regular_meme(self, image_url: str, top_text: str, bottom_text: str):
        """
        Generate a regular meme without AI involvement.
        
        Args:
            image_url: URL of the meme image
            top_text: Top text for the meme
            bottom_text: Bottom text for the meme
        """
        try:
            output_path = self.image_editor.generate_meme(
                image_path=image_url,
                top_text=top_text,
                bottom_text=bottom_text
            )
            self.ui.display_generated_meme(output_path)
        except Exception as e:
            self.ui.display_error(f"Failed to generate meme: {str(e)}")

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
                        
                        self.ai_generator = AIMemeGenerator(
                            api_key=os.getenv("OPENAI_API_KEY"),
                            temp_dir=new_settings["temp_dir"]
                        )
                    
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
        self.ai_generator = AIMemeGenerator(
            api_key=os.getenv("OPENAI_API_KEY"),
            temp_dir=self.config_manager.get_ai_config()["temp_dir"]
        )
        
        self.ui.display_info("OpenAI API key updated successfully!")
    
    def run(self):
        """Run the main application loop."""
        self.ui.display_welcome()
        self._initialize_reddit_api()
        
        while True:
            try:
                option = self.ui.display_main_menu()
                
                if option == "Browse memes from subreddits":
                    self._browse_subreddits()
                    
                elif option == "Search for memes by keyword":
                    self._search_memes()
                    
                elif option == "Generate custom meme":
                    custom_image_path = input("\nEnter path to local image or URL: ")
                    if not custom_image_path:
                        self.ui.display_error("No image path provided.")
                        continue
                        
                    top_text, bottom_text = self.ui.get_meme_text()
                    try:
                        output_path = self.image_editor.generate_meme(
                            image_path=custom_image_path,
                            top_text=top_text,
                            bottom_text=bottom_text
                        )
                        self.ui.display_generated_meme(output_path)
                    except Exception as e:
                        self.ui.display_error(f"Failed to generate meme: {str(e)}")
                
                elif option == "View generated memes":
                    self.view_generated_memes()
                
                elif option == "Guitar/Band memes":
                    self.handle_guitar_band_memes()
                    
                elif option == "Update Reddit API credentials":
                    self._update_reddit_credentials()
                    
                elif option == "AI Meme Settings":
                    self._handle_ai_settings()
                    
                elif option == "Exit":
                    self.ui.display_info("Thank you for using the Meme Generator! Goodbye.")
                    break
                    
            except KeyboardInterrupt:
                self.ui.display_info("\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                self.ui.display_error(f"An unexpected error occurred: {str(e)}")
    
    def _handle_ai_settings(self):
        """Handle AI meme regeneration settings."""
        if not self.ai_generator or not self.ai_generator.is_api_key_configured():
            self.ui.display_info(
                "AI meme generation requires an OpenAI API key.\n"
                "Please enter your API key to enable this feature."
            )
            api_key = getpass.getpass("Enter your OpenAI API key: ")
            if not api_key:
                self.ui.display_error("No API key provided. AI features remain disabled.")
                return
                
            self.ai_generator.set_api_key(api_key)
            self.ui.display_info("OpenAI API key configured successfully!")
        
        # Now handle AI menu options
        ai_menu_option = self.ui.display_ai_menu()
        
        if ai_menu_option == "Regenerate a meme with AI":
            self._regenerate_meme_with_ai()
        elif ai_menu_option == "Configure AI settings":
            # Placeholder for future AI settings
            self.ui.display_info("AI settings configuration will be available in a future update.")
        elif ai_menu_option == "Back to main menu":
            return

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