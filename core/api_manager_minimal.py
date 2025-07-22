"""
Minimal API manager for basic functionality
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class APIKeyManager:
    def __init__(self):
        self.api_key = None
    
    def get_api_key(self) -> Optional[str]:
        """Get OpenAI API key"""
        if self.api_key:
            return self.api_key
        
        # Try to get from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            return api_key
        
        logger.warning("No OpenAI API key found")
        return None
    
    def set_api_key(self, api_key: str) -> None:
        """Set OpenAI API key"""
        self.api_key = api_key
        logger.info("API key set successfully")
    
    def has_api_key(self) -> bool:
        """Check if API key is available"""
        return self.get_api_key() is not None
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key format"""
        if not api_key:
            return False
        
        # Basic validation - should start with 'sk-'
        if api_key.startswith('sk-') and len(api_key) > 20:
            return True
        
        return False