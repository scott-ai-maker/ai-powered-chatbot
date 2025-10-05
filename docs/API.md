# 🔌 API Documentation

> **Comprehensive API Reference** for the AI Career Mentor Chatbot system

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URLs](#base-urls)
- [Chat Endpoints](#chat-endpoints)
- [Health Endpoints](#health-endpoints)
- [Monitoring Endpoints](#monitoring-endpoints)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [SDK Examples](#sdk-examples)

## 🎯 Overview

The AI Career Mentor Chatbot provides a RESTful API built with FastAPI, offering:

- **🤖 AI-Powered Conversations**: GPT-4 enhanced career guidance
- **🔍 Knowledge Retrieval**: RAG-based information lookup
- **📊 Real-Time Monitoring**: System health and performance metrics
- **🔒 Secure Access**: Bearer token authentication with rate limiting

### API Specifications
- **Protocol**: HTTPS/HTTP
- **Format**: JSON
- **Authentication**: Bearer Token
- **Documentation**: OpenAPI 3.0 (Swagger)
- **Rate Limiting**: Token bucket algorithm

## 🔐 Authentication

### Bearer Token Authentication

All protected endpoints require a Bearer token in the Authorization header:

```http
Authorization: Bearer <your-access-token>
```

### Token Management

```bash
# Example token request (implementation-specific)
curl -X POST "https://api.your-domain.com/auth/token" \
     -H "Content-Type: application/json" \
     -d '{"username": "user", "password": "pass"}'
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## 🌐 Base URLs

| Environment | Base URL | Description |
|-------------|----------|-------------|
| **Production** | `https://ai-chatbot.azurecontainerapps.io` | Production API |
| **Staging** | `https://ai-chatbot-staging.azurecontainerapps.io` | Staging environment |
| **Development** | `http://localhost:8000` | Local development |

## 💬 Chat Endpoints

### Send Chat Message

Create a conversation with the AI assistant.

**Endpoint**: `POST /api/v1/chat/message`

**Request Body**:
```json
{
  "message": "How do I prepare for an AI engineering interview?",
  "session_id": "uuid-session-identifier",
  "context": {
    "user_background": "software_developer",
    "experience_level": "mid_level",
    "specific_interests": ["machine_learning", "nlp"]
  },
  "options": {
    "include_sources": true,
    "max_tokens": 500,
    "temperature": 0.7
  }
}
```

**Response** (200 OK):
```json
{
  "response": "To prepare for an AI engineering interview, focus on these key areas:\n\n1. **Technical Foundations**:\n   - Machine learning algorithms and their applications\n   - Deep learning frameworks (TensorFlow, PyTorch)\n   - Data preprocessing and feature engineering\n\n2. **Practical Experience**:\n   - Build end-to-end ML projects\n   - Understand model deployment and monitoring\n   - Practice coding problems in Python\n\n3. **System Design**:\n   - ML system architecture\n   - Scalability considerations\n   - Data pipeline design\n\nWould you like me to elaborate on any specific area?",
  "session_id": "uuid-session-identifier",
  "message_id": "msg-uuid-identifier",
  "metadata": {
    "tokens_used": 245,
    "response_time": 1.23,
    "model_used": "gpt-4",
    "knowledge_sources": [
      {
        "title": "AI Interview Guide",
        "relevance_score": 0.92,
        "source": "career_resources/ai_interview_prep.pdf"
      }
    ]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "Invalid request",
  "detail": "Message cannot be empty",
  "code": "INVALID_MESSAGE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Retrieve Chat History

Get conversation history for a specific session.

**Endpoint**: `GET /api/v1/chat/history/{session_id}`

**Path Parameters**:
- `session_id` (string): Unique session identifier

**Query Parameters**:
- `limit` (integer, optional): Maximum number of messages (default: 50)
- `offset` (integer, optional): Number of messages to skip (default: 0)
- `include_metadata` (boolean, optional): Include message metadata (default: true)

**Request**:
```http
GET /api/v1/chat/history/uuid-session-id?limit=10&include_metadata=true
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "session_id": "uuid-session-id",
  "total_messages": 25,
  "messages": [
    {
      "message_id": "msg-uuid-1",
      "role": "user",
      "content": "How do I prepare for an AI engineering interview?",
      "timestamp": "2024-01-15T10:30:00Z",
      "metadata": {
        "tokens": 12
      }
    },
    {
      "message_id": "msg-uuid-2",
      "role": "assistant",
      "content": "To prepare for an AI engineering interview...",
      "timestamp": "2024-01-15T10:30:01Z",
      "metadata": {
        "tokens_used": 245,
        "response_time": 1.23,
        "knowledge_sources": ["ai_interview_prep.pdf"]
      }
    }
  ],
  "pagination": {
    "limit": 10,
    "offset": 0,
    "has_more": true
  }
}
```

### Create Chat Session

Initialize a new conversation session.

**Endpoint**: `POST /api/v1/chat/session`

**Request Body**:
```json
{
  "user_context": {
    "background": "software_developer",
    "experience_level": "mid_level",
    "career_goals": ["ai_engineer", "machine_learning"]
  },
  "preferences": {
    "response_style": "detailed",
    "include_examples": true,
    "max_response_length": "medium"
  }
}
```

**Response** (201 Created):
```json
{
  "session_id": "new-uuid-session-id",
  "created_at": "2024-01-15T10:30:00Z",
  "expires_at": "2024-01-15T11:30:00Z",
  "context": {
    "background": "software_developer",
    "experience_level": "mid_level",
    "career_goals": ["ai_engineer", "machine_learning"]
  }
}
```

### Delete Chat Session

Remove a conversation session and its history.

**Endpoint**: `DELETE /api/v1/chat/session/{session_id}`

**Response** (204 No Content)

## 🏥 Health Endpoints

### Basic Health Check

Check if the application is running.

**Endpoint**: `GET /health`

**Authentication**: None required

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "uptime": "2 days, 14:23:45"
}
```

### Readiness Probe

Check if the application is ready to serve traffic.

**Endpoint**: `GET /health/ready`

**Authentication**: None required

**Response** (200 OK):
```json
{
  "status": "ready",
  "checks": {
    "database": "healthy",
    "azure_openai": "healthy",
    "cognitive_search": "healthy",
    "external_dependencies": "healthy"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Liveness Probe

Check if the application is alive (for container orchestration).

**Endpoint**: `GET /health/live`

**Authentication**: None required

**Response** (200 OK):
```json
{
  "status": "alive",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 📊 Monitoring Endpoints

### System Metrics

Get current system performance metrics.

**Endpoint**: `GET /monitoring/metrics`

**Authentication**: Admin Bearer Token required

**Response** (200 OK):
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "metrics": {
    "requests": {
      "total": 150234,
      "rate_per_minute": 45.2,
      "average_response_time": 1.23
    },
    "ai_usage": {
      "total_tokens": 2543210,
      "tokens_per_minute": 890,
      "cost_estimate_usd": 15.67
    },
    "system": {
      "cpu_usage": 45.2,
      "memory_usage": 67.8,
      "active_sessions": 123
    },
    "errors": {
      "error_rate": 0.02,
      "total_errors": 45,
      "errors_by_type": {
        "timeout": 20,
        "validation": 15,
        "server_error": 10
      }
    }
  }
}
```

### Real-Time Dashboard

Access the monitoring dashboard (HTML interface).

**Endpoint**: `GET /monitoring/dashboard`

**Authentication**: Admin Bearer Token required

**Response**: HTML dashboard with live metrics visualization

## ⚠️ Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
  "error": "Human-readable error message",
  "detail": "Detailed error description",
  "code": "ERROR_CODE_IDENTIFIER", 
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req-uuid-identifier"
}
```

### HTTP Status Codes

| Status Code | Description | Usage |
|-------------|-------------|-------|
| `200` | OK | Successful request |
| `201` | Created | Resource created successfully |
| `204` | No Content | Successful deletion |
| `400` | Bad Request | Invalid request data |
| `401` | Unauthorized | Missing or invalid authentication |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource not found |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server error |
| `503` | Service Unavailable | Temporary service outage |

### Common Error Codes

| Error Code | Description | Resolution |
|------------|-------------|------------|
| `INVALID_TOKEN` | Authentication token is invalid | Obtain a new access token |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Wait before making more requests |
| `SESSION_NOT_FOUND` | Chat session doesn't exist | Create a new session |
| `MESSAGE_TOO_LONG` | Message exceeds length limit | Shorten the message |
| `AI_SERVICE_UNAVAILABLE` | AI service is temporarily down | Retry after a few minutes |
| `INSUFFICIENT_TOKENS` | Not enough tokens for request | Check token balance |

## 🚦 Rate Limiting

### Rate Limit Headers

All responses include rate limiting information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1705320600
X-RateLimit-Window: 3600
```

### Rate Limits by Endpoint

| Endpoint | Limit | Window | Scope |
|----------|--------|--------|-------|
| `/api/v1/chat/message` | 100 requests | 1 hour | Per user |
| `/api/v1/chat/history/*` | 200 requests | 1 hour | Per user |
| `/api/v1/chat/session` | 20 requests | 1 hour | Per user |
| `/health/*` | 1000 requests | 1 minute | Global |
| `/monitoring/*` | 50 requests | 1 minute | Per admin |

### Rate Limit Exceeded Response

```json
{
  "error": "Rate limit exceeded",
  "detail": "You have exceeded the rate limit of 100 requests per hour",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 3600,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 💻 SDK Examples

### Python SDK Example

```python
import requests
import json
from typing import Dict, Any

class ChatbotAPIClient:
    def __init__(self, base_url: str, access_token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def send_message(self, message: str, session_id: str, **kwargs) -> Dict[str, Any]:
        """Send a message to the chatbot."""
        url = f"{self.base_url}/api/v1/chat/message"
        payload = {
            "message": message,
            "session_id": session_id,
            **kwargs
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_chat_history(self, session_id: str, limit: int = 50) -> Dict[str, Any]:
        """Retrieve chat history for a session."""
        url = f"{self.base_url}/api/v1/chat/history/{session_id}"
        params = {"limit": limit}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def create_session(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new chat session."""
        url = f"{self.base_url}/api/v1/chat/session"
        payload = {"user_context": user_context}
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

# Usage example
client = ChatbotAPIClient(
    base_url="https://ai-chatbot.azurecontainerapps.io",
    access_token="your-access-token"
)

# Create a session
session = client.create_session({
    "background": "software_developer",
    "experience_level": "mid_level"
})

# Send a message
response = client.send_message(
    message="How do I transition into AI engineering?",
    session_id=session["session_id"]
)

print(f"AI Response: {response['response']}")
```

### JavaScript/Node.js SDK Example

```javascript
class ChatbotAPIClient {
    constructor(baseUrl, accessToken) {
        this.baseUrl = baseUrl;
        this.accessToken = accessToken;
    }

    async sendMessage(message, sessionId, options = {}) {
        const response = await fetch(`${this.baseUrl}/api/v1/chat/message`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message,
                session_id: sessionId,
                ...options
            })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    }

    async getChatHistory(sessionId, limit = 50) {
        const url = new URL(`${this.baseUrl}/api/v1/chat/history/${sessionId}`);
        url.searchParams.append('limit', limit.toString());

        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${this.accessToken}`
            }
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    }

    async createSession(userContext) {
        const response = await fetch(`${this.baseUrl}/api/v1/chat/session`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_context: userContext })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        return await response.json();
    }
}

// Usage example
const client = new ChatbotAPIClient(
    'https://ai-chatbot.azurecontainerapps.io',
    'your-access-token'
);

async function example() {
    try {
        // Create a session
        const session = await client.createSession({
            background: 'software_developer',
            experience_level: 'mid_level'
        });

        // Send a message
        const response = await client.sendMessage(
            'What skills should I focus on for AI engineering?',
            session.session_id
        );

        console.log('AI Response:', response.response);
    } catch (error) {
        console.error('Error:', error.message);
    }
}

example();
```

### cURL Examples

**Create Session**:
```bash
curl -X POST "https://ai-chatbot.azurecontainerapps.io/api/v1/chat/session" \
     -H "Authorization: Bearer your-access-token" \
     -H "Content-Type: application/json" \
     -d '{
       "user_context": {
         "background": "software_developer",
         "experience_level": "mid_level"
       }
     }'
```

**Send Message**:
```bash
curl -X POST "https://ai-chatbot.azurecontainerapps.io/api/v1/chat/message" \
     -H "Authorization: Bearer your-access-token" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "How do I prepare for machine learning interviews?",
       "session_id": "uuid-session-id",
       "options": {
         "include_sources": true,
         "max_tokens": 500
       }
     }'
```

**Get Chat History**:
```bash
curl -X GET "https://ai-chatbot.azurecontainerapps.io/api/v1/chat/history/uuid-session-id?limit=10" \
     -H "Authorization: Bearer your-access-token"
```

---

## 📞 Support & Resources

- **🐛 Report Issues**: [GitHub Issues](https://github.com/scott-ai-maker/ai-powered-chatbot/issues)
- **📖 Interactive Docs**: `https://your-domain.com/docs`
- **🔍 API Explorer**: `https://your-domain.com/redoc`
- **💬 Community**: [GitHub Discussions](https://github.com/scott-ai-maker/ai-powered-chatbot/discussions)

For additional support or enterprise licensing, contact: **scott.ai.maker@example.com**