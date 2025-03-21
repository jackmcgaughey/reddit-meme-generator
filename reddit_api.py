"""
Reddit API module for fetching memes.
"""
import praw
import logging
import requests
from typing import List, Tuple, Optional
import random

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
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        
        if client_id and client_secret:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            logger.info("Reddit API client initialized")
        else:
            self.reddit = None
            logger.warning("Reddit API client initialized with empty credentials")
    
    def configure(self, client_id: str, client_secret: str, user_agent: str = "MemeGenerator/1.0"):
        """
        Configure or reconfigure the Reddit API client with new credentials.
        
        Args:
            client_id: Your Reddit application client ID
            client_secret: Your Reddit application client secret
            user_agent: User agent for API requests
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        
        if client_id and client_secret:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            logger.info("Reddit API client reconfigured")
        else:
            self.reddit = None
            logger.warning("Reddit API client configured with empty credentials")
    
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
        """
        Check if URL points to an image.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if URL points to an image
        """
        # Check common image extensions
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg']
        return any(url.lower().endswith(ext) for ext in image_extensions)
    
    def _is_video_url(self, url: str) -> bool:
        """
        Check if URL points to a video.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if URL points to a video
        """
        # Common video extensions and patterns
        video_extensions = ['.mp4', '.webm', '.mov', '.avi', '.mkv', '.gifv']
        video_patterns = ['v.redd.it', 'youtube.com/watch', 'youtu.be', 'vimeo.com']
        
        if any(url.lower().endswith(ext) for ext in video_extensions):
            return True
        
        if any(pattern in url.lower() for pattern in video_patterns):
            return True
            
        return False
    
    def _validate_image_url(self, url: str) -> bool:
        """
        Check if an image URL is valid and accessible.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if URL is accessible and contains a valid image
        """
        try:
            response = requests.head(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def download_image(self, url: str, save_path: str) -> bool:
        """
        Download an image from a URL and save it to the specified path.
        
        Args:
            url: URL of the image to download
            save_path: Local path where the image should be saved
            
        Returns:
            bool: True if download and save were successful, False otherwise
        """
        try:
            # Verify the URL points to an image
            if not self._is_image_url(url):
                logger.error(f"URL does not point to an image: {url}")
                return False
                
            # Download the image
            response = requests.get(url, stream=True, timeout=10)
            
            # Check if request was successful
            if response.status_code != 200:
                logger.error(f"Failed to download image from {url}, status code: {response.status_code}")
                return False
                
            # Save the image to the specified path
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logger.info(f"Image successfully downloaded from {url} and saved to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {str(e)}")
            return False
    
    def _check_credentials(self) -> bool:
        """
        Verify that Reddit API credentials are available.
        
        Returns:
            bool: True if credentials are valid
        """
        if self.reddit:
            return True
            
        raise ValueError("Reddit API credentials not configured. Please configure them before using this method.")

    def get_memes_from_subreddit(
        self, 
        subreddit_name: str,
        category: str = "hot",
        limit: int = 25
    ) -> List[Tuple[str, str, int, str, str]]:
        """
        Fetch memes from a specific subreddit.
        
        Args:
            subreddit_name: Name of the subreddit to fetch from
            category: One of 'hot', 'new', 'top', 'rising'
            limit: Maximum number of posts to fetch
            
        Returns:
            List of tuples: (title, image_url, score, subreddit, post_id)
        """
        if not self.reddit:
            self._check_credentials()
            
        results = []
        logger.info(f"Fetching up to {limit} memes from r/{subreddit_name} ({category})")
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get posts based on category
            if category == "hot":
                posts = subreddit.hot(limit=limit * 2)  # Get more to account for filtering
            elif category == "new":
                posts = subreddit.new(limit=limit * 2)
            elif category == "top":
                posts = subreddit.top(limit=limit * 2)
            elif category == "rising":
                posts = subreddit.rising(limit=limit * 2)
            else:
                logger.error(f"Invalid category: {category}")
                return []
            
            # Process each post
            for post in posts:
                if not hasattr(post, 'url'):
                    continue
                    
                # Skip stickied posts
                if post.stickied:
                    continue
                    
                # Check if it's an image URL
                url = post.url
                if not self._is_image_url(url):
                    continue
                    
                # Verify the URL is accessible
                if not self._validate_image_url(url):
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
            
            logger.info(f"Found {len(results)} memes in r/{subreddit_name}")
            return results
            
        except Exception as e:
            logger.error(f"Error fetching from r/{subreddit_name}: {str(e)}")
            return []
            
    def search_band_images(self, band_name: str, limit: int = 10) -> List[Tuple[str, str, int, str, str]]:
        """
        Search for images related to a specific band or musician across Reddit.
        
        Args:
            band_name: Name of the band to search for
            limit: Maximum number of results to return
            
        Returns:
            List of tuples (title, image_url, score, subreddit, post_id)
        """
        if not self.reddit:
            self._check_credentials()
            
        results = []
        
        # We'll extend the limit to account for filtered images
        target_limit = limit * 3
        
        try:
            # First check if there's a dedicated subreddit for the band
            try:
                band_subreddit = band_name.replace(" ", "")
                sub = self.reddit.subreddit(band_subreddit)
                # Verify the subreddit exists by checking if it has a display name
                if hasattr(sub, 'display_name'):
                    logger.info(f"Found dedicated subreddit for {band_name}: r/{band_subreddit}")
                    
                    # Search for image posts in the band's subreddit
                    for post in sub.search("site:i.redd.it OR site:imgur.com", sort="relevance", limit=target_limit * 2):
                        if not hasattr(post, 'url'):
                            continue
                            
                        # Check if it's an image URL
                        url = post.url
                        if not self._is_image_url(url):
                            continue
                        
                        # Skip likely meme images with text
                        if self._is_likely_meme_image(post.title, str(post.subreddit)):
                            continue
                            
                        results.append((
                            post.title,
                            url,
                            post.score,
                            str(post.subreddit),
                            post.id
                        ))
                        
                        if len(results) >= target_limit:
                            break
            except Exception as e:
                # No dedicated subreddit, this is expected for many bands
                pass
                
            # Get band images from Music, pics, and other relevant subreddits
            if len(results) < target_limit:
                subreddits = ["Music", "pics", "listentothis", "OldSchoolCool", 
                             "90sMusic", "ClassicRock", "AlternativeRock", "rock", 
                             "Metal", "HeavyMetal", "Jazz", "RapMusic", "hiphopheads",
                             "country", "ClassicalMusic", "indieheads", "PopMusic"]
                
                # Join the subreddits for a multi-subreddit search
                subreddit_str = "+".join(subreddits)
                
                for post in self.reddit.subreddit(subreddit_str).search(
                    f"{band_name} site:i.redd.it OR site:imgur.com", 
                    sort="relevance", 
                    time_filter="all",
                    limit=target_limit * 2
                ):
                    if not hasattr(post, 'url'):
                        continue
                        
                    # Check if it's an image URL
                    url = post.url
                    if not self._is_image_url(url):
                        continue
                        
                    # Check for duplicates
                    if any(result[4] == post.id for result in results):
                        continue
                    
                    # Skip likely meme images with text
                    if self._is_likely_meme_image(post.title, str(post.subreddit)):
                        continue
                        
                    results.append((
                        post.title,
                        url,
                        post.score,
                        str(post.subreddit),
                        post.id
                    ))
                    
                    if len(results) >= target_limit:
                        break
            
            # If needed, search across all of Reddit
            if len(results) < target_limit:
                for post in self.reddit.subreddit("all").search(
                    f"{band_name} site:i.redd.it OR site:imgur.com", 
                    sort="relevance", 
                    time_filter="all",
                    limit=(target_limit - len(results)) * 3
                ):
                    if not hasattr(post, 'url'):
                        continue
                        
                    # Check if it's an image URL
                    url = post.url
                    if not self._is_image_url(url):
                        continue
                        
                    # Check for duplicates
                    if any(result[4] == post.id for result in results):
                        continue
                    
                    # Skip likely meme images with text
                    if self._is_likely_meme_image(post.title, str(post.subreddit)):
                        continue
                        
                    results.append((
                        post.title,
                        url,
                        post.score,
                        str(post.subreddit),
                        post.id
                    ))
                    
                    if len(results) >= target_limit:
                        break
                        
            logger.info(f"Found {len(results)} images for band '{band_name}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching for band images: {str(e)}")
            # Fall back to general music/meme images if we encounter an error
            try:
                return self.search_memes("music", limit=limit)
            except:
                return []
    
    def _is_likely_meme_image(self, title: str, subreddit: str) -> bool:
        """
        Check if an image is likely a meme based on title and subreddit.
        
        Args:
            title: The title of the Reddit post
            subreddit: The subreddit name
            
        Returns:
            True if the image is likely a meme, False otherwise
        """
        # List of subreddits known for memes
        meme_subreddits = [
            "memes", "dankmemes", "meme", "adviceanimals", "comedycemetery", 
            "funny", "prequelmemes", "historymemes", "memeconomy", "politicalcompassmemes",
            "wholesomememes", "okbuddyretard", "comedyheaven", "terriblefacebookmemes",
            "guitarmemes", "metalmemes", "musicmemes", "classicalmemes", "hiphopmemes"
        ]
        
        # List of keywords that often appear in meme titles
        meme_keywords = [
            "meme", "caption", "when you", "me when", "my face when", "tfw", "mfw", 
            "expectation vs reality", "see the joke", "lol", "lmao", "be like",
            "when the", "how it feels", "caption this", "text", "quote", "lyric",
            "words", "subtitle", "hilarious", "funny", "laugh", "humor", "punchline"
        ]
        
        # Check if the subreddit is a known meme subreddit
        if any(meme_sub.lower() in subreddit.lower() for meme_sub in meme_subreddits):
            return True
            
        # Check if the title contains meme keywords
        if any(keyword.lower() in title.lower() for keyword in meme_keywords):
            return True
            
        # Additional filtering for text-containing images
        text_indicators = ["text", "caption", "quote", "lyric", "says", "wrote", "writing", 
                          "typed", "tweet", "post", "comment", "message", "headline"]
        
        if any(indicator in title.lower() for indicator in text_indicators):
            return True
            
        # Check for uppercase titles (often indicates meme/caption style)
        if title.isupper() and len(title) > 10:
            return True
            
        # Check if there are quotation marks in the title (likely contains a quote)
        if '"' in title or "'" in title:
            return True
            
        return False

    def search_genre_images(self, genre: str, limit: int = 10) -> List[Tuple[str, str, int, str, str]]:
        """
        Search for images related to a specific music genre across Reddit.
        
        Args:
            genre: Music genre to search for (e.g., "60s rock", "jazz", "90s rock", "rave", "2010s pop")
            limit: Maximum number of results to return
            
        Returns:
            List of tuples (title, image_url, score, subreddit, post_id)
        """
        if not self.reddit:
            self._check_credentials()
            
        results = []
        
        # Define genre-specific search parameters
        genre_search_config = {
            "60s rock": {
                "subreddits": ["ClassicRock", "OldSchoolCool", "60sMusic", "classic_rock", "psychedelicrock", "rock", "Music"],
                "search_terms": ["60s music", "classic rock", "woodstock", "vintage rock", "psychedelic rock", "60s band"],
                "bands": ["Beatles", "Rolling Stones", "Jimi Hendrix", "Grateful Dead", "The Doors"]
            },
            "jazz": {
                "subreddits": ["Jazz", "JazzPiano", "JazzGuitar", "LearnJazz", "classicjazz", "JazzPhotos", "jazzmen", "Music"],
                "search_terms": ["jazz music", "bebop", "saxophone", "trumpet", "jazz performance", "jazz club"],
                "artists": ["Miles Davis", "John Coltrane", "Thelonious Monk", "Charlie Parker", "Duke Ellington"]
            },
            "90s rock": {
                "subreddits": ["grunge", "90sMusic", "90sAlternative", "90sRock", "Nirvana", "PearlJam", "Soundgarden", "Music"],
                "search_terms": ["grunge music", "alternative rock", "90s band", "90s rock music", "90s concert", "flannel shirt"],
                "bands": ["Nirvana", "Pearl Jam", "Soundgarden", "Alice in Chains", "Red Hot Chili Peppers"]
            },
            "rave": {
                "subreddits": ["aves", "EDM", "electronicmusic", "DJs", "ravelight", "festivals", "ravecouture", "Music"],
                "search_terms": ["rave music", "plur", "electronic music", "festival", "edm concert", "dj performance"],
                "concepts": ["glowsticks", "kandi", "dj", "lightshow", "warehouse party"]
            },
            "2010s pop": {
                "subreddits": ["popheads", "TaylorSwift", "ariheads", "lanadelrey", "JustinBieber", "kpop", "Music"],
                "search_terms": ["pop music", "pop concert", "chart topper", "pop performance", "music video", "pop singer"],
                "artists": ["Taylor Swift", "Ariana Grande", "Justin Bieber", "Billie Eilish", "BTS"]
            },
            "rock music": {
                "subreddits": ["rock", "ClassicRock", "AlternativeRock", "Metal", "hardrock", "Music"],
                "search_terms": ["rock music", "rock band", "rock concert", "guitar", "drummer", "rock show"],
                "bands": ["Led Zeppelin", "Queen", "AC/DC", "Foo Fighters", "Radiohead"]
            },
            "heavy metal": {
                "subreddits": ["Metal", "Metallica", "heavymetal", "thrashmetal", "deathmetal", "Music"],
                "search_terms": ["metal band", "heavy metal", "headbang", "metal concert", "metal show", "metal music"],
                "bands": ["Metallica", "Iron Maiden", "Black Sabbath", "Slayer", "Megadeth"]
            },
            "pop music": {
                "subreddits": ["popheads", "pop", "MusicCharts", "Billboard", "Music"],
                "search_terms": ["pop music", "pop concert", "pop performance", "pop star", "pop singer", "studio"],
                "artists": ["Madonna", "Michael Jackson", "Katy Perry", "Lady Gaga", "Bruno Mars"]
            },
            "hip hop music": {
                "subreddits": ["hiphopheads", "rap", "hiphop101", "trapmuzik", "Music"],
                "search_terms": ["hip hop", "rap concert", "rap music", "rapper", "hip hop show", "mc"],
                "artists": ["Kendrick Lamar", "Jay-Z", "Kanye West", "Eminem", "Drake"]
            },
            "alternative rock": {
                "subreddits": ["AlternativeRock", "indie", "indieheads", "radiohead", "Music"],
                "search_terms": ["alternative rock", "indie concert", "alternative band", "rock music", "indie rock show"],
                "bands": ["Radiohead", "The Killers", "Arctic Monkeys", "The Strokes", "Coldplay"]
            },
            "punk rock": {
                "subreddits": ["punk", "punkrock", "Hardcore", "greenday", "Music"],
                "search_terms": ["punk rock", "punk concert", "punk band", "punk show", "mosh pit", "punk music"],
                "bands": ["Ramones", "Green Day", "The Clash", "Sex Pistols", "Blink-182"]
            },
            "funk music": {
                "subreddits": ["funk", "funk_music", "Music"],
                "search_terms": ["funk music", "funk band", "funk concert", "bassist", "funk groove", "funk guitarist"],
                "bands": ["Parliament", "James Brown", "Earth Wind & Fire", "Sly and the Family Stone", "Prince"]
            },
            "grunge music": {
                "subreddits": ["grunge", "Nirvana", "PearlJam", "Soundgarden", "Music"],
                "search_terms": ["grunge music", "grunge concert", "seattle music", "grunge scene", "90s rock"],
                "bands": ["Nirvana", "Pearl Jam", "Soundgarden", "Alice in Chains", "Stone Temple Pilots"]
            }
        }

        # Clean up the genre string to match our configuration
        cleaned_genre = genre.lower().strip()
        # Remove "music" suffix if present for matching against config
        search_key = cleaned_genre.replace(" music", "").strip()
        
        # Get the search config for the selected genre (default to general music if not found)
        default_config = {
            "subreddits": ["Music", "listentothis", "pics", "concertporn", "musicpics", "bandpics"],
            "search_terms": [cleaned_genre, "band", "concert", "performance", "music", "stage", "musician"],
            "names": []
        }
        
        search_config = genre_search_config.get(search_key, default_config)
        
        # Always ensure these music subreddits are included
        music_subreddits = ["Music", "listentothis", "musicpics", "MusicPhotography", "concertporn", "LiveMusic"]
        for sub in music_subreddits:
            if sub not in search_config["subreddits"]:
                search_config["subreddits"].append(sub)
        
        # Create a list of subreddits to search in
        genre_subreddits = search_config["subreddits"]
        
        # We'll extend the limit to account for filtered images
        target_limit = limit * 3
        
        try:
            # First strategy: search in genre-specific subreddits
            subreddit_string = "+".join(genre_subreddits)
            
            # Ensure all search terms include 'music' to get relevant results
            search_terms = []
            for term in search_config["search_terms"]:
                if "music" not in term.lower():
                    search_terms.append(f"{term} music")
                else:
                    search_terms.append(term)
                    
            # Always add the original genre term with 'music'
            if cleaned_genre not in search_terms:
                search_terms.append(cleaned_genre)
            
            for term in search_terms:
                if len(results) >= target_limit:
                    break
                    
                # Construct search query to focus on music-related content
                search_query = f"{term} {cleaned_genre} (concert OR band OR musician OR performance OR stage) site:i.redd.it OR site:imgur.com"
                
                search_results = self.reddit.subreddit(subreddit_string).search(
                    search_query, 
                    sort="relevance", 
                    time_filter="all",
                    limit=target_limit * 2
                )
                
                for post in search_results:
                    if not hasattr(post, 'url'):
                        continue
                        
                    # Check if it's an image URL
                    url = post.url
                    if not self._is_image_url(url):
                        continue
                        
                    # Check for duplicates
                    if any(result[4] == post.id for result in results):
                        continue
                    
                    # Skip likely meme images with text
                    if self._is_likely_meme_image(post.title, str(post.subreddit)):
                        continue
                        
                    results.append((
                        post.title,
                        url,
                        post.score,
                        str(post.subreddit),
                        post.id
                    ))
                    
                    if len(results) >= target_limit:
                        break
            
            # Second strategy: search for associated artists/bands
            if len(results) < target_limit and "bands" in search_config:
                for band in search_config.get("bands", []):
                    if len(results) >= target_limit:
                        break
                        
                    band_results = self.search_band_images(band, limit=(target_limit - len(results)))
                    
                    # Filter out duplicates and likely meme images
                    for result in band_results:
                        if any(r[4] == result[4] for r in results):
                            continue
                        
                        if self._is_likely_meme_image(result[0], result[3]):
                            continue
                            
                        results.append(result)
                        
                        if len(results) >= target_limit:
                            break
            
            # Same for artists if present
            if len(results) < target_limit and "artists" in search_config:
                for artist in search_config.get("artists", []):
                    if len(results) >= target_limit:
                        break
                        
                    artist_results = self.search_band_images(artist, limit=(target_limit - len(results)))
                    
                    # Filter out duplicates and likely meme images
                    for result in artist_results:
                        if any(r[4] == result[4] for r in results):
                            continue
                        
                        if self._is_likely_meme_image(result[0], result[3]):
                            continue
                            
                        results.append(result)
                        
                        if len(results) >= target_limit:
                            break
            
            # Third strategy: broader search across all of Reddit
            if len(results) < target_limit:
                search_results = self.reddit.subreddit("all").search(
                    f"{cleaned_genre} music (concert OR band OR musician OR performance) site:i.redd.it OR site:imgur.com", 
                    sort="relevance", 
                    time_filter="all",
                    limit=(target_limit - len(results)) * 3
                )
                
                for post in search_results:
                    if not hasattr(post, 'url'):
                        continue
                        
                    # Check if it's an image URL
                    url = post.url
                    if not self._is_image_url(url):
                        continue
                        
                    # Check for duplicates
                    if any(result[4] == post.id for result in results):
                        continue
                    
                    # Skip likely meme images with text
                    if self._is_likely_meme_image(post.title, str(post.subreddit)):
                        continue
                        
                    results.append((
                        post.title,
                        url,
                        post.score,
                        str(post.subreddit),
                        post.id
                    ))
                    
                    if len(results) >= target_limit:
                        break
            
            # If we still don't have enough images, fall back to general music images
            if len(results) < target_limit:
                logger.info(f"Found only {len(results)} images for genre '{cleaned_genre}', searching for more general music images.")
                search_results = self.reddit.subreddit("all").search(
                    "music concert band performance live site:i.redd.it OR site:imgur.com",
                    sort="relevance", 
                    time_filter="all",
                    limit=(target_limit - len(results)) * 2
                )
                
                for post in search_results:
                    if not hasattr(post, 'url'):
                        continue
                        
                    # Check if it's an image URL
                    url = post.url
                    if not self._is_image_url(url):
                        continue
                        
                    # Check for duplicates
                    if any(result[4] == post.id for result in results):
                        continue
                    
                    # Skip likely meme images with text
                    if self._is_likely_meme_image(post.title, str(post.subreddit)):
                        continue
                        
                    results.append((
                        post.title,
                        url,
                        post.score,
                        str(post.subreddit),
                        post.id
                    ))
                    
                    if len(results) >= target_limit:
                        break
            
            # Randomize the results for variety
            random.shuffle(results)
            
            logger.info(f"Found {len(results)} images for genre '{cleaned_genre}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching for genre images: {str(e)}")
            # Fall back to general music/meme images if we encounter an error
            try:
                return self.search_memes("music concert band", limit=limit)
            except:
                return [] 