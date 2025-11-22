# 3D Semantic Knowledge Graph Visualization Guide

## 🎨 What You Have

A beautiful **3D force-directed graph** that visualizes semantic relationships between your notes based on embedding similarity.

### Features
- ✅ Interactive 3D navigation
- ✅ Search and highlight functionality
- ✅ Click nodes to see details
- ✅ Color-coded by category/tags
- ✅ Edge thickness shows similarity strength
- ✅ Real-time graph updates

## 🚀 Quick Start

### 1. Start Your Services

First, ensure all services are running:

```bash
cd /home/jeffe/Github/semantic-search
docker-compose up -d
```

Wait ~10 seconds for services to initialize, then verify:

```bash
curl http://localhost:8000/health
```

### 2. Open the Visualization

Open the HTML file in your browser:

```bash
# On WSL, you can open it with:
wslview client/graph_viewer.html

# Or manually open in Windows:
# Navigate to: C:\Users\jeffe\Github\semantic-search\client\graph_viewer.html
```

Alternatively, start a simple HTTP server:

```bash
cd client
python3 -m http.server 8080
```

Then visit: **http://localhost:8080/graph_viewer.html**

## 🎯 How to Use

### Initial View
- Graph loads with 100 random notes from your vault
- Nodes are colored by their first tag/category
- Edges connect semantically similar notes

### Controls

**Search:**
1. Type a query in the search box (e.g., "token engineering")
2. Press Enter or click "Search"
3. Graph updates to show only related notes

**Navigation:**
- **Left-click + drag**: Rotate view
- **Right-click + drag**: Pan
- **Scroll**: Zoom in/out
- **Click node**: View details
- **Drag node**: Reposition

**Buttons:**
- 🔍 **Search**: Execute search query
- 🎲 **Random**: Load random sample of notes
- 🎯 **Reset View**: Return camera to default position

**Sliders:**
- **Node Limit**: How many notes to display (20-200)
- **Similarity Threshold**: Minimum similarity for edges (0.4-0.9)
  - Lower = more connections, denser graph
  - Higher = fewer connections, clearer clusters

### Interpreting the Graph

**Node Size**: All nodes are equal size (can be customized)

**Node Colors**: Automatically colored by category
- Each unique tag gets a different color
- Hover to see note title

**Edge Thickness**: Thicker = higher semantic similarity
- Only edges above threshold are shown
- Hovering shows similarity score

**Clusters**: Notes naturally cluster by topic
- Similar notes group together
- Bridges show cross-topic connections

## 🔍 Search Examples

Try these queries to explore your vault:

```
"regenerative economics"
"token engineering and DAOs"
"coordination mechanisms"
"mycelial networks"
"collective action problems"
```

## 🎨 Visual Features

### Highlighting
- **Red node**: Currently selected
- **Green nodes**: Connected to selected node
- **Default colors**: Category-based

### Node Details Panel
Click any node to see:
- Note title
- Tags
- Text preview
- File path
- Link to open in Obsidian

## ⚙️ API Configuration

The visualization uses these endpoints:

### Get Graph Data
```bash
POST http://localhost:8000/graph

Body:
{
  "query": "optional search query",
  "limit": 100,
  "similarity_threshold": 0.6,
  "filter_metadata": {"source": "obsidian"}
}

Response:
{
  "nodes": [...],
  "edges": [...],
  "node_count": 100,
  "edge_count": 250
}
```

### Test API Directly
```bash
curl -X POST http://localhost:8000/graph \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 50,
    "similarity_threshold": 0.65,
    "filter_metadata": {"source": "obsidian"}
  }' | python3 -m json.tool | head -50
```

## 🛠️ Customization

Edit `client/graph_viewer.html` to customize:

### Change Node Appearance
```javascript
graph.nodeVal(node => {
    // Size by number of tags
    return node.tags.length + 1;
})
```

### Change Colors
```javascript
graph.nodeColor(node => {
    // Custom color mapping
    if (node.tags.includes('web3')) return '#ff4444';
    if (node.tags.includes('dao')) return '#44ff44';
    return '#4a9eff';
})
```

### Change Force Parameters
```javascript
graph
    .d3Force('charge').strength(-200)  // Repulsion strength
    .d3Force('link').distance(30);     // Link length
```

## 🎭 Tips for Better Visualization

### 1. Find the Right Threshold
- **0.4-0.5**: See broader connections, more edges
- **0.6-0.7**: Balanced view, clear clusters
- **0.8-0.9**: Only strongest connections, sparse

### 2. Adjust Node Limit
- **20-50**: Fast, focused view
- **100**: Good balance
- **150-200**: Full context, slower

### 3. Use Search Strategically
- Search broad concepts to see clusters
- Search specific terms to find exact matches
- Search combined concepts to see crossover

### 4. Navigate Effectively
- Start zoomed out to see overall structure
- Zoom in on interesting clusters
- Click nodes to explore connections

## 🐛 Troubleshooting

### Graph Won't Load
```bash
# Check if API is running
curl http://localhost:8000/health

# Check if services are up
docker-compose ps

# Restart services
docker-compose restart

# Check browser console for errors (F12)
```

### No Edges Showing
- Lower the similarity threshold (try 0.4)
- Increase node limit to find more connections
- Check that documents have been indexed

### Performance Issues
- Reduce node limit (try 50)
- Increase similarity threshold (try 0.7)
- Close other browser tabs
- Restart browser

### CORS Errors
Make sure the API has CORS enabled (it should by default).
Check `services/search_api.py` for:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    ...
)
```

## 🚀 Advanced Use Cases

### 1. Topic Exploration
1. Search for a broad topic
2. Identify main clusters
3. Click nodes in each cluster
4. Discover connections between subtopics

### 2. Finding Gaps
1. Load full graph (limit=200)
2. Look for isolated nodes
3. These are unique/underconnected topics
4. Good candidates for new connections

### 3. Research Pathways
1. Search starting concept
2. Click connected nodes
3. Follow similarity chains
4. Discover unexpected connections

### 4. Tag Analysis
1. Load random sample
2. Observe color clusters
3. See which tags group together
4. Identify tag synonyms or overlaps

## 📊 Graph Statistics

The visualization shows:
- **Node Count**: Total notes displayed
- **Connections**: Total edges (similarity links)
- **Categories**: Unique first tags

Higher edge count = more interconnected knowledge
Lower edge count = more distinct topic areas

## 🎨 Color Palette

Default colors are auto-generated by category.
Common mappings:
- Blue shades: General/uncategorized
- Green: DAO/governance
- Purple: Token engineering
- Orange: Economics
- Red: Currently selected

## 📱 Mobile/Tablet Support

The visualization works on touch devices:
- Pinch to zoom
- Drag to rotate
- Tap nodes for details
- May be slower with large graphs

## 🔮 Future Enhancements

Potential additions:
- Time-based filtering (show notes from date range)
- Tag filtering (show only specific categories)
- Export graph as image
- Save/load graph layouts
- Annotation mode
- Path highlighting between two nodes
- Degree centrality visualization
- Community detection coloring

## 💡 Interpretation Guide

### Dense Clusters
- Well-explored topics
- Lots of related notes
- Central to your thinking

### Bridge Nodes
- Connect different topics
- Integration points
- Interdisciplinary concepts

### Isolated Nodes
- Unique ideas
- Underexplored topics
- Potential for expansion

### Star Patterns
- Hub concepts
- Referenced by many notes
- Core themes

---

**Your knowledge is now visible in 3D space! 🌌**
