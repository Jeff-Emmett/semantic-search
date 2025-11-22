"""
Test script for semantic search service
"""
import httpx
import asyncio

API_URL = "http://localhost:8000"

async def test_service():
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Semantic Search Service\n")

        # Test 1: Health check
        print("1️⃣ Health check...")
        resp = await client.get(f"{API_URL}/health")
        print(f"   Status: {resp.status_code}")
        print(f"   {resp.json()}\n")

        # Test 2: Index documents
        print("2️⃣ Indexing test documents...")
        docs = [
            {
                "text": "Mycelial networks enable nutrient sharing between trees in forests, creating a wood wide web of fungal communication.",
                "url": "https://example.com/mycelial-networks",
                "title": "Mycelial Networks in Forest Ecosystems",
                "metadata": {"category": "ecology"}
            },
            {
                "text": "Token engineering combines mechanism design with blockchain technology to create incentive-aligned systems.",
                "url": "https://example.com/token-engineering",
                "title": "Introduction to Token Engineering",
                "metadata": {"category": "blockchain"}
            },
            {
                "text": "The Commons Stack builds tools for regenerative economics and community governance.",
                "url": "https://example.com/commons-stack",
                "title": "Commons Stack Overview",
                "metadata": {"category": "dao"}
            }
        ]

        for doc in docs:
            resp = await client.post(f"{API_URL}/index", json=doc)
            print(f"   Indexed: {doc['title']}")
        print()

        # Test 3: Get stats
        print("3️⃣ Collection stats...")
        resp = await client.get(f"{API_URL}/stats")
        print(f"   {resp.json()}\n")

        # Test 4: Semantic search
        print("4️⃣ Testing semantic search...")
        queries = [
            "How do fungi communicate?",
            "What is token design?",
            "Regenerative economics"
        ]

        for query in queries:
            resp = await client.post(
                f"{API_URL}/search",
                json={"query": query, "limit": 2, "score_threshold": 0.3}
            )
            results = resp.json()
            print(f"\n   Query: '{query}'")
            print(f"   Results: {len(results)}")
            for i, result in enumerate(results, 1):
                print(f"     {i}. {result['title']} (score: {result['score']:.3f})")

        print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_service())
