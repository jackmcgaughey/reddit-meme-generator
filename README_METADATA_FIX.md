# Meme Template Metadata Fix

This directory contains scripts to fix mismatches between meme templates and their descriptions.

## Background

The Reddit Meme Generator application uses template metadata from two sources:
1. `cache/templates_cache.json` - Contains basic template information from the ImgFlip API
2. `cache/custom_template_metadata.json` - Contains custom metadata, including descriptions

Over time, mismatches can occur between these files, leading to inconsistencies in the application, such as:
- Templates showing incorrect descriptions
- Template descriptions not matching the actual meme format
- Missing descriptions for certain templates

## Fix Scripts

This package includes three scripts to fix metadata issues:

### 1. `reset_metadata.py`

This script:
- Resets the custom metadata file to an empty state
- Refreshes the templates cache with clean data from the ImgFlip API
- Prepares the system for regenerating descriptions

### 2. `regenerate_descriptions.py`

This script:
- Processes each template one by one
- Uses OpenAI's API (GPT-4o with vision) to generate accurate descriptions based on the template images
- Saves the descriptions to the custom metadata file

### 3. `fix_metadata.sh`

This shell script runs both scripts in sequence:
1. Resets all template metadata
2. Regenerates accurate descriptions
3. Restarts the Flask application

## Usage

### Full Automated Fix

To perform a complete reset and regeneration of all template metadata:

```bash
./fix_metadata.sh
```

Follow the prompts to confirm and begin the process. Note that this process may take some time, especially during the description regeneration step.

### Manual Process

If you prefer to run the steps individually:

1. Reset metadata:
   ```bash
   python reset_metadata.py
   ```

2. Regenerate descriptions:
   ```bash
   python regenerate_descriptions.py
   ```

3. Restart the Flask application:
   ```bash
   pkill -f "python app.py" && python app.py
   ```

## Requirements

- Python 3.6+
- OpenAI API key configured in `.env` file
- Required Python packages (OpenAI, Pillow, requests, etc.)

## Troubleshooting

- If the OpenAI API key is not configured, set it in your `.env` file:
  ```
  OPENAI_API_KEY=your_api_key_here
  ```

- If the process is interrupted, you can safely run it again. The regeneration script will skip templates that already have descriptions.

- To process only specific templates, you can modify the regeneration script to filter templates based on their IDs or names. 