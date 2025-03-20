# Reddit Meme Generator

A simple yet powerful tool to discover, generate, and customize memes from Reddit, now with AI-powered meme regeneration!

## Features

- **Browse Popular Meme Subreddits**: Find the best meme templates from top meme communities
- **Search for Memes by Keyword**: Discover memes matching specific topics or themes
- **Generate Custom Memes**: Add your own text to any meme template
- **View Generated Memes**: Browse and view your previously created memes
- **AI-Powered Meme Regeneration**: Use OpenAI to create new clever captions for existing memes
- **Smart Text Rendering**: Automatically sizes and wraps text to ensure readability

## Requirements

- Python 3.7+
- Required packages:
  - praw (Reddit API wrapper)
  - Pillow (Image processing)
  - requests
  - python-dotenv (Environment variable management)
  - openai (Optional, for AI features)

## Installation

1. Clone this repository or download the source code
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy the template configuration files:
   ```
   cp config.json.example config.json
   cp .env.example .env
   ```
4. Configure your API keys (see API Setup below)
5. Run the application:
   ```
   python main.py
   ```

## API Setup

### Reddit API Setup (Required)

The application requires Reddit API credentials to function:

1. Go to [Reddit's App Preferences](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App" at the bottom
3. Fill in the following:
   - Name: `MemeGenerator` (or any name you prefer)
   - App type: Select `script`
   - Description: Optional
   - About URL: `http://localhost:8000` (this is just a placeholder)
   - Redirect URI: `http://localhost:8000` (this is also a placeholder)
4. Click "Create app"
5. Note your `client_id` (displayed under your app name) and `client_secret`
6. Add these credentials to your local `config.json` file or provide them when prompted at first launch

The application will prompt you to enter these credentials on first launch.

### OpenAI API Setup (Optional, for AI features)

To use the AI meme regeneration feature:

1. Create an account at [OpenAI](https://platform.openai.com)
2. Generate an API key from your account dashboard
3. Add your API key to the `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
4. Alternatively, in the application, select "AI Meme Regeneration" from the main menu and choose "Update OpenAI API Key"

## Security Notes

- **API Keys**: Never commit your API keys or credentials to version control
- **Configuration**: The `config.json` and `.env` files are excluded from git tracking for security
- **Templates**: Use the provided example files as templates for your local configuration

## Usage

1. **Start the Application**: Run `python main.py`
2. **Configure Reddit API**: Enter your Reddit client ID and client secret when prompted
3. **Browse or Search**: 
   - Browse subreddits to explore popular meme templates
   - Or search for specific memes by keyword
4. **Customize**: Add your own text at the top and bottom of selected memes
5. **Save and Share**: Generated memes are saved to the `generated_memes` directory
6. **AI Regeneration**: Select "AI Meme Regeneration" to create new captions for existing memes

### Text Rendering Features

- **Smart Text Sizing**: Text automatically scales to fit the image width
- **Line Wrapping**: Long text automatically wraps to multiple lines
- **Margin Control**: Text properly positioned to stay within image boundaries
- **Readable Captions**: Text includes outlines to ensure visibility against any background

## Project Structure

- `main.py` - Main application entry point
- `reddit_api.py` - Reddit API interaction module
- `image_editor.py` - Image processing and text addition
- `config_manager.py` - Handles application configuration
- `ui.py` - Command-line user interface
- `ai_meme_generator.py` - AI-powered meme caption generation
- `.env.example` - Template for environment variables
- `config.json.example` - Template for application configuration

## License

This project is open source under the MIT license.

## Disclaimer

This tool is for educational and personal use. Please respect copyright and Reddit's terms of service when using and sharing memes.

## Future Improvements

- Add advanced text customization options (colors, fonts, positioning)
- Support for meme templates from more sources
- Export to social media platforms
- Add GUI interface
- Support for more AI models and image generation features
- Sentiment analysis for meme categorization 