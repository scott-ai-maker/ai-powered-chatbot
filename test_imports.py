#!/usr/bin/env python3
"""
Quick import test to verify all dependencies are working.
This file should have no red squiggles if the Python environment is properly configured.
"""

# Core web framework imports
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.responses import JSONResponse

# Data validation
from pydantic import BaseModel, Field

# AI/ML libraries
from openai import AsyncAzureOpenAI
import httpx

# Async and utilities
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os

# Testing
import pytest

# Logging
import structlog
import logging

# Streamlit for frontend
import streamlit as st

print("✅ All imports successful! No red squiggles should appear above.")

if __name__ == "__main__":
    print("Running import test...")
    print("All dependencies are properly installed and accessible.")