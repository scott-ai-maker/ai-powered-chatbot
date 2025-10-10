"""
ASYNC + PYDANTIC: How They Work Together in Our Chatbot

This example shows how async programming and Pydantic settings combine
to create a production-ready system like our AI Career Mentor Chatbot.
"""

import asyncio
import time
from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import httpx


# ============================================================================
# 1. PYDANTIC MODELS FOR OUR DATA
# ============================================================================


class ChatMessage(BaseModel):
    """A chat message with validation."""

    content: str = Field(..., min_length=1, max_length=4000)
    user_id: str
    timestamp: Optional[float] = None

    def model_post_init(self, __context):
        """Set timestamp after model creation."""
        if self.timestamp is None:
            self.timestamp = time.time()


class ChatResponse(BaseModel):
    """AI response with metadata."""

    message: str
    confidence: float = Field(ge=0.0, le=1.0)
    processing_time: float
    model_used: str


class ConversationSession(BaseModel):
    """A conversation session with multiple messages."""

    session_id: str
    user_id: str
    messages: List[ChatMessage] = []
    created_at: float = Field(default_factory=time.time)


# ============================================================================
# 2. PYDANTIC SETTINGS FOR CONFIGURATION
# ============================================================================


class ChatbotSettings(BaseSettings):
    """Our chatbot configuration using Pydantic Settings."""

    # AI Service
    openai_endpoint: str = Field(..., env="OPENAI_ENDPOINT")
    openai_key: str = Field(..., env="OPENAI_KEY")
    model_name: str = Field(default="gpt-4", env="MODEL_NAME")
    max_tokens: int = Field(default=1000, env="MAX_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")

    # Performance
    timeout_seconds: float = Field(default=30.0, env="TIMEOUT_SECONDS")
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")

    class Config:
        env_file = ".env"


# ============================================================================
# 3. ASYNC SERVICE CLASS COMBINING BOTH PATTERNS
# ============================================================================


class AsyncChatbotService:
    """
    Production-ready async chatbot service that combines:
    - Pydantic Settings for configuration
    - Pydantic Models for data validation
    - Async programming for performance
    """

    def __init__(self, settings: ChatbotSettings):
        self.settings = settings
        self.client: Optional[httpx.AsyncClient] = None
        self.active_sessions: dict[str, ConversationSession] = {}

        # Semaphore to limit concurrent requests
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_requests)

    async def __aenter__(self):
        """Async context manager - initialize HTTP client."""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.settings.timeout_seconds),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=5),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager - cleanup HTTP client."""
        if self.client:
            await self.client.aclose()

    async def process_message(self, message: ChatMessage) -> ChatResponse:
        """
        Process a single message with async AI call.

        This is where the magic happens - we use:
        1. Pydantic validation on the input message
        2. Async HTTP call to AI service
        3. Pydantic validation on the response
        """
        start_time = time.time()

        # Use semaphore to limit concurrent requests
        async with self.semaphore:
            # Simulate AI service call (in real app, this would be Azure OpenAI)
            ai_response = await self._call_ai_service(message.content)

            processing_time = time.time() - start_time

            # Return validated response
            return ChatResponse(
                message=ai_response,
                confidence=0.95,
                processing_time=processing_time,
                model_used=self.settings.model_name,
            )

    async def _call_ai_service(self, message: str) -> str:
        """Simulate async call to AI service."""
        # Simulate network latency
        await asyncio.sleep(0.5)

        # In real implementation, this would be:
        # response = await self.client.post(
        #     self.settings.openai_endpoint,
        #     headers={"Authorization": f"Bearer {self.settings.openai_key}"},
        #     json={
        #         "model": self.settings.model_name,
        #         "messages": [{"role": "user", "content": message}],
        #         "max_tokens": self.settings.max_tokens,
        #         "temperature": self.settings.temperature
        #     }
        # )
        # return response.json()["choices"][0]["message"]["content"]

        return f"AI response to: '{message}' (using {self.settings.model_name})"

    async def handle_conversation(
        self, user_id: str, messages: List[str]
    ) -> List[ChatResponse]:
        """Handle multiple messages concurrently - demonstrates async power."""

        # Convert strings to validated ChatMessage objects
        chat_messages = [ChatMessage(content=msg, user_id=user_id) for msg in messages]

        # Process all messages concurrently - this is the async magic!
        responses = await asyncio.gather(
            *[self.process_message(msg) for msg in chat_messages],
            return_exceptions=True,
        )

        # Filter out any exceptions and return successful responses
        successful_responses = [
            resp for resp in responses if isinstance(resp, ChatResponse)
        ]

        return successful_responses


# ============================================================================
# 4. DEMONSTRATION: CONCURRENT USERS WITH VALIDATION
# ============================================================================


async def demonstrate_production_patterns():
    """Show how async + Pydantic work together in a realistic scenario."""

    print("🤖 PRODUCTION CHATBOT SIMULATION")
    print("=" * 50)

    # Create settings (normally loaded from environment)
    settings = ChatbotSettings(
        openai_endpoint="https://demo-openai.com",
        openai_key="demo-key-123",
        model_name="gpt-4",
        max_concurrent_requests=5,
    )

    print(
        f"✅ Settings loaded: {settings.model_name} with {settings.max_concurrent_requests} max concurrent requests"
    )

    # Initialize async service
    async with AsyncChatbotService(settings) as chatbot:
        # Simulate 3 users with multiple questions each
        user_scenarios = [
            {
                "user_id": "user_1",
                "messages": [
                    "How do I transition to AI engineering?",
                    "What skills should I learn first?",
                    "Which programming languages are most important?",
                ],
            },
            {
                "user_id": "user_2",
                "messages": [
                    "Should I get a PhD for AI roles?",
                    "What's the salary range for AI engineers?",
                ],
            },
            {
                "user_id": "user_3",
                "messages": [
                    "How important is math for AI engineering?",
                    "Can I transition from web development?",
                    "What projects should I build?",
                    "How do I prepare for AI interviews?",
                ],
            },
        ]

        # Process all users concurrently - this demonstrates the power of async
        start_time = time.time()

        # Each user's conversation runs concurrently
        user_tasks = [
            chatbot.handle_conversation(scenario["user_id"], scenario["messages"])
            for scenario in user_scenarios
        ]

        all_responses = await asyncio.gather(*user_tasks)

        total_time = time.time() - start_time

        # Display results
        total_messages = sum(len(scenario["messages"]) for scenario in user_scenarios)
        print("\n📊 RESULTS:")
        print(f"  • Total users: {len(user_scenarios)}")
        print(f"  • Total messages: {total_messages}")
        print(f"  • Total time: {total_time:.2f}s")
        print(f"  • Average time per message: {total_time / total_messages:.2f}s")
        print(
            f"  • Messages processed concurrently: {settings.max_concurrent_requests}"
        )

        # Show some responses
        print("\n💬 SAMPLE RESPONSES:")
        for i, user_responses in enumerate(all_responses):
            user_id = user_scenarios[i]["user_id"]
            print(f"  {user_id}: {len(user_responses)} responses processed")
            if user_responses:
                sample_response = user_responses[0]
                print(f"    Sample: {sample_response.message[:50]}...")
                print(f"    Processing time: {sample_response.processing_time:.2f}s")


# ============================================================================
# 5. KEY INSIGHTS FOR YOUR LEARNING
# ============================================================================


def explain_the_patterns():
    """Explain what makes this production-ready."""

    print("\n🎯 KEY PATTERNS IN OUR CHATBOT")
    print("=" * 40)

    insights = [
        "🔧 Pydantic Settings: Type-safe config from environment variables",
        "📝 Pydantic Models: Automatic validation of all data flowing through system",
        "⚡ Async Programming: Handle multiple users simultaneously",
        "🛡️ Error Handling: Graceful handling of failures with asyncio.gather",
        "📊 Resource Management: Semaphore limits concurrent requests to protect APIs",
        "🧹 Context Managers: Proper async resource cleanup (HTTP clients, etc.)",
        "🏭 Production Patterns: Same patterns used by Netflix, Uber, etc.",
    ]

    for insight in insights:
        print(f"  {insight}")

    print("\n🚀 IN OUR ACTUAL CHATBOT:")
    print("  • FastAPI endpoints will use these same async patterns")
    print("  • Azure OpenAI calls will be async HTTP requests")
    print("  • Pydantic models will validate all API requests/responses")
    print("  • Settings will load Azure credentials from environment")
    print("  • Multiple users can chat simultaneously without blocking")


# ============================================================================
# MAIN EXECUTION
# ============================================================================


async def main():
    """Run the production patterns demonstration."""
    await demonstrate_production_patterns()
    explain_the_patterns()


if __name__ == "__main__":
    asyncio.run(main())
