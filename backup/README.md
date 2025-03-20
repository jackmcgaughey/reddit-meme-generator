# Advanced Meme Generator System

This project is a comprehensive meme generator system that can:
1. Discover trending memes from multiple sources
2. Analyze meme trends and popularity
3. Generate custom memes with your own text
4. Create categorized meme collections

## Features

- **Multi-Source Meme Discovery**: Automatically finds popular memes from:
  - Twitter/X (user accounts and trending hashtags)
  - Reddit (subreddits and keyword search)
  - Web Scraping (Imgur, 9GAG, Know Your Meme)

- **Meme Trend Analysis**: 
  - Identify trending keywords in meme content
  - Track engagement metrics
  - Compare popularity across platforms

- **Custom Meme Generation**:
  - Add custom text to any meme template
  - Support for top and bottom text formatting
  - Batch generation capabilities

- **Category-Specific Memes**:
  - Generate memes by category (e.g., cats, dogs, programming)
  - Build thematic meme collections

## Setup

### Requirements

- Python 3.8+
- Required packages (install using `pip install -r requirements.txt`)

### API Keys

The system can use the following API keys (optional, based on which sources you enable):

- Twitter/X API:
  - Consumer Key
  - Consumer Secret
  - Access Token
  - Access Token Secret

- Reddit API:
  - Client ID
  - Client Secret

### Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd memegenerator
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application in interactive mode:
   ```
   python main.py
   ```

## Usage

The application can be run in several modes:

### Interactive Mode (Default)

```
python main.py
```

This mode will:
1. Prompt for any missing API keys
2. Fetch memes from all configured sources
3. Let you select a meme template
4. Prompt for top and bottom text
5. Generate and save the custom meme

### Fetch Mode

```
python main.py --mode fetch --output meme_dataset.json
```

This mode will:
1. Fetch memes from all configured sources
2. Save all meme data to a JSON file for later analysis

### Analyze Mode

```
python main.py --mode analyze --output meme_dataset.json
```

This mode will:
1. Load meme data from the specified file (or fetch new data if the file doesn't exist)
2. Analyze trends, popular keywords, and engagement metrics
3. Display analysis results

### Generate Mode

```
python main.py --mode generate --category programming
```

This mode will:
1. Fetch memes related to the specified category (e.g., "programming")
2. Automatically generate a batch of memes with appropriate text
3. Save the generated memes to the output directory

## Configuration

The application uses a JSON configuration file (`config.json`) that is created automatically on first run. You can edit this file to:

- Enable/disable specific meme sources
- Configure API keys
- Specify default meme accounts, subreddits, and hashtags to follow
- Set output directories and other preferences

## Building a Viral Instagram Meme Page

This system is designed to help you build a viral Instagram meme page by:

1. **Discovering Trending Content**: Find what's popular right now across multiple platforms
2. **Content Customization**: Add your own voice and branding to memes
3. **Niche Targeting**: Generate category-specific memes for targeted audiences
4. **Content Scheduling**: Batch generate memes for consistent posting
5. **Trend Analysis**: Understand what types of memes get the most engagement

## Future Enhancements

- AI-powered text generation for memes
- Automated Instagram posting
- Advanced image manipulation (not just text overlays)
- Style transfer for unique meme aesthetics
- Video meme support

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Always respect copyright and platform terms of service when using and sharing meme content. Be aware of API usage limits and scraping policies of the websites used.