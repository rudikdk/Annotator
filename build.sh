#!/bin/bash
# Rebuild the compiled React bundle from source
# Run this after any changes to templates/index_src.jsx
set -e
cd "$(dirname "$0")"
npx babel templates/index_src.jsx --presets @babel/preset-react -o static/index_built.js
echo "Build complete: static/index_built.js"
