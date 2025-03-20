def select_meme(memes):
    """
    Display memes and prompt user to select one.
    Args:
        memes (list): List of tuples (tweet_text, image_url).
    Returns:
        str: Selected image URL.
    """
    for i, (text, url) in enumerate(memes):
        print(f"{i+1}. {text} - {url}")
    while True:
        try:
            selection = int(input("Select a meme by number: ")) - 1
            if selection < 0 or selection >= len(memes):
                print("Invalid selection. Please try again.")
            else:
                return memes[selection][1]
        except ValueError:
            print("Please enter a valid number.")

def get_text():
    """
    Prompt user for top and bottom text.
    Returns:
        tuple: (top_text, bottom_text).
    """
    top_text = input("Enter top text: ")
    bottom_text = input("Enter bottom text: ")
    return top_text, bottom_text

def get_api_keys():
    """
    Prompt user for Twitter API keys.
    Returns:
        tuple: (consumer_key, consumer_secret, access_token, access_token_secret).
    """
    consumer_key = input("Enter your consumer key: ")
    consumer_secret = input("Enter your consumer secret: ")
    access_token = input("Enter your access token: ")
    access_token_secret = input("Enter your access token secret: ")
    return consumer_key, consumer_secret, access_token, access_token_secret