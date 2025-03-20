"""
Reddit API module for fetching memes.
"""
import praw
import logging
import requests
from typing import List, Tuple, Optional

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedditMemeAPI:
    """Class to handle Reddit API interactions for meme fetching."""
    
    def __init__(self, client_id: str, client_secret: str, user_agent: str = "MemeGenerator/1.0"):
        """
        Initialize the Reddit API client.
        
        Args:
            client_id: Your Reddit application client ID
            client_secret: Your Reddit application client secret
            user_agent: User agent for API requests
        """
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        logger.info("Reddit API client initialized")
    
    def fetch_memes_from_subreddit(
        self, 
        subreddit_name: str,
        limit: int = 25, 
        category: str = "hot"
    ) -> List[Tuple[str, str, int, str]]:
        """
        Fetch memes from a specific subreddit.
        
        Args:
            subreddit_name: Name of the subreddit to fetch from
            limit: Maximum number of posts to fetch
            category: One of 'hot', 'new', 'top', 'rising'
            
        Returns:
            List of tuples: (title, image_url, score, post_id)
        """
        memes = []
        logger.info(f"Fetching up to {limit} memes from r/{subreddit_name} ({category})")
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get posts based on category
            if category == "hot":
                posts = subreddit.hot(limit=limit)
            elif category == "new":
                posts = subreddit.new(limit=limit)
            elif category == "top":
                posts = subreddit.top(limit=limit)
            elif category == "rising":
                posts = subreddit.rising(limit=limit)
            else:
                logger.error(f"Invalid category: {category}")
                return memes
            
            # Process each post
            for post in posts:
                # Skip stickied posts
                if post.stickied:
                    continue
                    
                # Check if post has an image
                if hasattr(post, 'url') and self._is_image_url(post.url):
                    # Verify the URL is accessible
                    if self._validate_image_url(post.url):
                        memes.append((post.title, post.url, post.score, post.id))
            
            logger.info(f"Found {len(memes)} memes in r/{subreddit_name}")
            return memes
            
        except Exception as e:
            logger.error(f"Error fetching from r/{subreddit_name}: {e}")
            return memes
    
    def search_memes_by_keyword(
        self, 
        keyword: str,
        limit: int = 25,
        time_filter: str = "month"
    ) -> List[Tuple[str, str, int, str, str]]:
        """
        Search for memes across Reddit by keyword.
        
        Args:
            keyword: Search term
            limit: Maximum number of results
            time_filter: One of 'day', 'week', 'month', 'year', 'all'
            
        Returns:
            List of tuples: (title, image_url, score, subreddit_name, post_id)
        """
        memes = []
        logger.info(f"Searching for '{keyword}' memes across Reddit")
        
        try:
            # Search for posts containing the keyword
            search_query = f"{keyword} meme"
            search_results = self.reddit.subreddit('all').search(
                query=search_query,
                sort='relevance',
                time_filter=time_filter,
                limit=limit
            )
            
            for post in search_results:
                if hasattr(post, 'url') and self._is_image_url(post.url):
                    if self._validate_image_url(post.url):
                        memes.append((
                            post.title, 
                            post.url, 
                            post.score, 
                            post.subreddit.display_name,
                            post.id
                        ))
            
            logger.info(f"Found {len(memes)} memes matching '{keyword}'")
            return memes
            
        except Exception as e:
            logger.error(f"Error searching for '{keyword}' memes: {e}")
            return memes
    
    def search_memes(self, keyword: str, limit: int = 10) -> List[Tuple[str, str, int, str, str]]:
        """
        Search for memes based on keyword.
        
        Args:
            keyword: Search term
            limit: Maximum number of results to return
            
        Returns:
            List of tuples (title, image_url, score, subreddit, post_id)
        """
        if not self.reddit:
            self._check_credentials()
            
        results = []
        
        try:
            logger.info(f"Searching for '{keyword}' across Reddit")
            
            # Search across all of Reddit
            search_results = self.reddit.subreddit("all").search(
                f"{keyword} site:i.redd.it OR site:imgur.com", 
                sort="relevance", 
                time_filter="month", 
                limit=limit * 2  # Get more than we need to filter non-images
            )
            
            for post in search_results:
                if not hasattr(post, 'url'):
                    continue
                    
                # Check if it's an image URL
                url = post.url
                if not self._is_image_url(url):
                    continue
                    
                results.append((
                    post.title,
                    url,
                    post.score,
                    str(post.subreddit),
                    post.id
                ))
                
                if len(results) >= limit:
                    break
            
            logger.info(f"Found {len(results)} memes for keyword '{keyword}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching for memes: {str(e)}")
            return []
    
    def search_guitar_memes(self, keyword: str = "guitar", limit: int = 10) -> List[Tuple[str, str, int, str, str]]:
        """
        Search for guitar-related memes based on keyword.
        
        Args:
            keyword: Guitar-related search term (default: "guitar")
            limit: Maximum number of results to return
            
        Returns:
            List of tuples (title, image_url, score, subreddit, post_id)
        """
        if not self.reddit:
            self._check_credentials()
            
        results = []
        guitar_subreddits = [
            "guitar", 
            "guitarcirclejerk", 
            "guitars", 
            "guitarplaying", 
            "guitarmemes",
            "guitarpedals", 
            "acousticguitar", 
            "bassguitar",
            "guitarlessons"
        ]
        
        subreddit_string = "+".join(guitar_subreddits)
        enhanced_keyword = f"{keyword}"
        
        try:
            logger.info(f"Searching for '{enhanced_keyword}' in guitar subreddits")
            
            # Search across all guitar subreddits
            search_results = self.reddit.subreddit(subreddit_string).search(
                f"{enhanced_keyword} site:i.redd.it OR site:imgur.com", 
                sort="relevance", 
                time_filter="year",  # Extend time to find more guitar memes
                limit=limit * 3  # Get more than we need to filter non-images
            )
            
            for post in search_results:
                if not hasattr(post, 'url'):
                    continue
                    
                # Check if it's an image URL
                url = post.url
                if not self._is_image_url(url):
                    continue
                    
                results.append((
                    post.title,
                    url,
                    post.score,
                    str(post.subreddit),
                    post.id
                ))
                
                if len(results) >= limit:
                    break
            
            # If we don't have enough results, try another search strategy
            if len(results) < limit:
                # Try a broader search with guitar-related terms
                broader_terms = ["fender", "gibson", "stratocaster", "les paul", 
                                "amp", "pedal", "musician", "band", "rock"]
                
                for term in broader_terms:
                    if len(results) >= limit:
                        break
                        
                    additional_results = self.reddit.subreddit("all").search(
                        f"{term} {keyword} site:i.redd.it OR site:imgur.com", 
                        sort="relevance", 
                        time_filter="year",
                        limit=(limit - len(results)) * 2
                    )
                    
                    for post in additional_results:
                        if not hasattr(post, 'url'):
                            continue
                            
                        # Check if it's an image URL
                        url = post.url
                        if not self._is_image_url(url):
                            continue
                            
                        # Check for duplicates
                        if any(result[4] == post.id for result in results):
                            continue
                            
                        results.append((
                            post.title,
                            url,
                            post.score,
                            str(post.subreddit),
                            post.id
                        ))
                        
                        if len(results) >= limit:
                            break
            
            logger.info(f"Found {len(results)} guitar memes for keyword '{keyword}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching for guitar memes: {str(e)}")
            return []
    
    def get_trending_meme_subreddits(self, limit: int = 10) -> List[Tuple[str, str, int]]:
        """
        Get a list of trending meme-related subreddits.
        
        Args:
            limit: Maximum number of subreddits to return
            
        Returns:
            List of tuples: (subreddit_name, description, subscriber_count)
        """
        trending_subreddits = []
        meme_keywords = ['meme', 'memes', 'funny', 'dank']
        
        try:
            # Get popular subreddits
            for sr in self.reddit.subreddits.popular(limit=100):
                # Check if it's meme-related by name or description
                name_lower = sr.display_name.lower()
                if any(keyword in name_lower for keyword in meme_keywords):
                    description = sr.public_description[:100] + '...' if len(sr.public_description) > 100 else sr.public_description
                    trending_subreddits.append((sr.display_name, description, sr.subscribers))
                    
                    if len(trending_subreddits) >= limit:
                        break
            
            # Sort by subscriber count
            trending_subreddits.sort(key=lambda x: x[2], reverse=True)
            return trending_subreddits
            
        except Exception as e:
            logger.error(f"Error fetching trending subreddits: {e}")
            # Return default list if API fails
            return [
                ('memes', 'Memes!', 0),
                ('dankmemes', 'Dank memes for all', 0),
                ('wholesomememes', 'Wholesome memes', 0),
                ('MemeEconomy', 'Meme economy', 0),
                ('AdviceAnimals', 'Advice animals', 0)
            ]
    
    def get_guitar_subreddits(self, limit: int = 10) -> List[str]:
        """
        Get a list of guitar-related subreddits.
        
        Returns:
            List of subreddit names
        """
        if not self.reddit:
            self._check_credentials()
            
        # Static list of guitar-related subreddits
        default_subreddits = [
            "guitar",
            "guitarmemes",
            "guitarcirclejerk",
            "guitars",
            "guitarplaying",
            "acousticguitar",
            "guitarpedals",
            "bassguitar",
            "guitarlessons",
            "guitarcovers"
        ]
        
        # Try to discover additional guitar-related subreddits
        try:
            search_results = self.reddit.subreddits.search("guitar", limit=20)
            discovered_subreddits = []
            
            for subreddit in search_results:
                if hasattr(subreddit, 'display_name') and "guitar" in subreddit.display_name.lower():
                    discovered_subreddits.append(subreddit.display_name)
            
            # Combine default and discovered subreddits, remove duplicates
            all_subreddits = list(set(default_subreddits + discovered_subreddits))
            
            # Sort by relevance (default subreddits first, then alphabetically)
            sorted_subreddits = sorted(all_subreddits, 
                                     key=lambda x: (x not in default_subreddits, x.lower()))
            
            return sorted_subreddits[:limit]
        except Exception as e:
            logger.error(f"Error discovering guitar subreddits: {str(e)}")
            return default_subreddits[:limit]
    
    def _is_image_url(self, url: str) -> bool:
        """Check if URL points to an image."""
        return any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif'])
    
    def _validate_image_url(self, url: str) -> bool:
        """Validate that the URL is accessible."""
        try:
            # Just do a HEAD request to verify URL is valid
            response = requests.head(url, timeout=3)
            return response.status_code == 200
        except requests.RequestException:
            return False 