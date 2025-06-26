#!/bin/bash

# Only allow .md output
FORMAT="md"

# Check if a directory argument is passed
TARGET_DIR="${1:-.}"

# Check if the directory exists
if [ ! -d "$TARGET_DIR" ]; then
  echo "❌ Error: Directory '$TARGET_DIR' does not exist."
  exit 1
fi

# Convert to absolute path and change to the target directory
cd "$TARGET_DIR" || exit 1

# Get root directory name and script filename
ROOT_DIR_NAME=$(basename "$(pwd)")
SCRIPT_NAME=$(basename "$0")
DATE=$(date +"%Y-%m-%d")
OUTPUT="${ROOT_DIR_NAME}-Codebase-Dump-${DATE}.md"

# Clear output file
> "$OUTPUT"

# Add directory tree (excluding unwanted dirs)
echo "## Project Directory Structure" >> "$OUTPUT"
echo '```' >> "$OUTPUT"
tree -F --dirsfirst -I '__pycache__|venv|models|node_modules|.git|dist|build' >> "$OUTPUT"
echo '```' >> "$OUTPUT"
echo -e "\n\n" >> "$OUTPUT"

# File extensions to include
EXTENSIONS="js|ts|tsx|py|css|html|json|sh|Dockerfile|md"

# Generate the dump
find . -type d \( -name '__pycache__' -o -name 'venv' -o -name '.git' -o -name 'dist' -o -name 'build' -o -name 'ai_framework/models' -o -name 'node_modules' \) -prune -o -type f -print \
  | grep -Ev 'package-lock.json' \
  | grep -E "\.($EXTENSIONS)$|Dockerfile$" \
  | sort \
  | while read -r file; do
    # Skip output file and the script itself
    if [[ "$file" == "./$OUTPUT" || "$(basename "$file")" == "$SCRIPT_NAME" ]]; then
      continue
    fi

    echo "### \`$file\`" >> "$OUTPUT"
    echo '```'$(basename "$file" | awk -F. '{print $NF}') >> "$OUTPUT"
    cat "$file" >> "$OUTPUT"
    echo -e '\n```\n' >> "$OUTPUT"
done

echo "✅ Markdown file created: $OUTPUT in $TARGET_DIR"
