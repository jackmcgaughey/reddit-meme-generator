import json
import sys

if len(sys.argv) != 3:
    print("Usage: python3 update_config_simple.py <reddit_client_id> <reddit_client_secret>")
    sys.exit(1)

client_id = sys.argv[1]
client_secret = sys.argv[2]

try:
    # Load existing config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Update config
    config['reddit']['client_id'] = client_id
    config['reddit']['client_secret'] = client_secret
    
    # Save config
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("Config successfully updated with Reddit API credentials!")
    
except Exception as e:
    print(f"Error updating config: {e}") 