# Reddit Meme Generator

A simple yet powerful tool to discover, generate, and customize memes from Reddit.

## Features

- **Browse Popular Meme Subreddits**: Find the best meme templates from top meme communities
- **Search for Memes by Keyword**: Discover memes matching specific topics or themes
- **Generate Custom Memes**: Add your own text to any meme template
- **View Generated Memes**: Browse and view your previously created memes

## Requirements

- Python 3.7+
- Required packages:
  - praw (Reddit API wrapper)
  - Pillow (Image processing)
  - requests

## Installation

1. Clone this repository or download the source code
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python main.py
   ```

## Reddit API Setup

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

The application will prompt you to enter these credentials on first launch.

## Usage

1. **Start the Application**: Run `python main.py`
2. **Configure Reddit API**: Enter your Reddit client ID and client secret when prompted
3. **Browse or Search**: 
   - Browse subreddits to explore popular meme templates
   - Or search for specific memes by keyword
4. **Customize**: Add your own text at the top and bottom of selected memes
5. **Save and Share**: Generated memes are saved to the `generated_memes` directory

## Project Structure

- `main.py` - Main application entry point
- `reddit_api.py` - Reddit API interaction module
- `image_editor.py` - Image processing and text addition
- `config_manager.py` - Handles application configuration
- `ui.py` - Command-line user interface

## License

This project is open source under the MIT license.

## Disclaimer

This tool is for educational and personal use. Please respect copyright and Reddit's terms of service when using and sharing memes.

## Future Improvements

- Add advanced text customization options (colors, fonts, positioning)
- Support for meme templates from more sources
- Export to social media platforms
- Add GUI interface 