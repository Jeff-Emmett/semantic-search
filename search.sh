#!/bin/bash
# Quick semantic search of your Obsidian vault
# Usage: ./search.sh "your search query"

if [ -z "$1" ]; then
    echo "Usage: ./search.sh \"your search query\""
    echo "Example: ./search.sh \"token engineering\""
    exit 1
fi

QUERY="$*"

echo "🔍 Searching for: $QUERY"
echo ""

curl -s -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$QUERY\", \"limit\": 5, \"score_threshold\": 0.4, \"filter_metadata\": {\"source\": \"obsidian\"}}" \
  | python3 -c "
import sys, json
results = json.load(sys.stdin)

if not results:
    print('No results found. Try lowering the score threshold or different terms.')
    sys.exit(0)

for i, r in enumerate(results, 1):
    print(f\"{i}. {r['title']} (score: {r['score']:.2f})\")
    print(f\"   📁 {r['metadata'].get('file_path', 'N/A')}\")

    tags = r['metadata'].get('tags', [])
    if tags:
        print(f\"   🏷️  {', '.join('#' + t for t in tags[:5])}\")

    links = r['metadata'].get('links', [])
    if links:
        print(f\"   🔗 Links to: {', '.join(links[:3])}\")

    preview = r['text'][:150].replace('\n', ' ')
    print(f\"   📝 {preview}...\")
    print(f\"   🔗 {r['url']}\")
    print()
"
