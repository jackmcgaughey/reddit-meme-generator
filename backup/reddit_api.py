import praw
import requests
import prawcore.exceptions
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedditAPI:
    """Handles authentication and meme fetching from Reddit API."""
    
    def __init__(self, client_id, client_secret, user_agent):
        """
        Initialize Reddit API client.
        
        Args:
            client_id (str): Reddit API client ID
            client_secret (str): Reddit API client secret
            user_agent (str): User agent string for API requests
        """
        logger.info(f"Initializing Reddit API with client_id: {client_id[:4]}*** and user_agent: {user_agent}")
        
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        # Verify authentication
        try:
            logger.info(f"Verifying Reddit API authentication...")
            username = self.reddit.user.me()
            logger.info(f"Authenticated as: {username if username else 'Read-only mode'}")
        except prawcore.exceptions.OAuthException as e:
            logger.error(f"Reddit authentication error: {e}")
            if "401" in str(e):
                logger.error("401 Unauthorized: Your Reddit API credentials are invalid")
                logger.error("Please check your client_id and client_secret")
            raise
        except Exception as e:
            logger.error(f"Reddit authentication unexpected error: {e}")
            logger.error("This is likely a read-only instance (normal for script-only access)")
        
    def fetch_trending_memes(self, subreddits=None, time_filter='day', limit=100):
        """
        Fetch trending memes from specified subreddits.
        
        Args:
            subreddits (list): List of subreddit names (without 'r/'). 
                             If None, uses default meme subreddits.
            time_filter (str): One of 'hour', 'day', 'week', 'month', 'year', 'all'
            limit (int): Maximum number of posts to fetch per subreddit
            
        Returns:
            list: List of tuples (title, image_url, score, subreddit_name)
        """
        if subreddits is None:
            # Popular meme subreddits
            subreddits = [
                'memes', 'dankmemes', 'wholesomememes', 'MemeEconomy',
                'AdviceAnimals', 'PrequelMemes', 'ProgrammerHumor', 'trippinthroughtime'
            ]
            
        trending_memes = []
        
        for subreddit_name in subreddits:
            try:
                logger.info(f"Fetching memes from r/{subreddit_name}...")
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get top posts within time_filter
                for post in subreddit.top(time_filter=time_filter, limit=limit):
                    # Check if post contains an image
                    if hasattr(post, 'url') and any(post.url.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                        # Check if the URL is valid by making a HEAD request
                        try:
                            response = requests.head(post.url, timeout=3)
                            if response.status_code == 200:
                                trending_memes.append((post.title, post.url, post.score, subreddit_name))
                        except requests.RequestException:
                            # Skip invalid URLs
                            continue
                
                logger.info(f"Found {len(trending_memes)} memes from r/{subreddit_name}")
                    
            except prawcore.exceptions.OAuthException as e:
                logger.error(f"Reddit OAuth error for r/{subreddit_name}: {e}")
                if "401" in str(e):
                    logger.error("401 Unauthorized: Your Reddit API credentials are invalid")
                    logger.error("Please check your client_id and client_secret")
                raise
            except prawcore.exceptions.Forbidden:
                logger.error(f"Access forbidden for r/{subreddit_name} - this subreddit may be private")
            except prawcore.exceptions.NotFound:
                logger.error(f"Subreddit r/{subreddit_name} not found")
            except prawcore.exceptions.ServerError:
                logger.error(f"Reddit server error when accessing r/{subreddit_name}")
            except prawcore.exceptions.TooManyRequests:
                logger.error(f"Rate limited when accessing r/{subreddit_name}")
                logger.error("Consider reducing the frequency of requests or limit parameter")
            except Exception as e:
                logger.error(f"Error fetching memes from r/{subreddit_name}: {e}")
                
        # Sort by score (highest first)
        trending_memes.sort(key=lambda x: x[2], reverse=True)
        return trending_memes
        
    def fetch_memes_by_category(self, category_keyword, limit=100):
        """
        Search for memes across Reddit by category keyword.
        
        Args:
            category_keyword (str): Keyword to search for (e.g., 'cat', 'dog', 'programming')
            limit (int): Maximum number of posts to fetch
            
        Returns:
            list: List of tuples (title, image_url, score, subreddit_name)
        """
        memes = []
        
        try:
            logger.info(f"Searching for '{category_keyword}' memes across Reddit...")
            # Search for posts containing the keyword
            search_results = self.reddit.subreddit('all').search(
                f"{category_keyword} meme", 
                sort='top', 
                time_filter='month',
                limit=limit
            )
            
            for post in search_results:
                # Check if post contains an image
                if hasattr(post, 'url') and any(post.url.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                    # Verify the URL is accessible
                    try:
                        response = requests.head(post.url, timeout=3)
                        if response.status_code == 200:
                            memes.append((post.title, post.url, post.score, post.subreddit.display_name))
                    except requests.RequestException:
                        continue
            
            logger.info(f"Found {len(memes)} '{category_keyword}' memes")
                    
        except prawcore.exceptions.OAuthException as e:
            logger.error(f"Reddit OAuth error searching for '{category_keyword}': {e}")
            if "401" in str(e):
                logger.error("401 Unauthorized: Your Reddit API credentials are invalid")
                logger.error("Please check your client_id and client_secret")
            raise
        except Exception as e:
            logger.error(f"Error searching for '{category_keyword}' memes: {e}")
            
        return memes 