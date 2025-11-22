# Personal Semantic Search System - Usage Guide

## 🎉 What You Have

A fully functional, **private semantic search system** running locally that indexes and searches your personal data using AI embeddings.

### Current Status
- ✅ **1,396 Obsidian notes** indexed
- ✅ Qdrant vector database running
- ✅ FastAPI search service live
- ✅ All data stored locally (100% private)

## 🔍 Quick Search

```bash
# Search your Obsidian vault
./search.sh "your search query"

# Examples
./search.sh "token engineering"
./search.sh "mycelial networks"
./search.sh "regenerative economics"
```

## 📊 What's Indexed

### From Your Obsidian Vault:
- Full text content
- Frontmatter metadata
- Tags (#hashtags)
- Wikilinks ([[links]])
- File creation/modification dates
- File paths

### Searchable by:
- Semantic meaning (not just keywords!)
- Tags
- Date ranges
- File paths
- Any metadata field

## 🔧 Service Management

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Start services
docker-compose up -d

# Check service health
curl http://localhost:8000/health
```

## 📝 Re-indexing Your Vault

When you add new notes:

```bash
docker run --rm --network semantic-search_default \
  -e API_URL="http://search-api:8000" \
  -v "/mnt/c/Users/jeffe/Jeff's Vault:/vault:ro" \
  -v "/home/jeffe/Github/semantic-search/services:/app" \
  semantic-search_search-api \
  python3 /app/obsidian_indexer.py index /vault
```

## 🌐 API Access

### Interactive Documentation
Visit: http://localhost:8000/docs

### Search API
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "your search here",
    "limit": 10,
    "score_threshold": 0.4
  }'
```

### Filter by Source
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "your search",
    "filter_metadata": {"source": "obsidian"}
  }'
```

### Get Statistics
```bash
curl http://localhost:8000/stats
```

## 📁 Expanding to Other Data Sources

### Index Text Files
```bash
docker run --rm --network semantic-search_default \
  -e API_URL="http://search-api:8000" \
  -v "/path/to/your/documents:/data:ro" \
  -v "/home/jeffe/Github/semantic-search/services:/app" \
  semantic-search_search-api \
  python3 /app/universal_indexer.py /data text
```

### Index CSV Files
```bash
docker run --rm --network semantic-search_default \
  -e API_URL="http://search-api:8000" \
  -v "/path/to/your/csvs:/data:ro" \
  -v "/home/jeffe/Github/semantic-search/services:/app" \
  semantic-search_search-api \
  python3 /app/universal_indexer.py /data csv
```

### Index PDFs (requires PyPDF2)
```bash
# First install PyPDF2 in the container (one-time)
docker exec -it semantic-search_search-api_1 pip install PyPDF2

# Then index
docker run --rm --network semantic-search_default \
  -e API_URL="http://search-api:8000" \
  -v "/path/to/your/pdfs:/data:ro" \
  -v "/home/jeffe/Github/semantic-search/services:/app" \
  semantic-search_search-api \
  python3 /app/universal_indexer.py /data pdf
```

## 🚀 Next Steps: What Else Can Be Indexed?

### Easy to Add:
1. **Email archives** (mbox, Maildir)
   - Search your entire email history semantically
   - Find emails by topic, not just sender/subject

2. **Bookmarks** (browser exports)
   - Never lose track of saved articles
   - Find that link you bookmarked months ago

3. **Code repositories**
   - Search your codebases by functionality
   - Find implementations across projects

4. **Financial data** (bank statements, transactions)
   - Natural language queries: "healthcare expenses last year"
   - Pattern detection across accounts

5. **Chat logs** (Slack, Discord, Telegram exports)
   - Search conversations semantically
   - Find that discussion about X

6. **Music metadata** (ID3 tags, playlists)
   - Search by mood, genre, era
   - Find songs you haven't heard in years

7. **Photos** (EXIF data, locations)
   - Search by location, date, people
   - Find "that photo from the beach trip"

### Advanced Possibilities:
- **Voice memos** (transcribed)
- **Browser history** (with page content)
- **Meeting transcripts**
- **Calendar events** (historical)
- **Health data** (fitness apps, journals)
- **Reading lists** (Kindle highlights, Pocket)

## 💾 Data Storage

All your data is stored in:
```
./qdrant_storage/
```

### Backup Your Data
```bash
# Create backup
tar -czf semantic-search-backup-$(date +%Y%m%d).tar.gz qdrant_storage/

# Restore backup
tar -xzf semantic-search-backup-YYYYMMDD.tar.gz
```

## 🔒 Privacy & Security

- ✅ 100% local - no cloud services
- ✅ No data leaves your machine
- ✅ Open source components
- ✅ You control all data
- ✅ Can run air-gapped

## 🎯 Search Tips

### Better Results:
1. **Be conceptual**: "coordination problems in DAOs" > "dao coordination"
2. **Use natural language**: "What are my notes about regenerative economics?"
3. **Combine concepts**: "token engineering AND community governance"
4. **Adjust threshold**: Lower score_threshold (0.3-0.4) for more results

### Filter by Metadata:
```bash
# Only notes with specific tags
"filter_metadata": {"tags": ["web3"]}

# Notes from specific date
"filter_metadata": {"modified": "2024-*"}

# Notes from specific folder
"filter_metadata": {"file_path": "projects/*"}
```

## 📈 Performance

- **Query speed**: ~50-100ms
- **Index size**: ~2-3MB per 1000 documents
- **Memory usage**: ~1-2GB (embedding model)
- **Disk space**: Minimal (compressed vectors)

Current setup handles:
- ✅ 1,396 documents indexed
- ✅ Sub-second search
- ✅ Unlimited queries

## 🛠️ Customization

### Change Embedding Model
Edit `.env`:
```bash
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Default: fast, good quality
# EMBEDDING_MODEL=all-mpnet-base-v2  # Slower, better quality
```

Then rebuild:
```bash
docker-compose build embedding-service
docker-compose up -d
```

### Adjust Search Threshold
Lower = more results, potentially less relevant
```bash
"score_threshold": 0.3  # More permissive
"score_threshold": 0.6  # More strict
```

## 🤝 Integration Ideas

### Alfred/Spotlight Alternative
Create a hotkey that:
1. Takes your query
2. Calls the search API
3. Shows results in a picker

### Obsidian Plugin
Build a plugin that:
1. Searches on every note open
2. Shows related notes
3. Suggests links

### Slack Bot
Create a bot that:
1. Searches your personal knowledge base
2. Responds with relevant notes
3. Helps you remember context

## 📞 Support

- **API Docs**: http://localhost:8000/docs
- **Qdrant UI**: http://localhost:6333/dashboard
- **Health Check**: http://localhost:8000/health

---

**Your personal semantic memory is now searchable! 🧠✨**
