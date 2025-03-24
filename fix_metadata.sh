#!/bin/bash

# Fix Template Metadata Script
# This script executes the complete process to fix template metadata mismatches:
# 1. Resets template metadata files
# 2. Regenerates accurate descriptions for each template

echo "===== MEME TEMPLATE METADATA FIX PROCESS ====="
echo "This process will:"
echo "  1. Reset all template metadata"
echo "  2. Regenerate accurate descriptions for all templates"
echo "  3. Restart the Flask application with clean metadata"
echo ""
echo "NOTE: This process may take some time, especially regenerating descriptions!"
echo "----------------------------------------------"
echo ""

# Confirm with the user
read -p "Are you sure you want to proceed? (y/n): " confirm
if [[ $confirm != "y" && $confirm != "Y" ]]; then
    echo "Operation canceled."
    exit 0
fi

echo ""
echo "Step 1: Resetting template metadata..."
python reset_metadata.py

if [ $? -ne 0 ]; then
    echo "Error: Failed to reset metadata. Aborting."
    exit 1
fi

echo ""
echo "Step 2: Regenerating template descriptions..."
echo "This may take a while as it processes each template individually."
echo "You can monitor progress in the logs."
echo ""

python regenerate_descriptions.py

if [ $? -ne 0 ]; then
    echo "Error: Failed to regenerate descriptions. Aborting."
    exit 1
fi

echo ""
echo "Step 3: Restarting Flask application..."
pkill -f "python app.py" || true
python app.py &

echo ""
echo "===== METADATA FIX PROCESS COMPLETE ====="
echo "All template metadata has been reset and regenerated."
echo "Flask application has been restarted with clean metadata."
echo "You can now use the application with accurate template descriptions."
echo "" 