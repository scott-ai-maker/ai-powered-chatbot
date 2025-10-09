"""
Simple in-memory cache for chatbot responses.
This provides immediate performance improvements without external dependencies.
"""

import hashlib
import time
from typing import Dict, Optional, Tuple
from threading import Lock

class SimpleResponseCache:
    """
    Lightweight in-memory cache for chatbot responses.
    
    This cache helps avoid re-processing similar questions and provides
    instant responses for frequently asked questions.
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[str, float]] = {}
        self._lock = Lock()
    
    def _generate_key(self, message: str, use_rag: bool = False) -> str:
        """Generate cache key from message content."""
        content = f"{message.lower().strip()}_rag_{use_rag}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, message: str, use_rag: bool = False) -> Optional[str]:
        """Get cached response if available and not expired."""
        key = self._generate_key(message, use_rag)
        
        with self._lock:
            if key in self._cache:
                response, timestamp = self._cache[key]
                
                # Check if expired
                if time.time() - timestamp > self.ttl_seconds:
                    del self._cache[key]
                    return None
                
                return response
            
            return None
    
    def set(self, message: str, response: str, use_rag: bool = False):
        """Cache response with current timestamp."""
        key = self._generate_key(message, use_rag)
        
        with self._lock:
            # Remove oldest entry if cache is full
            if len(self._cache) >= self.max_size:
                oldest_key = min(self._cache.keys(), 
                               key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]
            
            self._cache[key] = (response, time.time())
    
    def clear(self):
        """Clear all cached responses."""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


# Global cache instance
response_cache = SimpleResponseCache(max_size=500, ttl_seconds=1800)  # 30 minutes TTL