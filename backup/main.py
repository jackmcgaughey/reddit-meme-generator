import os
import json
import argparse
from datetime import datetime
from collections import Counter

from api import TwitterAPI
from reddit_api import RedditAPI
from web_scraper import MemeWebScraper
from image_editor import ImageEditor
from ui import select_meme, get_text, get_api_keys

def save_meme_data(memes, filename="meme_data.json"):
    """
    Save meme data to a JSON file for analysis and future use.
    
    Args:
        memes (list): List of meme data tuples
        filename (str): Output filename
    """
    output_dir = "data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filepath = os.path.join(output_dir, filename)
    
    # Convert to list of dictionaries for JSON serialization
    meme_data = []
    for meme in memes:
        # Handle different tuple formats from different sources
        if len(meme) >= 2:  # All sources provide at least (title, url)
            meme_dict = {
                "title": meme[0],
                "image_url": meme[1],
                "source": getattr(meme, "source", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }
            
            # Add engagement data if available
            if len(meme) >= 3:
                meme_dict["engagement"] = meme[2]
                
            # Add additional data if available
            if len(meme) >= 4:
                if isinstance(meme[3], str):
                    meme_dict["subreddit"] = meme[3]
                else:
                    meme_dict["additional_data"] = meme[3]
                    
            meme_data.append(meme_dict)
    
    # Save to JSON
    with open(filepath, 'w') as f:
        json.dump(meme_data, f, indent=2)
        
    print(f"Saved meme data to {filepath}")
    return filepath

def analyze_meme_trends(meme_data):
    """
    Analyze meme data to identify trends.
    
    Args:
        meme_data (list): List of meme dictionaries
        
    Returns:
        dict: Analysis results
    """
    # Count most common words in titles
    words = []
    for meme in meme_data:
        title = meme.get("title", "").lower()
        # Simple tokenization - split on spaces and remove punctuation
        words.extend([word.strip(".,!?():;\"'") for word in title.split() if len(word) > 3])
    
    # Count word frequencies
    word_counts = Counter(words)
    
    # Get top engagement
    sorted_by_engagement = sorted(
        [m for m in meme_data if "engagement" in m],
        key=lambda x: x["engagement"],
        reverse=True
    )
    
    # Get sources distribution
    sources = Counter([meme.get("source", "unknown") for meme in meme_data])
    
    return {
        "top_keywords": dict(word_counts.most_common(10)),
        "top_engagement": sorted_by_engagement[:5],
        "source_distribution": dict(sources)
    }

def fetch_memes_from_all_sources(config):
    """
    Fetch memes from all configured sources.
    
    Args:
        config (dict): Configuration with API keys and settings
        
    Returns:
        dict: Memes from all sources
    """
    all_memes = {}
    
    # Twitter memes
    if config.get("twitter", {}).get("enabled", False):
        try:
            twitter_keys = config["twitter"]
            twitter_api = TwitterAPI(
                twitter_keys["consumer_key"],
                twitter_keys["consumer_secret"],
                twitter_keys["access_token"],
                twitter_keys["access_token_secret"]
            )
            
            # Fetch memes from specific accounts
            account_memes = twitter_api.fetch_memes(config["twitter"].get("accounts", []))
            # Add source info
            account_memes = [(text, url, "twitter_account") for text, url in account_memes]
            
            # Fetch trending memes by hashtags
            trending_memes = twitter_api.fetch_trending_memes(
                hashtags=config["twitter"].get("hashtags"),
                count=config["twitter"].get("count", 50)
            )
            # Add source info
            trending_memes = [(text, url, engagement, "twitter_trending") 
                             for text, url, engagement in trending_memes]
            
            all_memes["twitter_accounts"] = account_memes
            all_memes["twitter_trending"] = trending_memes
            
            print(f"Fetched {len(account_memes)} memes from Twitter accounts")
            print(f"Fetched {len(trending_memes)} trending memes from Twitter")
            
        except Exception as e:
            print(f"Error fetching Twitter memes: {e}")
    
    # Reddit memes
    if config.get("reddit", {}).get("enabled", False):
        try:
            reddit_keys = config["reddit"]
            reddit_api = RedditAPI(
                reddit_keys["client_id"],
                reddit_keys["client_secret"],
                reddit_keys["user_agent"]
            )
            
            # Fetch trending memes from subreddits
            reddit_memes = reddit_api.fetch_trending_memes(
                subreddits=config["reddit"].get("subreddits"),
                time_filter=config["reddit"].get("time_filter", "day"),
                limit=config["reddit"].get("limit", 100)
            )
            
            # Fetch category-specific memes if categories provided
            category_memes = {}
            for category in config["reddit"].get("categories", []):
                category_results = reddit_api.fetch_memes_by_category(
                    category,
                    limit=config["reddit"].get("category_limit", 50)
                )
                category_memes[category] = category_results
                print(f"Fetched {len(category_results)} '{category}' memes from Reddit")
            
            all_memes["reddit_trending"] = reddit_memes
            all_memes["reddit_categories"] = category_memes
            
            print(f"Fetched {len(reddit_memes)} trending memes from Reddit")
            
        except Exception as e:
            print(f"Error fetching Reddit memes: {e}")
    
    # Web scraping
    if config.get("web_scraping", {}).get("enabled", False):
        try:
            scraper = MemeWebScraper()
            
            # Fetch from all configured sources
            sources = config["web_scraping"].get("sources", ["imgur", "knowyourmeme", "9gag"])
            limit = config["web_scraping"].get("limit_per_source", 20)
            
            scraped_memes = scraper.get_trending_memes(sources, limit)
            all_memes["scraped"] = scraped_memes
            
            for source, memes in scraped_memes.items():
                print(f"Fetched {len(memes)} memes from {source}")
                
        except Exception as e:
            print(f"Error scraping memes: {e}")
    
    return all_memes

def load_config(config_path="config.json"):
    """
    Load configuration from JSON file or create default if it doesn't exist.
    
    Args:
        config_path (str): Path to config file
        
    Returns:
        dict: Configuration dictionary
    """
    default_config = {
        "twitter": {
            "enabled": True,
            "consumer_key": "",
            "consumer_secret": "",
            "access_token": "",
            "access_token_secret": "",
            "accounts": ["9GAG", "DankMemes", "Memeulous"],
            "hashtags": ["memes", "dankmemes", "funny"],
            "count": 50
        },
        "reddit": {
            "enabled": True,
            "client_id": "",
            "client_secret": "",
            "user_agent": "MemeGenerator/1.0",
            "subreddits": ["memes", "dankmemes", "wholesomememes"],
            "time_filter": "day",
            "limit": 100,
            "categories": ["cat", "dog", "programming", "gaming"],
            "category_limit": 50
        },
        "web_scraping": {
            "enabled": True,
            "sources": ["imgur", "knowyourmeme", "9gag"],
            "limit_per_source": 20
        },
        "image_editor": {
            "font_path": "arial.ttf",
            "output_dir": "generated_memes"
        }
    }
    
    # Create config file if it doesn't exist
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"Created default configuration file at {config_path}")
        print("Please update the configuration with your API keys before running again.")
        return default_config
    
    # Load existing config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return config

def main():
    """Main function to run the meme generator."""
    parser = argparse.ArgumentParser(description="Meme Generator")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    parser.add_argument("--mode", choices=["interactive", "fetch", "analyze", "generate"], 
                       default="interactive", help="Operation mode")
    parser.add_argument("--category", help="Meme category for category-specific operations")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Check if config has API keys
    missing_keys = False
    if config["twitter"]["enabled"]:
        for key in ["consumer_key", "consumer_secret", "access_token", "access_token_secret"]:
            if not config["twitter"][key]:
                missing_keys = True
                
    if config["reddit"]["enabled"]:
        for key in ["client_id", "client_secret"]:
            if not config["reddit"][key]:
                missing_keys = True
    
    if missing_keys and args.mode != "interactive":
        print("API keys are missing in the configuration file.")
        print("Please update the configuration or run in interactive mode to input keys.")
        return
        
    # Interactive mode
    if args.mode == "interactive":
        # If API keys are missing, get them from user
        if config["twitter"]["enabled"] and not all([
            config["twitter"]["consumer_key"],
            config["twitter"]["consumer_secret"],
            config["twitter"]["access_token"],
            config["twitter"]["access_token_secret"]
        ]):
            print("Twitter API keys are missing. Please enter them:")
            consumer_key, consumer_secret, access_token, access_token_secret = get_api_keys()
            config["twitter"]["consumer_key"] = consumer_key
            config["twitter"]["consumer_secret"] = consumer_secret
            config["twitter"]["access_token"] = access_token
            config["twitter"]["access_token_secret"] = access_token_secret
        
        # Initialize the image editor
        image_editor = ImageEditor(font_path=config["image_editor"]["font_path"])
        
        # Fetch memes from all sources
        print("Fetching memes from all configured sources...")
        all_memes = fetch_memes_from_all_sources(config)
        
        # Flatten memes for selection
        # Combine different formats into a standard format
        flat_memes = []
        
        # Twitter account memes
        if "twitter_accounts" in all_memes:
            flat_memes.extend([(text, url) for text, url, _ in all_memes["twitter_accounts"]])
            
        # Twitter trending memes
        if "twitter_trending" in all_memes:
            flat_memes.extend([(text, url) for text, url, _, _ in all_memes["twitter_trending"]])
            
        # Reddit trending memes
        if "reddit_trending" in all_memes:
            flat_memes.extend([(title, url) for title, url, _, _ in all_memes["reddit_trending"]])
            
        # Scraped memes
        if "scraped" in all_memes:
            for source, memes in all_memes["scraped"].items():
                if source == "imgur":
                    flat_memes.extend([(title, url) for title, url, _ in memes])
                elif source == "knowyourmeme":
                    flat_memes.extend([(title, url) for title, url, _, _ in memes])
                elif source == "9gag":
                    flat_memes.extend([(title, url) for title, url, _ in memes])
        
        if not flat_memes:
            print("No memes found. Please check your API keys or try again later.")
            return
        
        # User selects a meme
        print(f"Found {len(flat_memes)} memes. Select one:")
        selected_meme = select_meme(flat_memes)
        
        # Get custom text
        top_text, bottom_text = get_text()
        
        # Generate and save the meme
        print("Generating custom meme...")
        output_dir = config["image_editor"].get("output_dir", "generated_memes")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        custom_meme_path = image_editor.add_text_to_image(selected_meme, top_text, bottom_text, output_dir=output_dir)
        if custom_meme_path:
            print(f"Custom meme saved as {custom_meme_path}")
        else:
            print("Failed to generate custom meme.")
            
    # Fetch mode - just fetch and save meme data
    elif args.mode == "fetch":
        print("Fetching memes from all configured sources...")
        all_memes = fetch_memes_from_all_sources(config)
        
        # Flatten and save all memes to a dataset
        flat_memes = []
        
        # Process each source and format consistently
        for source_type, memes in all_memes.items():
            if isinstance(memes, list):
                for meme in memes:
                    # Add source type to each meme tuple
                    meme_with_source = meme + (source_type,)
                    flat_memes.append(meme_with_source)
            elif isinstance(memes, dict):
                for source, source_memes in memes.items():
                    for meme in source_memes:
                        meme_with_source = meme + (f"{source_type}_{source}",)
                        flat_memes.append(meme_with_source)
        
        # Save meme data
        output_file = args.output or f"meme_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_meme_data(flat_memes, output_file)
        
    # Analyze mode - analyze the meme dataset
    elif args.mode == "analyze":
        # Load meme data
        data_file = args.output or "meme_data.json"
        if not os.path.exists(os.path.join("data", data_file)):
            print(f"Meme data file {data_file} not found. Fetching new data...")
            all_memes = fetch_memes_from_all_sources(config)
            flat_memes = []
            for source_type, memes in all_memes.items():
                if isinstance(memes, list):
                    flat_memes.extend(memes)
                elif isinstance(memes, dict):
                    for source, source_memes in memes.items():
                        flat_memes.extend(source_memes)
            
            data_file = save_meme_data(flat_memes)
        
        # Load and analyze
        with open(os.path.join("data", data_file), 'r') as f:
            meme_data = json.load(f)
        
        analysis = analyze_meme_trends(meme_data)
        
        # Print analysis results
        print("\n=== MEME TREND ANALYSIS ===")
        print("\nTop Keywords:")
        for word, count in analysis["top_keywords"].items():
            print(f"  - {word}: {count}")
            
        print("\nTop Memes by Engagement:")
        for i, meme in enumerate(analysis["top_engagement"], 1):
            print(f"  {i}. \"{meme['title']}\" - Engagement: {meme['engagement']}")
            
        print("\nSource Distribution:")
        for source, count in analysis["source_distribution"].items():
            print(f"  - {source}: {count}")
            
    # Generate mode - generate multiple memes
    elif args.mode == "generate":
        if not args.category:
            print("Please specify a meme category with --category")
            return
            
        # Initialize the image editor
        image_editor = ImageEditor(font_path=config["image_editor"]["font_path"])
        
        # Fetch memes with the specified category
        print(f"Fetching '{args.category}' memes...")
        if config["reddit"]["enabled"]:
            try:
                reddit_api = RedditAPI(
                    config["reddit"]["client_id"],
                    config["reddit"]["client_secret"],
                    config["reddit"]["user_agent"]
                )
                
                category_memes = reddit_api.fetch_memes_by_category(
                    args.category,
                    limit=config["reddit"].get("category_limit", 50)
                )
                
                if not category_memes:
                    print(f"No '{args.category}' memes found on Reddit.")
                    return
                    
                # Generate a batch of memes
                output_dir = config["image_editor"].get("output_dir", "generated_memes")
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                # Generate up to 5 memes
                generated_count = 0
                for title, url, score, subreddit in category_memes[:5]:
                    # Generate meme text based on title
                    words = title.split()
                    if len(words) < 6:
                        top_text = title
                        bottom_text = args.category.upper()
                    else:
                        mid_point = len(words) // 2
                        top_text = " ".join(words[:mid_point])
                        bottom_text = " ".join(words[mid_point:])
                    
                    # Generate the meme
                    custom_meme_path = image_editor.add_text_to_image(
                        url, top_text, bottom_text, 
                        output_dir=os.path.join(output_dir, args.category)
                    )
                    
                    if custom_meme_path:
                        print(f"Generated meme: {custom_meme_path}")
                        generated_count += 1
                
                print(f"Generated {generated_count} '{args.category}' memes.")
                
            except Exception as e:
                print(f"Error generating '{args.category}' memes: {e}")
        else:
            print("Reddit API is not enabled in configuration.")

if __name__ == "__main__":
    main()