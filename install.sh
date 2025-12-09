#!/bin/bash

REPO_URL="https://github.com/tawanamohammadi/tawana-antigravity-cleaner.git"
DEST_DIR="$HOME/antigravity-cleaner"

echo "Downloading Antigravity Cleaner..."
if [ -d "$DEST_DIR" ]; then
    rm -rf "$DEST_DIR"
fi

git clone --depth 1 $REPO_URL $DEST_DIR

cd $DEST_DIR
chmod +x run_mac_linux.sh
echo "Starting Cleaner..."
./run_mac_linux.sh
