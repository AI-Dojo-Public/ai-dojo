#!/bin/bash

for file in /modules/*; do
    if [ -d "$file" ]; then  # check if the file is a directory
        echo "$file"
        /app/.venv/bin/pip install -e $file
    fi
done

exec "$@"
