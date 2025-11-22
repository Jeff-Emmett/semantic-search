/**
 * Canvas integration for semantic search
 * Add this to your tldraw hyperindexing tool
 */

const SEARCH_API_URL = 'http://localhost:8000';

interface SearchResult {
  id: string;
  text: string;
  url: string;
  title: string;
  score: number;
  metadata: Record<string, any>;
}

interface SearchOptions {
  limit?: number;
  scoreThreshold?: number;
  useExa?: boolean;
}

// Search API client
export class SemanticSearchClient {
  private baseUrl: string;

  constructor(baseUrl: string = SEARCH_API_URL) {
    this.baseUrl = baseUrl;
  }

  async search(
    query: string,
    options: SearchOptions = {}
  ): Promise<SearchResult[]> {
    const response = await fetch(`${this.baseUrl}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        limit: options.limit || 10,
        score_threshold: options.scoreThreshold || 0.5,
        use_exa: options.useExa || false,
      }),
    });

    if (!response.ok) {
      throw new Error(`Search failed: ${response.statusText}`);
    }

    return response.json();
  }

  async indexDocument(doc: {
    text: string;
    url?: string;
    title?: string;
    metadata?: Record<string, any>;
  }): Promise<{ id: string; status: string }> {
    const response = await fetch(`${this.baseUrl}/index`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(doc),
    });

    if (!response.ok) {
      throw new Error(`Indexing failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getStats(): Promise<{
    total_documents: number;
    collection_name: string;
  }> {
    const response = await fetch(`${this.baseUrl}/stats`);
    return response.json();
  }
}

// Canvas integration functions
export class CanvasSemanticSearch {
  private client: SemanticSearchClient;
  private editor: any; // tldraw Editor type

  constructor(editor: any) {
    this.client = new SemanticSearchClient();
    this.editor = editor;
  }

  /**
   * Auto-index a canvas node when created/updated
   */
  async autoIndexNode(shape: any): Promise<void> {
    const text = this.extractTextFromShape(shape);
    if (!text || text.length < 20) return;

    try {
      await this.client.indexDocument({
        text,
        title: text.substring(0, 100),
        metadata: {
          canvas_id: this.editor.getCurrentPageId(),
          shape_id: shape.id,
          shape_type: shape.type,
          indexed_from: 'canvas',
          timestamp: new Date().toISOString(),
        },
      });
      console.log(`Indexed node: ${shape.id}`);
    } catch (error) {
      console.error('Auto-indexing failed:', error);
    }
  }

  /**
   * Enrich a node with semantically related content
   */
  async enrichNode(shape: any, options: SearchOptions = {}): Promise<void> {
    const text = this.extractTextFromShape(shape);
    if (!text) return;

    try {
      const results = await this.client.search(text, {
        limit: 5,
        scoreThreshold: 0.6,
        ...options,
      });

      // Create linked nodes around the original
      this.createRelatedNodes(shape, results);
    } catch (error) {
      console.error('Node enrichment failed:', error);
    }
  }

  /**
   * Search canvas and create visualization
   */
  async searchAndVisualize(query: string): Promise<void> {
    const results = await this.client.search(query, {
      limit: 10,
      scoreThreshold: 0.5,
    });

    // Create central query node
    const centerX = 0;
    const centerY = 0;

    this.editor.createShape({
      type: 'text',
      x: centerX,
      y: centerY,
      props: { text: `🔍 ${query}` },
    });

    // Create result nodes in a circle
    const radius = 300;
    results.forEach((result, i) => {
      const angle = (i / results.length) * 2 * Math.PI;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);

      this.editor.createShape({
        type: 'note',
        x,
        y,
        props: {
          text: `${result.title}\n\nScore: ${result.score.toFixed(2)}\n${result.url}`,
          color: this.scoreToColor(result.score),
        },
      });
    });
  }

  // Helper methods
  private extractTextFromShape(shape: any): string {
    if (shape.type === 'text') return shape.props.text;
    if (shape.type === 'note') return shape.props.text;
    if (shape.type === 'geo' && shape.props.text) return shape.props.text;
    return '';
  }

  private createRelatedNodes(sourceShape: any, results: SearchResult[]): void {
    const sourceX = sourceShape.x;
    const sourceY = sourceShape.y;
    const spacing = 200;

    results.forEach((result, i) => {
      this.editor.createShape({
        type: 'note',
        x: sourceX + (i + 1) * spacing,
        y: sourceY,
        props: {
          text: `${result.title}\n\n${result.text.substring(0, 200)}...\n\n${result.url}`,
          color: 'light-blue',
          size: 's',
        },
      });

      // Create arrow from source to result
      this.editor.createShape({
        type: 'arrow',
        props: {
          start: { x: sourceX, y: sourceY },
          end: { x: sourceX + (i + 1) * spacing, y: sourceY },
        },
      });
    });
  }

  private scoreToColor(score: number): string {
    if (score > 0.8) return 'green';
    if (score > 0.6) return 'blue';
    if (score > 0.4) return 'yellow';
    return 'grey';
  }
}

// Usage example
/*
import { CanvasSemanticSearch } from './canvas_integration';

const searchTool = new CanvasSemanticSearch(editor);

// Auto-index on node creation
editor.on('shape-change', async (change) => {
  if (change.type === 'create') {
    await searchTool.autoIndexNode(change.shape);
  }
});

// Enrich selected node
const selectedShape = editor.getSelectedShapes()[0];
if (selectedShape) {
  await searchTool.enrichNode(selectedShape);
}

// Search and visualize
await searchTool.searchAndVisualize('mycelial coordination');
*/
