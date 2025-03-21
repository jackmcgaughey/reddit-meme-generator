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
        Search for images related to a specific band across Reddit.
        
        Args:
            band_name: Name of the band to search for
            limit: Maximum number of results to return
            
        Returns:
            List of tuples (title, image_url, score, subreddit, post_id)
        """
        if not self.reddit:
            self._check_credentials()
            
        results = []
        
        # Create a list of music-related subreddits to search in
        music_subreddits = [
            "Music",
            "listentothis",
            "IndieFolk",
            "Metal",
            "Rock",
            "AlternativeRock",
            "ClassicRock",
            "HipHopImages",
            "FolkPunk",
            "Punk",
            "Jazz",
            "Emo",
            "PostRock",
            "Blues",
            "ElectronicMusic",
            "Rap",
            "IndieHeads",
            "country"
        ]
        
        # Try to find if there's a subreddit dedicated to the band
        try:
            # Sanitize band name for search
            sanitized_band_name = band_name.replace(" ", "").lower()
            
            # Check if a specific subreddit exists for this band
            band_subreddit = None
            try:
                sub = self.reddit.subreddit(sanitized_band_name)
                if hasattr(sub, 'display_name'):
                    band_subreddit = sub.display_name
                    music_subreddits.insert(0, band_subreddit)  # Add it to the front of the list
                    logger.info(f"Found dedicated subreddit for {band_name}: r/{band_subreddit}")
            except Exception:
                logger.info(f"No dedicated subreddit found for {band_name}")
            
            # First strategy: search in the band's subreddit if it exists
            if band_subreddit:
                search_results = self.reddit.subreddit(band_subreddit).search(
                    "site:i.redd.it OR site:imgur.com", 
                    sort="hot", 
                    time_filter="all",
                    limit=limit * 2
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
            
            # Second strategy: search all music subreddits
            if len(results) < limit:
                subreddit_string = "+".join(music_subreddits)
                
                search_results = self.reddit.subreddit(subreddit_string).search(
                    f"\"{band_name}\" site:i.redd.it OR site:imgur.com", 
                    sort="relevance", 
                    time_filter="all",
                    limit=limit * 3
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
                        
                    results.append((
                        post.title,
                        url,
                        post.score,
                        str(post.subreddit),
                        post.id
                    ))
                    
                    if len(results) >= limit:
                        break
            
            # Third strategy: broader search across all of Reddit
            if len(results) < limit:
                search_results = self.reddit.subreddit("all").search(
                    f"\"{band_name}\" site:i.redd.it OR site:imgur.com", 
                    sort="relevance", 
                    time_filter="all",
                    limit=(limit - len(results)) * 3
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
                        
                    results.append((
                        post.title,
                        url,
                        post.score,
                        str(post.subreddit),
                        post.id
                    ))
                    
                    if len(results) >= limit:
                        break
            
            # If we still don't have enough images, fall back to guitar images
            if len(results) < limit and len(results) == 0:
                logger.info(f"No band-specific images found for {band_name}, falling back to guitar images.")
                guitar_results = self.search_guitar_memes(limit=limit)
                results.extend(guitar_results[:limit - len(results)])
            
            logger.info(f"Found {len(results)} images for band '{band_name}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching for band images: {str(e)}")
            # Fall back to guitar images if we encounter an error
            try:
                return self.search_guitar_memes(limit=limit)
            except:
                return []
    
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
                "subreddits": ["ClassicRock", "OldSchoolCool", "60sMusic", "classic_rock", "psychedelicrock", "rock"],
                "search_terms": ["60s", "classic rock", "woodstock", "vintage", "psychedelic"],
                "bands": ["Beatles", "Rolling Stones", "Jimi Hendrix", "Grateful Dead", "The Doors"]
            },
            "jazz": {
                "subreddits": ["Jazz", "JazzPiano", "JazzGuitar", "LearnJazz", "classicjazz", "JazzPhotos", "jazzmen"],
                "search_terms": ["jazz", "bebop", "saxophone", "trumpet", "improvisation", "club"],
                "artists": ["Miles Davis", "John Coltrane", "Thelonious Monk", "Charlie Parker", "Duke Ellington"]
            },
            "90s rock": {
                "subreddits": ["grunge", "90sMusic", "90sAlternative", "90sRock", "Nirvana", "PearlJam", "Soundgarden"],
                "search_terms": ["grunge", "alternative", "flannel", "90s rock", "MTV", "generation x"],
                "bands": ["Nirvana", "Pearl Jam", "Soundgarden", "Alice in Chains", "Red Hot Chili Peppers"]
            },
            "rave": {
                "subreddits": ["aves", "EDM", "electronicmusic", "DJs", "ravelight", "festivals", "ravecouture"],
                "search_terms": ["rave", "plur", "electronic", "festival", "lights", "edm", "dance"],
                "concepts": ["glowsticks", "kandi", "dj", "lightshow", "warehouse party"]
            },
            "2010s pop": {
                "subreddits": ["popheads", "TaylorSwift", "ariheads", "lanadelrey", "JustinBieber", "kpop"],
                "search_terms": ["pop", "streaming", "chart topper", "stan", "instagram aesthetic"],
                "artists": ["Taylor Swift", "Ariana Grande", "Justin Bieber", "Billie Eilish", "BTS"]
            }
        }
        
        # Get the search config for the selected genre (default to general music if not found)
        search_config = genre_search_config.get(genre.lower(), {
            "subreddits": ["Music", "pics", "listentothis", "ImagesOfThe2010s"],
            "search_terms": [genre, "music", "concert", "festival", "band"],
            "names": []
        })
        
        # Create a list of subreddits to search in
        genre_subreddits = search_config["subreddits"] + ["Music", "pics", "OldSchoolCool", "ImagesOfThe20thCentury"]
        
        try:
            # First strategy: search in genre-specific subreddits
            subreddit_string = "+".join(genre_subreddits)
            
            for term in search_config["search_terms"]:
                if len(results) >= limit:
                    break
                    
                search_results = self.reddit.subreddit(subreddit_string).search(
                    f"{term} {genre} site:i.redd.it OR site:imgur.com", 
                    sort="relevance", 
                    time_filter="all",
                    limit=limit * 2
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
                        
                    results.append((
                        post.title,
                        url,
                        post.score,
                        str(post.subreddit),
                        post.id
                    ))
                    
                    if len(results) >= limit:
                        break
            
            # Second strategy: search for associated artists/bands
            if len(results) < limit and "bands" in search_config:
                for band in search_config.get("bands", []):
                    if len(results) >= limit:
                        break
                        
                    band_results = self.search_band_images(band, limit=(limit - len(results)))
                    
                    # Filter out duplicates
                    for result in band_results:
                        if any(r[4] == result[4] for r in results):
                            continue
                            
                        results.append(result)
                        
                        if len(results) >= limit:
                            break
            
            # Same for artists if present
            if len(results) < limit and "artists" in search_config:
                for artist in search_config.get("artists", []):
                    if len(results) >= limit:
                        break
                        
                    artist_results = self.search_band_images(artist, limit=(limit - len(results)))
                    
                    # Filter out duplicates
                    for result in artist_results:
                        if any(r[4] == result[4] for r in results):
                            continue
                            
                        results.append(result)
                        
                        if len(results) >= limit:
                            break
            
            # Third strategy: broader search across all of Reddit
            if len(results) < limit:
                search_results = self.reddit.subreddit("all").search(
                    f"{genre} music site:i.redd.it OR site:imgur.com", 
                    sort="relevance", 
                    time_filter="all",
                    limit=(limit - len(results)) * 3
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
                        
                    results.append((
                        post.title,
                        url,
                        post.score,
                        str(post.subreddit),
                        post.id
                    ))
                    
                    if len(results) >= limit:
                        break
            
            # If we still don't have enough images, fall back to general music images
            if len(results) < limit:
                logger.info(f"Found only {len(results)} images for genre '{genre}', searching for more general music images.")
                search_results = self.reddit.subreddit("all").search(
                    "music meme site:i.redd.it OR site:imgur.com",
                    sort="relevance", 
                    time_filter="all",
                    limit=(limit - len(results)) * 2
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
                        
                    results.append((
                        post.title,
                        url,
                        post.score,
                        str(post.subreddit),
                        post.id
                    ))
                    
                    if len(results) >= limit:
                        break
            
            logger.info(f"Found {len(results)} images for genre '{genre}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching for genre images: {str(e)}")
            # Fall back to general music/meme images if we encounter an error
            try:
                return self.search_memes("music", limit=limit)
            except:
                return [] 