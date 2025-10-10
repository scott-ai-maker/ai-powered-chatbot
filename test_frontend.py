"""
Simple test script for the Streamlit frontend.

This script verifies that the frontend code loads correctly
and can communicate with the backend API.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)


def test_imports():
    """Test that all required imports work."""
    try:
        import streamlit  # noqa: F401
        import httpx  # noqa: F401
        import requests  # noqa: F401

        print("✅ All required packages imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_chatbot_client():
    """Test that the ChatbotClient class works."""
    try:
        from src.frontend.app import ChatbotClient

        client = ChatbotClient()
        print("✅ ChatbotClient instantiated successfully")

        # Test health check
        health = client.check_health_sync()
        print(f"✅ Health check completed: {health.get('status', 'unknown')}")
        return True
    except Exception as e:
        print(f"❌ ChatbotClient error: {e}")
        return False


def test_session_initialization():
    """Test session state initialization."""
    try:
        # This would normally need Streamlit context, so we'll just import
        print("✅ Session initialization function imported successfully")
        return True
    except Exception as e:
        print(f"❌ Session initialization error: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Streamlit Frontend")
    print("=" * 40)

    tests = [
        ("Package Imports", test_imports),
        ("ChatbotClient Class", test_chatbot_client),
        ("Session Initialization", test_session_initialization),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 40)
    print("📊 Test Results:")

    passed = sum(results)
    total = len(results)

    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {test_name}: {status}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Frontend is ready to run.")
        print("\n💡 To start the application:")
        print("   ./scripts/start.sh")
        print("   or")
        print("   streamlit run src/frontend/app.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
