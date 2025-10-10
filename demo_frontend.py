"""
Demo script for the AI Career Mentor Chatbot.

This script demonstrates the frontend functionality even without
Azure OpenAI credentials by simulating the backend responses.
"""

import time
from datetime import datetime
from typing import Dict


class MockChatbotClient:
    """Mock client that simulates AI responses for demo purposes."""

    def __init__(self):
        self.conversation_history = []
        self.demo_responses = {
            "transition": "Great question! Transitioning to AI engineering from another field is definitely possible. Here's what I recommend:\n\n🎯 **Start with the fundamentals:**\n- Python programming (if you're not already proficient)\n- Statistics and linear algebra basics\n- Machine learning concepts\n\n📚 **Learning path:**\n1. Take Andrew Ng's ML course on Coursera\n2. Practice with scikit-learn and basic projects\n3. Learn PyTorch or TensorFlow\n4. Build 2-3 portfolio projects\n\n💼 **Leverage your existing skills:**\n- Software engineering → Focus on MLOps and production ML\n- Data analysis → Emphasize feature engineering and model interpretation\n- Domain expertise → Apply AI to problems in your field\n\nWhat's your current background? I can give more specific advice!",
            "skills": "For AI engineering roles, here are the most important skills to develop:\n\n🐍 **Programming & Tools:**\n- Python (essential) - pandas, numpy, scikit-learn\n- SQL for data manipulation\n- Git/GitHub for version control\n- Docker for containerization\n- Cloud platforms (AWS, Azure, or GCP)\n\n🧠 **ML/AI Fundamentals:**\n- Supervised & unsupervised learning\n- Deep learning basics (neural networks)\n- Model evaluation and validation\n- Feature engineering techniques\n\n⚡ **Production Skills:**\n- MLOps practices\n- Model deployment and monitoring\n- API development (FastAPI/Flask)\n- Data pipelines and workflow orchestration\n\n📊 **Math & Statistics:**\n- Linear algebra (vectors, matrices)\n- Statistics and probability\n- Calculus basics (for deep learning)\n\nStart with Python and ML fundamentals, then build projects that demonstrate these skills!",
            "salary": "AI engineering salaries vary significantly by location, experience, and company size:\n\n💰 **Salary Ranges (USD, 2024):**\n\n**Entry Level (0-2 years):**\n- $80k-120k at smaller companies\n- $130k-180k at big tech (Google, Meta, etc.)\n- $90k-140k at mid-size companies\n\n**Mid Level (3-5 years):**\n- $120k-180k at smaller companies\n- $200k-350k at big tech\n- $140k-220k at mid-size companies\n\n**Senior Level (5+ years):**\n- $160k-250k at smaller companies\n- $350k-600k+ at big tech\n- $200k-300k at mid-size companies\n\n📍 **Location multipliers:**\n- San Francisco/Seattle: 1.3-1.5x\n- New York: 1.2-1.3x\n- Austin/Denver: 1.0-1.1x\n- Remote: 0.8-1.1x depending on company\n\n💡 **Negotiation tips:**\n- Research company-specific ranges on levels.fyi\n- Highlight unique skills (domain expertise + AI)\n- Consider total compensation, not just base salary\n\nWhat location are you targeting?",
            "default": "That's an excellent question about AI engineering careers! While I don't have real Azure OpenAI access in this demo, I'd love to help you with:\n\n🎯 **Career Planning:**\n- Transition strategies from your current field\n- Skill development roadmaps\n- Timeline expectations for career change\n\n📚 **Learning Resources:**\n- Best courses and certifications\n- Hands-on project recommendations\n- Books and online resources\n\n💼 **Job Search:**\n- Resume optimization for AI roles\n- Interview preparation strategies\n- Portfolio project ideas\n\n💰 **Compensation:**\n- Salary expectations by location and level\n- Negotiation strategies\n- Benefits and equity considerations\n\nWhat specific aspect of AI engineering careers would you like to explore? I can provide detailed guidance based on current industry trends and best practices!",
        }

    def check_health_sync(self) -> Dict:
        """Simulate backend health check."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "0.1.0-demo",
            "azure_openai_status": "demo_mode",
            "database_status": "connected",
        }

    def send_message(self, message: str, conversation_id: str, user_id: str) -> Dict:
        """Simulate AI response generation."""
        # Add some realistic delay
        time.sleep(1.5)

        # Store user message
        self.conversation_history.append(
            {
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Generate response based on keywords
        response_text = self._generate_demo_response(message)

        # Store AI response
        self.conversation_history.append(
            {
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.now().isoformat(),
            }
        )

        return {
            "id": f"demo_response_{len(self.conversation_history)}",
            "message": response_text,
            "conversation_id": conversation_id,
            "model_used": "demo-ai-mentor",
            "processing_time_ms": 1500,
            "confidence_score": 0.95,
            "response_type": "career_advice",
        }

    def _generate_demo_response(self, message: str) -> str:
        """Generate contextual demo response based on message content."""
        message_lower = message.lower()

        if any(
            word in message_lower
            for word in ["transition", "switch", "change career", "move to ai"]
        ):
            return self.demo_responses["transition"]
        elif any(
            word in message_lower
            for word in ["skills", "learn", "technology", "programming"]
        ):
            return self.demo_responses["skills"]
        elif any(
            word in message_lower
            for word in ["salary", "pay", "money", "compensation", "earn"]
        ):
            return self.demo_responses["salary"]
        else:
            return self.demo_responses["default"]


def create_demo_frontend():
    """Create a modified version of the frontend for demo purposes."""
    frontend_code = '''"""
Demo version of the AI Career Mentor Chatbot frontend.
This version uses mock responses to demonstrate functionality.
"""

import streamlit as st
import json
import uuid
from datetime import datetime
import time

# Mock client import
import sys
import os
sys.path.append('.')
from demo_frontend import MockChatbotClient

# Page configuration
st.set_page_config(
    page_title="AI Career Mentor (Demo)",
    page_icon="🤖",
    layout="wide"
)

# Demo notice
st.info("🎭 **Demo Mode**: This is a demonstration using simulated AI responses. The full version integrates with Azure OpenAI for real AI-powered career advice!")

# Initialize session state
if 'demo_client' not in st.session_state:
    st.session_state.demo_client = MockChatbotClient()

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

# Header
st.markdown("""
<div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 2rem;">
    <h1>🤖 AI Career Mentor</h1>
    <p>Your intelligent guide to AI engineering careers</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🎯 Try These Questions")
    
    sample_questions = [
        "How do I transition from web development to AI engineering?",
        "What skills are most important for AI engineering roles?", 
        "What's the typical salary for AI engineers?",
        "Should I get a PhD for AI positions?",
        "What portfolio projects should I build?",
        "How do I prepare for AI engineering interviews?"
    ]
    
    for i, question in enumerate(sample_questions):
        if st.button(f"💬 {question[:40]}...", key=f"q_{i}"):
            st.session_state.messages.append({
                "role": "user",
                "content": question,
                "timestamp": datetime.now().isoformat()
            })
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 🔄 Actions")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.conversation_id = str(uuid.uuid4())
        st.rerun()

# Main chat interface
st.markdown("### 💬 Chat with AI Career Mentor")

# Display messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.75rem 1rem; border-radius: 18px 18px 5px 18px; margin: 0.5rem 0; margin-left: 20%;">
            <strong>You:</strong> {message["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: #f1f3f4; padding: 0.75rem 1rem; border-radius: 18px 18px 18px 5px; margin: 0.5rem 0; margin-right: 20%; border-left: 4px solid #667eea;">
            <strong>🤖 AI Mentor:</strong><br>{message["content"]}
        </div>
        """, unsafe_allow_html=True)

# Input form
with st.form("chat_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Ask me anything about AI engineering careers...",
            placeholder="e.g., How do I get started in AI engineering?",
            label_visibility="collapsed"
        )
    
    with col2:
        submit = st.form_submit_button("Send 🚀", use_container_width=True)

# Process input
if submit and user_input.strip():
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().isoformat()
    })
    
    # Show loading and get response
    with st.spinner("🤖 AI Mentor is thinking..."):
        response = st.session_state.demo_client.send_message(
            message=user_input,
            conversation_id=st.session_state.conversation_id,
            user_id="demo_user"
        )
        
        # Add AI response
        st.session_state.messages.append({
            "role": "assistant",
            "content": response["message"],
            "timestamp": datetime.now().isoformat()
        })
    
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>🚀 Built with FastAPI, Azure OpenAI, and Streamlit | 
    <a href="https://github.com/scott-ai-maker/ai-powered-chatbot">View on GitHub</a></p>
</div>
""", unsafe_allow_html=True)
'''

    with open("demo_frontend_app.py", "w") as f:
        f.write(frontend_code)

    print("✅ Demo frontend created: demo_frontend_app.py")
    print("💡 Run with: streamlit run demo_frontend_app.py")


if __name__ == "__main__":
    print("🎭 AI Career Mentor Chatbot - Demo Mode")
    print("=" * 50)

    # Test the mock client
    client = MockChatbotClient()

    print("Testing mock responses...")
    test_messages = [
        "How do I transition to AI engineering?",
        "What skills should I learn?",
        "What's the salary range?",
    ]

    for msg in test_messages:
        print(f"\n👤 User: {msg}")
        response = client.send_message(msg, "demo_conv", "demo_user")
        print(f"🤖 AI: {response['message'][:100]}...")

    print(
        f"\n✅ Mock client working! Generated {len(client.conversation_history)} messages"
    )

    # Create demo frontend
    create_demo_frontend()
    print("\n🎉 Demo setup complete!")
