#!/bin/bash
# This script runs during the build phase on Render

# Make the script executable
chmod +x build.sh

# Install Python dependencies
pip install -r requirements.txt

# Create uploads directory on the mounted disk
if [ -d "/data" ]; then
  mkdir -p /data/uploads
  echo "Created uploads directory on mounted disk"
fi

# Initialize the database
python init_db.py

echo "Build completed successfully!"
