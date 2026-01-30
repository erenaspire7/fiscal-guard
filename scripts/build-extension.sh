#!/bin/bash
# Build the Fiscal Guard Chrome Extension

set -e

echo "🔧 Building Fiscal Guard Chrome Extension..."

# Check if .env exists in root directory
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found in root directory"
    if [ -f ".env.example" ]; then
        echo "📝 Copying from .env.example..."
        cp .env.example .env
        echo "⚠️  Please edit .env with your configuration"
        echo "⚠️  Make sure these variables are set:"
        echo "   - VITE_API_URL"
        echo "   - VITE_GOOGLE_CLIENT_ID"
        exit 1
    else
        echo "❌ .env.example not found"
        exit 1
    fi
fi

# Export environment variables from .env file
echo "📦 Loading environment variables from root .env..."
set -a
source .env
set +a

# Navigate to extension directory
cd extension

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    yarn install
else
    echo "✅ Dependencies already installed"
fi

# Run TypeScript compiler
echo "🔍 Type checking..."
yarn tsc -b

# Build extension
echo "🏗️  Building extension..."
yarn vite build

# Check if build succeeded
if [ -d "dist" ]; then
    echo ""
    echo "✅ Extension built successfully!"
    echo ""
    echo "📍 Output directory: extension/dist"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Open Chrome and go to chrome://extensions/"
    echo "   2. Enable 'Developer mode'"
    echo "   3. Click 'Load unpacked'"
    echo "   4. Select the extension/dist directory"
    echo ""
    echo "🔑 Don't forget to:"
    echo "   - Get a Gemini API key from https://makersuite.google.com/app/apikey"
    echo "   - Configure your Google OAuth client ID in manifest.json"
    echo ""
else
    echo "❌ Build failed - dist directory not found"
    exit 1
fi
