# Reddit Meme Generator

A simple yet powerful tool to discover, generate, and customize memes from Reddit, now with AI-powered meme regeneration!

## Features

- **Browse Popular Meme Subreddits**: Find the best meme templates from top meme communities
- **Search for Memes by Keyword**: Discover memes matching specific topics or themes
- **Generate Custom Memes**: Add your own text to any meme template
- **View Generated Memes**: Browse and view your previously created memes
- **AI-Powered Meme Regeneration**: Use OpenAI to create new clever captions for existing memes
- **Smart Text Rendering**: Automatically sizes and wraps text to ensure readability
- **Guitar/Band themed meme generator**:
  - Browse guitar-specific subreddits
  - Generate memes with AI-created jokes about specific bands
  - Search for guitar-related content
  - Generate genre-specific memes with unique personality for each music genre
- **Music Genre Meme Generator**:
  - Create memes with genre-specific humor and cultural references
  - Supported genres include Rock, Metal, Jazz, Hip Hop, and many more
  - Each genre has a unique AI personality and style
  - Enhanced music-focused image search for relevant results
  - Smart filtering to ensure images don't already contain text
- **Enhanced Media Support**:
  - Support for multiple image formats (JPG, JPEG, PNG, GIF, BMP, WebP, TIFF, SVG)
  - Automatic format conversion for compatibility
  - Video content detection with clear user notification
  - Graceful handling of unsupported media formats
- **Advanced Image Selection**:
  - Smart filtering to avoid images that already have text
  - Search results include 20 images instead of just 10
  - Randomized results for more variety with each search
  - Higher quality selection criteria for better meme creation

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
7. **Guitar & Band Memes**: Select "Guitar/Band memes" from the main menu to:
   - Browse guitar-related subreddits
   - Search for guitar memes
   - Generate band-themed memes with custom AI humor
   - Create genre-specific memes with distinct styles

### Genre-Specific Meme Generation

The application offers specialized meme generation for different music genres:

- **60s Rock**: Nostalgic Baby Boomer style with references to Woodstock, The Beatles, Rolling Stones, etc.
- **Jazz**: Pretentious jazz aficionado personality with bebop references and intellectual humor
- **90s Rock**: Cynical Gen-X slacker tone with grunge references and ironic humor
- **Rave**: Manic enthusiasm with PLUR references and electronic music culture jokes
- **2010s Pop**: Social media-obsessed personality with references to streaming, stan culture, and current trends

Each genre has its own AI personality that crafts humor specifically tailored to the culture and stereotypes of that music scene.

### Image Search Improvements

The application now includes enhanced image searching capabilities:

- **Smart Filtering**: Automatically skips images that likely already contain text by:
  - Analyzing the image source (subreddit)
  - Checking post titles for common meme phrases
  - Identifying posts from known meme subreddits
  - Looking for indicators of quotes or text in titles
- **More Results**: Each search returns 20 images instead of just 10
- **Randomization**: Results are shuffled to ensure you get different images each time
- **Higher Quality**: Behind the scenes, searches fetch 30 images and filter out lower quality options
- **Consistent Experience**: Both genre and band searches use the same improvements
- **Music-Focused Search**: Enhanced algorithms ensure genre searches return music-related images:
  - Targeted music subreddit searching for each genre
  - Multi-stage search with fallback options to ensure relevant results
  - Intelligent query construction with music-specific keywords
  - Specialized configurations for different musical styles

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

## Recent Updates

### v1.3.1 (March 2025)
- Improved text filtering to ensure cleaner images without captions or text
- Enhanced the genre filtering to maintain music context without modifying display names
- Added more aggressive filtering for text-containing images
- Optimized search queries to find authentic music-related content

### v1.3.0 (March 2025)
- Enhanced music genre search with more accurate music-related image results
- Added more specific genre options
- Implemented smarter search algorithms with multiple fallback strategies
- Improved search queries to focus on concerts, performances, and music-related content
- Added specialized configurations for over 10 music genres

### v1.2.0 (March 2025)
- Added intelligent image filtering to avoid using images that already have text
- Increased search results from 10 to 20 images for more selection
- Implemented randomization for more varied results on repeated searches
- Enhanced image quality through better filtering of results
- Improved caption generation by analyzing both image content and selected genre/band

### Future Improvements

- Add advanced text customization options (colors, fonts, positioning)
- Support for meme templates from more sources
- Export to social media platforms
- Add GUI interface
- Support for more AI models and image generation features
- Sentiment analysis for meme categorization
- Add more music genres and cultural themes to the genre-specific generator
- Implement a meme battle feature where two genres or bands compete
- Create a collaborative mode where multiple users can contribute to a meme
- Expand video meme support for popular video formats and hosting platforms
- Add custom video thumbnail extraction for creating static memes from videos
- Integrate with other APIs for more diverse content sources
- Build a recommendation system based on user preferences
- Add accessibility features for screen readers and alternative input methods 