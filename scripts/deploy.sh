#!/bin/bash
set -e

echo "🚀 Deploying Semantic Search Service..."

# Start services
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Health checks
echo "🏥 Checking service health..."

# Check Qdrant
if curl -s http://localhost:6333/health > /dev/null; then
    echo "✅ Qdrant is healthy"
else
    echo "❌ Qdrant is not responding"
    exit 1
fi

# Check Embedding Service
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ Embedding Service is healthy"
else
    echo "❌ Embedding Service is not responding"
    exit 1
fi

# Check Search API
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Search API is healthy"
else
    echo "❌ Search API is not responding"
    exit 1
fi

echo ""
echo "🎉 All services deployed successfully!"
echo ""
echo "Service URLs:"
echo "  Search API:      http://localhost:8000"
echo "  API Docs:        http://localhost:8000/docs"
echo "  Embedding API:   http://localhost:8001"
echo "  Qdrant UI:       http://localhost:6333/dashboard"
echo ""
echo "View logs: docker-compose logs -f"
echo "Stop services: docker-compose down"
