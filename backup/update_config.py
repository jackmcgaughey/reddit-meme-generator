import json
import getpass

print("Reddit API Credentials Update Tool")
print("=================================")

# Load existing config
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
        
    # Get credentials from user
    client_id = getpass.getpass("Enter your Reddit client ID: ")
    client_secret = getpass.getpass("Enter your Reddit client secret: ")
    
    # Update config
    config['reddit']['client_id'] = client_id
    config['reddit']['client_secret'] = client_secret
    
    # Save config
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
        
    print("Config successfully updated!")
    print("You can now run the meme generator with Reddit API access.")
    
except Exception as e:
    print(f"Error updating config: {e}") 