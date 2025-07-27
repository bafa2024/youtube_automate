#!/usr/bin/env python3
"""
Simple test script for image generation
"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append('.')

from core.openai_generator import OpenAIImageGenerator
from core.api_manager import APIKeyManager

def test_image_generation():
    """Test image generation directly"""
    print("Testing image generation...")
    
    # Check API key
    api_key_file = Path("api_key.txt")
    if api_key_file.exists():
        api_key = api_key_file.read_text().strip()
        print(f"API key found: {api_key[:10]}...")
    else:
        print("No API key file found!")
        return False
    
    # Initialize generator
    try:
        generator = OpenAIImageGenerator(api_key)
        print("Generator initialized successfully")
    except Exception as e:
        print(f"Failed to initialize generator: {e}")
        return False
    
    # Test connection
    print("Testing OpenAI connection...")
    if generator.test_connection():
        print("✅ OpenAI connection successful")
    else:
        print("❌ OpenAI connection failed")
        return False
    
    # Generate test image
    print("Generating test image...")
    try:
        output_dir = "test_output"
        Path(output_dir).mkdir(exist_ok=True)
        
        image_path = generator.generate_and_save_image(
            prompt="A beautiful sunset over mountains, photorealistic style",
            output_dir=output_dir,
            filename="test_image",
            style="Photorealistic"
        )
        
        print(f"✅ Image generated successfully: {image_path}")
        return True
        
    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        return False

if __name__ == "__main__":
    success = test_image_generation()
    if success:
        print("\n🎉 Image generation test passed!")
    else:
        print("\n💥 Image generation test failed!")
        sys.exit(1) 