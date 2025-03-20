"""
Command-line user interface for the meme generator.
"""
import os
import logging
import getpass
from typing import Tuple, List, Dict, Any, Optional

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemeGeneratorUI:
    """Command-line interface for meme generator."""
    
    def display_welcome(self):
        """Display welcome message and program info."""
        print("\n" + "=" * 60)
        print("REDDIT MEME GENERATOR".center(60))
        print("=" * 60)
        print("Generate custom memes from Reddit's best content")
        print("=" * 60 + "\n")
    
    def get_reddit_credentials(self) -> Tuple[str, str]:
        """
        Prompt user for Reddit API credentials.
        
        Returns:
            Tuple of (client_id, client_secret)
        """
        print("\nReddit API Credentials")
        print("-" * 30)
        print("These credentials are required to access Reddit's API.")
        print("You can get them by creating an app at: https://www.reddit.com/prefs/apps")
        print("Create a 'script' type app, and use 'http://localhost:8000' as the redirect URI.\n")
        
        client_id = input("Enter your Reddit Client ID: ").strip()
        # Using regular input instead of getpass to ensure compatibility
        client_secret = input("Enter your Reddit Client Secret: ").strip()
        
        return client_id, client_secret
    
    def display_main_menu(self) -> int:
        """
        Display main menu and get user choice.
        
        Returns:
            User's menu choice as int
        """
        print("\nMain Menu")
        print("-" * 30)
        print("1. Browse Popular Meme Subreddits")
        print("2. Search for Memes by Keyword")
        print("3. Generate Custom Meme")
        print("4. View Generated Memes")
        print("5. Update Reddit API Credentials")
        print("6. AI Meme Regeneration")
        print("7. Exit")
        
        while True:
            try:
                choice = int(input("\nEnter your choice (1-7): "))
                if 1 <= choice <= 7:
                    return choice
                print("Invalid choice. Please enter a number between 1 and 7.")
            except ValueError:
                print("Please enter a valid number.")
    
    def select_subreddit(self, subreddits: List[Tuple[str, str, int]]) -> Optional[str]:
        """
        Display list of subreddits and get user selection.
        
        Args:
            subreddits: List of (subreddit_name, description, subscriber_count) tuples
            
        Returns:
            Selected subreddit name or None to go back
        """
        print("\nPopular Meme Subreddits")
        print("-" * 60)
        
        for i, (name, desc, subs) in enumerate(subreddits, 1):
            sub_count = f"{subs:,}" if subs > 0 else "N/A"
            print(f"{i}. r/{name} - {sub_count} subscribers")
            if desc:
                print(f"   {desc}")
            print()
        
        print("0. Back to main menu")
        
        while True:
            try:
                choice = int(input("\nSelect a subreddit (0 to go back): "))
                if choice == 0:
                    return None
                if 1 <= choice <= len(subreddits):
                    return subreddits[choice-1][0]
                print(f"Invalid choice. Please enter a number between 0 and {len(subreddits)}.")
            except ValueError:
                print("Please enter a valid number.")
    
    def select_category(self, categories: List[str]) -> Optional[str]:
        """
        Display list of categories and get user selection.
        
        Args:
            categories: List of category names
            
        Returns:
            Selected category or None to go back
        """
        print("\nBrowse Category")
        print("-" * 30)
        
        for i, category in enumerate(categories, 1):
            print(f"{i}. {category.capitalize()}")
        
        print("0. Back")
        
        while True:
            try:
                choice = int(input("\nSelect a category (0 to go back): "))
                if choice == 0:
                    return None
                if 1 <= choice <= len(categories):
                    return categories[choice-1]
                print(f"Invalid choice. Please enter a number between 0 and {len(categories)}.")
            except ValueError:
                print("Please enter a valid number.")
    
    def get_search_keyword(self) -> Optional[str]:
        """
        Prompt user for search keyword.
        
        Returns:
            Search keyword or None to cancel
        """
        print("\nSearch for Memes")
        print("-" * 30)
        print("Enter a keyword to search for memes (empty to go back)")
        
        keyword = input("\nSearch keyword: ").strip()
        return keyword if keyword else None
    
    def select_meme(self, memes: List[Tuple[str, str, int, str]]) -> Optional[Tuple[str, str]]:
        """
        Display list of memes and get user selection.
        
        Args:
            memes: List of (title, image_url, score, identifier) tuples
            
        Returns:
            Tuple of (title, image_url) for selected meme or None to go back
        """
        if not memes:
            print("\nNo memes found matching your criteria.")
            input("Press Enter to continue...")
            return None
        
        print("\nSelect a Meme")
        print("-" * 60)
        
        for i, (title, url, score, ident) in enumerate(memes, 1):
            title_short = (title[:57] + "...") if len(title) > 60 else title
            print(f"{i}. {title_short}")
            print(f"   Score: {score}, URL: {url[:40]}...")
            print()
        
        print("0. Back")
        
        while True:
            try:
                choice = int(input("\nSelect a meme (0 to go back): "))
                if choice == 0:
                    return None
                if 1 <= choice <= len(memes):
                    selected = memes[choice-1]
                    return (selected[0], selected[1])
                print(f"Invalid choice. Please enter a number between 0 and {len(memes)}.")
            except ValueError:
                print("Please enter a valid number.")
    
    def get_meme_text(self) -> Tuple[str, str]:
        """
        Prompt user for top and bottom text for a meme.
        
        Returns:
            Tuple of (top_text, bottom_text)
        """
        print("\nMeme Text")
        print("-" * 30)
        print("Enter text for the top and bottom of your meme.")
        print("Leave empty if you don't want text in that position.")
        
        top_text = input("\nTop text: ").strip()
        bottom_text = input("Bottom text: ").strip()
        
        return top_text, bottom_text
    
    def display_generated_meme(self, meme_path: Optional[str]):
        """
        Display information about a generated meme.
        
        Args:
            meme_path: Path to the generated meme or None if generation failed
        """
        if meme_path and os.path.exists(meme_path):
            print("\nMeme Generated Successfully!")
            print("-" * 30)
            print(f"Saved to: {meme_path}")
            
            # Try to open the meme with the default image viewer
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(meme_path)
                elif os.name == 'posix':  # macOS and Linux
                    import subprocess
                    if os.uname().sysname == 'Darwin':  # macOS
                        subprocess.run(['open', meme_path], check=True)
                    else:  # Linux
                        subprocess.run(['xdg-open', meme_path], check=True)
                
                print("The meme has been opened in your default image viewer.")
            except Exception as e:
                print(f"Could not open the image automatically: {e}")
                print("Please open it manually from the path above.")
        else:
            print("\nMeme Generation Failed")
            print("-" * 30)
            print("There was an error generating your meme.")
            print("Please try again with a different image or text.")
        
        input("\nPress Enter to continue...")
    
    def browse_generated_memes(self, meme_dir: str) -> Optional[str]:
        """
        Display list of generated memes and allow user to select one.
        
        Args:
            meme_dir: Directory containing generated memes
            
        Returns:
            Selected meme path or None if no selection
        """
        if not os.path.exists(meme_dir):
            print("\nNo memes have been generated yet.")
            input("Press Enter to continue...")
            return None
        
        # Get list of image files in the directory
        image_files = [f for f in os.listdir(meme_dir) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        
        if not image_files:
            print("\nNo meme images found in the output directory.")
            input("Press Enter to continue...")
            return None
        
        print("\nGenerated Memes")
        print("-" * 30)
        
        # Sort by creation time, newest first
        image_files.sort(key=lambda x: os.path.getctime(os.path.join(meme_dir, x)), reverse=True)
        
        for i, img_file in enumerate(image_files, 1):
            created = os.path.getctime(os.path.join(meme_dir, img_file))
            size_kb = os.path.getsize(os.path.join(meme_dir, img_file)) / 1024
            print(f"{i}. {img_file} ({size_kb:.1f} KB)")
        
        print("0. Back")
        
        while True:
            try:
                choice = int(input("\nSelect a meme to view (0 to go back): "))
                if choice == 0:
                    return None
                if 1 <= choice <= len(image_files):
                    return os.path.join(meme_dir, image_files[choice-1])
                print(f"Invalid choice. Please enter a number between 0 and {len(image_files)}.")
            except ValueError:
                print("Please enter a valid number.")
    
    def display_error(self, message: str):
        """Display an error message."""
        print("\nERROR")
        print("-" * 30)
        print(message)
        input("\nPress Enter to continue...")
    
    def display_info(self, message: str):
        """Display an informational message."""
        print("\nINFO")
        print("-" * 30)
        print(message)
        input("\nPress Enter to continue...")
    
    def get_openai_api_key(self) -> str:
        """
        Prompt user for OpenAI API key.
        
        Returns:
            OpenAI API key
        """
        print("\nOpenAI API Key")
        print("-" * 30)
        print("An OpenAI API key is required for AI-powered meme generation.")
        print("You can get one at: https://platform.openai.com/api-keys")
        print("This will be stored in your .env file, not in config.json")
        print("Leave empty to cancel.")
        
        api_key = input("\nEnter your OpenAI API key: ").strip()
        return api_key
    
    def display_ai_menu(self) -> int:
        """
        Display AI meme generation menu and get user choice.
        
        Returns:
            User's menu choice as int
        """
        print("\nAI Meme Regeneration")
        print("-" * 30)
        print("1. Regenerate Existing Meme with AI")
        print("2. Update OpenAI API Key")
        print("3. Configure AI Settings")
        print("4. Back to Main Menu")
        
        while True:
            try:
                choice = int(input("\nEnter your choice (1-4): "))
                if 1 <= choice <= 4:
                    return choice
                print("Invalid choice. Please enter a number between 1 and 4.")
            except ValueError:
                print("Please enter a valid number.")
    
    def configure_ai_settings(self, current_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure AI settings.
        
        Args:
            current_settings: Current AI settings
            
        Returns:
            Updated settings dictionary
        """
        print("\nAI Settings")
        print("-" * 30)
        print(f"Current status: {'Enabled' if current_settings.get('enabled', False) else 'Disabled'}")
        print(f"Model: {current_settings.get('model', 'gpt-4o')}")
        
        # Toggle enabled status
        toggle = input("\nEnable AI features? (y/n): ").strip().lower()
        enabled = toggle == 'y'
        
        # Select model
        print("\nAvailable Models:")
        print("1. GPT-4o (Best quality, requires subscription)")
        print("2. GPT-3.5 Turbo (Faster, less expensive)")
        
        model = current_settings.get('model', 'gpt-4o')
        model_choice = input("\nSelect model (1-2, Enter to keep current): ").strip()
        if model_choice == '1':
            model = 'gpt-4o'
        elif model_choice == '2':
            model = 'gpt-3.5-turbo'
        
        return {
            "enabled": enabled,
            "model": model,
            "temp_dir": current_settings.get('temp_dir', 'temp_images')
        }
    
    def display_ai_meme_result(self, original_path: str, new_path: Optional[str]):
        """
        Display information about an AI-generated meme.
        
        Args:
            original_path: Path to the original meme
            new_path: Path to the new meme or None if generation failed
        """
        if new_path and os.path.exists(new_path):
            print("\nAI Meme Generated Successfully!")
            print("-" * 30)
            print(f"Original meme: {original_path}")
            print(f"New meme saved to: {new_path}")
            
            # Try to open the meme with the default image viewer
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(new_path)
                elif os.name == 'posix':  # macOS and Linux
                    import subprocess
                    if os.uname().sysname == 'Darwin':  # macOS
                        subprocess.run(['open', new_path], check=True)
                    else:  # Linux
                        subprocess.run(['xdg-open', new_path], check=True)
                
                print("The AI-generated meme has been opened in your default image viewer.")
            except Exception as e:
                print(f"Could not open the image automatically: {e}")
                print("Please open it manually from the path above.")
        else:
            print("\nAI Meme Generation Failed")
            print("-" * 30)
            print("There was an error generating your AI meme.")
            print("Please check if your OpenAI API key is valid and try again.")
        
        input("\nPress Enter to continue...") 