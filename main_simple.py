#!/usr/bin/env python3
"""
Main Simple - Redirect to main app
This file exists to satisfy Render's cached configuration
"""
from main import app

# Re-export the app from main.py
__all__ = ['app'] 