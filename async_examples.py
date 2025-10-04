"""
Understanding Async Programming - Examples and Patterns

This module demonstrates the difference between sync and async programming
and shows patterns used in production applications.
"""

import asyncio
import time
from typing import List
import httpx


# ============================================================================
# SYNCHRONOUS VS ASYNCHRONOUS EXAMPLES
# ============================================================================

def sync_sleep_example():
    """Synchronous version - blocks everything."""
    print("Sync: Starting task 1")
    time.sleep(2)  # This blocks the entire thread!
    print("Sync: Task 1 complete")
    
    print("Sync: Starting task 2") 
    time.sleep(2)  # This also blocks!
    print("Sync: Task 2 complete")
    # Total time: ~4 seconds


async def async_sleep_example():
    """Asynchronous version - can do other work while waiting."""
    print("Async: Starting task 1")
    await asyncio.sleep(2)  # This yields control back to the event loop
    print("Async: Task 1 complete")
    
    print("Async: Starting task 2")
    await asyncio.sleep(2)  # Other tasks can run during this wait
    print("Async: Task 2 complete")
    # Still ~4 seconds if run sequentially


async def concurrent_async_example():
    """Async with concurrency - the real power!"""
    
    async def task(name: str, duration: int):
        print(f"Async Concurrent: Starting {name}")
        await asyncio.sleep(duration)
        print(f"Async Concurrent: {name} complete")
        return f"Result from {name}"
    
    # Run both tasks concurrently
    results = await asyncio.gather(
        task("task 1", 2),
        task("task 2", 2)
    )
    # Total time: ~2 seconds (both run at the same time!)
    print(f"All results: {results}")


# ============================================================================
# REAL-WORLD ASYNC PATTERNS
# ============================================================================

async def fetch_url_sync_style(url: str) -> str:
    """This is what NOT to do - blocking in async function."""
    import requests  # This is a synchronous library
    response = requests.get(url)  # This blocks the event loop!
    return response.text


async def fetch_url_async_proper(url: str) -> str:
    """Proper async HTTP request using httpx."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)  # This is truly async
        return response.text


async def fetch_multiple_urls_concurrent(urls: List[str]) -> List[str]:
    """Fetch multiple URLs concurrently - much faster!"""
    
    async def fetch_one(url: str) -> str:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                return f"✅ {url}: {len(response.text)} characters"
            except Exception as e:
                return f"❌ {url}: Error - {str(e)}"
    
    # This runs all requests concurrently
    results = await asyncio.gather(*[fetch_one(url) for url in urls])
    return results


# ============================================================================
# ASYNC PATTERNS IN OUR CHATBOT
# ============================================================================

class AsyncAIService:
    """Example of how we'll structure our AI service with async patterns."""
    
    def __init__(self):
        self.client = None  # Will be httpx.AsyncClient for Azure OpenAI
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
    
    async def generate_response(self, message: str) -> str:
        """Simulate AI response generation."""
        # Simulate network call to Azure OpenAI
        await asyncio.sleep(0.5)  # Simulate network latency
        
        # In real implementation, this would be:
        # response = await self.client.post(azure_openai_url, json=payload)
        
        return f"AI Response to: '{message}'"
    
    async def generate_streaming_response(self, message: str):
        """Simulate streaming response like ChatGPT."""
        response_parts = [
            "I understand you're asking about ",
            f"'{message}'. ",
            "Based on my knowledge of AI engineering careers, ",
            "I'd recommend focusing on..."
        ]
        
        for part in response_parts:
            await asyncio.sleep(0.2)  # Simulate streaming delay
            yield part


async def handle_chat_request(message: str) -> str:
    """Example of how our FastAPI endpoint will work."""
    
    # Multiple async operations can run concurrently
    async with AsyncAIService() as ai_service:
        
        # These could all run concurrently if needed
        tasks = await asyncio.gather(
            ai_service.generate_response(message),
            # save_to_database(message),  # Would be async
            # update_user_context(user_id),  # Would be async
            return_exceptions=True
        )
        
        ai_response = tasks[0]
        return ai_response


# ============================================================================
# WHY ASYNC MATTERS FOR OUR CHATBOT
# ============================================================================

async def chatbot_scenario_demo():
    """
    Demonstrate why async is crucial for a chatbot serving multiple users.
    """
    print("\n🤖 Chatbot Scenario: 3 users asking questions simultaneously")
    
    async def user_conversation(user_id: int, question: str):
        start_time = time.time()
        print(f"👤 User {user_id}: {question}")
        
        # Simulate the full request cycle
        async with AsyncAIService() as ai_service:
            response = await ai_service.generate_response(question)
            
        end_time = time.time()
        print(f"🤖 To User {user_id}: {response} (took {end_time - start_time:.1f}s)")
    
    # Simulate 3 concurrent users
    start_time = time.time()
    await asyncio.gather(
        user_conversation(1, "How do I transition to AI engineering?"),
        user_conversation(2, "What skills are most important for AI roles?"),
        user_conversation(3, "Should I learn PyTorch or TensorFlow first?")
    )
    total_time = time.time() - start_time
    
    print(f"\n📊 Total time to serve all 3 users: {total_time:.1f}s")
    print("🚀 With async: all users get responses ~simultaneously!")
    print("🐌 With sync: users would wait in line, total ~1.5s each")


# ============================================================================
# RUNNING THE EXAMPLES
# ============================================================================

async def main():
    """Run all async examples."""
    print("=" * 60)
    print("🔄 ASYNC PROGRAMMING EXAMPLES")
    print("=" * 60)
    
    print("\n1. Sequential Async (still takes full time):")
    await async_sleep_example()
    
    print("\n2. Concurrent Async (much faster!):")
    await concurrent_async_example()
    
    print("\n3. Real HTTP requests (concurrent):")
    urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1", 
        "https://httpbin.org/delay/1"
    ]
    start_time = time.time()
    results = await fetch_multiple_urls_concurrent(urls)
    end_time = time.time()
    
    for result in results:
        print(f"  {result}")
    print(f"  ⚡ All 3 requests completed in {end_time - start_time:.1f}s")
    
    print("\n4. Chatbot Scenario:")
    await chatbot_scenario_demo()


if __name__ == "__main__":
    # This is how you run async code from a sync context
    asyncio.run(main())