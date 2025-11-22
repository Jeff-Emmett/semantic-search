# Local Semantic Search Service

Self-hosted semantic search infrastructure for tldraw canvas integration.

## Quick Start

```bash
# 1. Clone and setup
git clone <your-repo>
cd semantic-search
chmod +x scripts/*.sh
./scripts/setup.sh

# 2. Configure (edit .env if needed)
cp .env.example .env

# 3. Deploy
./scripts/deploy.sh

# 4. Test
python scripts/test_service.py

# 5. Index your first site
python services/crawler.py https://example.com
```

## Architecture

- **Qdrant**: Vector database (localhost:6333)
- **Embedding Service**: sentence-transformers (localhost:8001)
- **Search API**: FastAPI backend (localhost:8000)

## API Endpoints

### POST /index

Index a single document:

```bash
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your document text",
    "url": "https://example.com",
    "title": "Document Title",
    "metadata": {"category": "example"}
  }'
```

### POST /search

Search semantically:

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mycelial networks",
    "limit": 10,
    "score_threshold": 0.5,
    "use_exa": false
  }'
```

### GET /stats

Get collection stats:

```bash
curl http://localhost:8000/stats
```

## Canvas Integration

See `client/canvas_integration.ts` for tldraw integration.

## Deployment Options

### Local Development

```bash
docker-compose up
```

### Production (Digital Ocean)

```bash
# SSH into droplet
ssh root@your-droplet-ip

# Clone repo
git clone <your-repo>
cd semantic-search

# Deploy with production settings
docker-compose -f docker-compose.prod.yml up -d
```

## Cost Estimates

- DO Droplet (4GB): $24/month
- Storage (10GB): ~$1/month
- RunPod (optional GPU): $0.10-0.20/hr when needed

Total: ~$25/month for unlimited queries

## Maintenance

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Backup Qdrant data
tar -czf qdrant_backup.tar.gz qdrant_storage/

# Update models
docker-compose build --no-cache embedding-service
docker-compose up -d
```

## Troubleshooting

**Embedding service slow?**
- Use smaller model: `EMBEDDING_MODEL=all-MiniLM-L6-v2`
- Or deploy to RunPod GPU for 10x speed

**Out of memory?**
- Increase Docker memory limit
- Use swap on droplet: `sudo swapon --show`

**Qdrant connection failed?**
- Check ports: `docker-compose ps`
- View logs: `docker-compose logs qdrant`

## Next Steps

1. ✅ Deploy locally
2. ✅ Test with sample data
3. 🔄 Integrate with canvas
4. 🔄 Crawl initial corpus
5. 🔄 Deploy to production
6. 🔄 Add Exa hybrid search
