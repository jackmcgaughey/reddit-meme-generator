import tweepy
from tweepy.errors import TweepyException

class TwitterAPI:
    """Handles authentication and meme fetching from Twitter API."""
    
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):
        """Initialize and authenticate with Twitter API."""
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(self.auth)
    
    def fetch_memes(self, accounts, count=10):
        """
        Fetch recent tweets with images from specified accounts.
        Args:
            accounts (list): List of Twitter screen names (e.g., ['9GAG']).
            count (int): Number of tweets to fetch per account.
        Returns:
            list: List of tuples (tweet_text, image_url).
        """
        memes = []
        for account in accounts:
            try:
                tweets = self.api.user_timeline(
                    screen_name=account,
                    count=count,
                    include_entities=True
                )
                for tweet in tweets:
                    if 'media' in tweet.entities:
                        for media in tweet.entities['media']:
                            if media['type'] == 'photo':
                                memes.append((tweet.text, media['media_url']))
            except TweepyException as e:
                print(f"Error fetching tweets from {account}: {e}")
        return memes
        
    def fetch_trending_memes(self, hashtags=None, count=50):
        """
        Fetch trending memes by hashtags and sort by engagement.
        
        Args:
            hashtags (list): List of hashtags to search (e.g., ['memes', 'dankmemes']).
                            If None, uses default popular meme hashtags.
            count (int): Number of tweets to fetch per hashtag.
            
        Returns:
            list: List of tuples (tweet_text, image_url, engagement_score).
                 Engagement score is calculated based on likes, retweets, and replies.
        """
        if hashtags is None:
            hashtags = ['memes', 'dankmemes', 'funny', 'memesdaily', 'memesoftheday']
            
        trending_memes = []
        
        for hashtag in hashtags:
            try:
                query = f"#{hashtag} filter:images -filter:retweets"
                tweets = self.api.search_tweets(
                    q=query,
                    count=count,
                    result_type='popular',
                    include_entities=True,
                    tweet_mode='extended'
                )
                
                for tweet in tweets:
                    # Calculate engagement score (simplistic version)
                    engagement = tweet.favorite_count * 1.0 + tweet.retweet_count * 2.0
                    
                    if hasattr(tweet, 'entities') and 'media' in tweet.entities:
                        for media in tweet.entities['media']:
                            if media['type'] == 'photo':
                                # Get full text handling both normal and extended tweets
                                text = tweet.full_text if hasattr(tweet, 'full_text') else tweet.text
                                trending_memes.append((text, media['media_url'], engagement))
                
            except TweepyException as e:
                print(f"Error fetching trending tweets for #{hashtag}: {e}")
                
        # Sort by engagement score (highest first)
        trending_memes.sort(key=lambda x: x[2], reverse=True)
        return trending_memes