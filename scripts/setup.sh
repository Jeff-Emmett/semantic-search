#!/bin/bash
set -e

echo "🚀 Setting up Local Semantic Search Service..."

# Check dependencies
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Please install Docker first."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ docker-compose not found. Please install it first."; exit 1; }

# Create directory structure
echo "📁 Creating project structure..."
mkdir -p services scripts client qdrant_storage

# Copy .env.example to .env if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration"
fi

# Build and start services
echo "🐳 Building Docker containers..."
docker-compose build

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file if needed"
echo "2. Run: ./scripts/deploy.sh"
echo "3. Test with: python scripts/test_service.py"
