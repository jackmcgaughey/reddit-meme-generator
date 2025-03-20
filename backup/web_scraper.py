import requests
from bs4 import BeautifulSoup
import json
import time
import random
from urllib.parse import urljoin
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemeWebScraper:
    """Web scraper for finding trending memes from various websites."""
    
    def __init__(self, headers=None):
        """
        Initialize the scraper with custom headers.
        
        Args:
            headers (dict): Custom headers for HTTP requests to avoid getting blocked.
        """
        if headers is None:
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        else:
            self.headers = headers
    
    def _fetch_page(self, url):
        """
        Helper method to fetch web page content.
        
        Args:
            url (str): URL to fetch
            
        Returns:
            BeautifulSoup: Parsed HTML content or None if failed
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def scrape_imgur(self, section='hot', viral=True, limit=50):
        """
        Scrape trending memes from Imgur.
        
        Args:
            section (str): One of 'hot', 'top', 'user'
            viral (bool): Whether to include viral posts
            limit (int): Maximum number of posts to fetch
            
        Returns:
            list: List of tuples (title, image_url, view_count)
        """
        memes = []
        
        try:
            # Imgur gallery API URL
            viral_param = 'viral' if viral else 'top'
            url = f"https://imgur.com/{section}/{viral_param}"
            
            soup = self._fetch_page(url)
            if not soup:
                return memes
                
            # Find posts on the page
            post_elements = soup.select('.post')
            
            for post in post_elements[:limit]:
                try:
                    # Extract post information
                    title_elem = post.select_one('.post-title')
                    img_elem = post.select_one('.post-image img, .post-image video')
                    views_elem = post.select_one('.post-info .views')
                    
                    if title_elem and img_elem:
                        title = title_elem.get_text(strip=True)
                        
                        # Get image source
                        if img_elem.name == 'img':
                            image_url = img_elem.get('src', '')
                            if image_url.startswith('//'):
                                image_url = 'https:' + image_url
                        else:  # video
                            image_url = img_elem.get('poster', '')
                            if image_url.startswith('//'):
                                image_url = 'https:' + image_url
                        
                        # Get view count if available
                        views = 0
                        if views_elem:
                            views_text = views_elem.get_text(strip=True).replace(',', '')
                            views = int(views_text) if views_text.isdigit() else 0
                        
                        memes.append((title, image_url, views))
                except Exception as e:
                    logger.error(f"Error parsing Imgur post: {e}")
                    continue
                    
            # Sort by view count
            memes.sort(key=lambda x: x[2], reverse=True)
            
        except Exception as e:
            logger.error(f"Error scraping Imgur: {e}")
            
        return memes
    
    def scrape_knowyourmeme(self, limit=50):
        """
        Scrape trending memes from Know Your Meme.
        
        Args:
            limit (int): Maximum number of memes to fetch
            
        Returns:
            list: List of tuples (title, image_url, page_url, description)
        """
        memes = []
        
        try:
            # KYM trending page
            url = "https://knowyourmeme.com/memes/trending"
            
            soup = self._fetch_page(url)
            if not soup:
                return memes
                
            # Find meme entries
            meme_entries = soup.select('.entry')
            
            for entry in meme_entries[:limit]:
                try:
                    # Extract meme information
                    title_elem = entry.select_one('h2 a')
                    img_elem = entry.select_one('.photo img')
                    desc_elem = entry.select_one('.entry-meta-description')
                    
                    if title_elem and img_elem:
                        title = title_elem.get_text(strip=True)
                        image_url = img_elem.get('data-src') or img_elem.get('src', '')
                        page_url = urljoin("https://knowyourmeme.com", title_elem.get('href', ''))
                        
                        # Get description if available
                        description = ""
                        if desc_elem:
                            description = desc_elem.get_text(strip=True)
                            
                        memes.append((title, image_url, page_url, description))
                except Exception as e:
                    logger.error(f"Error parsing KYM entry: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Know Your Meme: {e}")
            
        return memes
    
    def scrape_9gag(self, section='trending', limit=50):
        """
        Scrape trending memes from 9GAG.
        
        Args:
            section (str): One of 'trending', 'hot', 'fresh'
            limit (int): Maximum number of posts to fetch
            
        Returns:
            list: List of tuples (title, image_url, points)
        """
        memes = []
        
        try:
            url = f"https://9gag.com/{section}"
            
            soup = self._fetch_page(url)
            if not soup:
                return memes
                
            # Find posts
            posts = soup.select('article.post-article')
            
            for post in posts[:limit]:
                try:
                    # Extract post information
                    title_elem = post.select_one('h1.post-title, h3.post-title')
                    img_elem = post.select_one('img.post-image')
                    points_elem = post.select_one('.post-votes .point')
                    
                    if title_elem and img_elem:
                        title = title_elem.get_text(strip=True)
                        image_url = img_elem.get('src', '')
                        
                        # Get points if available
                        points = 0
                        if points_elem:
                            points_text = points_elem.get_text(strip=True).replace('k', '000').replace('.', '')
                            points = int(points_text) if points_text.isdigit() else 0
                            
                        memes.append((title, image_url, points))
                except Exception as e:
                    logger.error(f"Error parsing 9GAG post: {e}")
                    continue
                    
            # Sort by points
            memes.sort(key=lambda x: x[2], reverse=True)
            
        except Exception as e:
            logger.error(f"Error scraping 9GAG: {e}")
            
        return memes
        
    def get_trending_memes(self, sources=None, limit_per_source=20):
        """
        Get trending memes from multiple sources.
        
        Args:
            sources (list): List of source names to scrape. 
                          Options: 'imgur', 'knowyourmeme', '9gag'
            limit_per_source (int): Maximum number of memes to fetch per source
            
        Returns:
            dict: Dictionary mapping source names to lists of memes
        """
        if sources is None:
            sources = ['imgur', 'knowyourmeme', '9gag']
            
        results = {}
        
        for source in sources:
            # Add a small delay between requests to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            if source == 'imgur':
                results['imgur'] = self.scrape_imgur(limit=limit_per_source)
            elif source == 'knowyourmeme':
                results['knowyourmeme'] = self.scrape_knowyourmeme(limit=limit_per_source)
            elif source == '9gag':
                results['9gag'] = self.scrape_9gag(limit=limit_per_source)
                
        return results 