"""
Test image generation synchronously without Celery
"""
import os
import asyncio
from pathlib import Path
from core.openai_generator import OpenAIImageGenerator
from core.api_manager import APIKeyManager

async def test_sync_generation():
    """Test image generation directly without Celery"""
    
    # Load API key
    api_key_file = Path("api_key.txt")
    if api_key_file.exists():
        api_key = api_key_file.read_text().strip()
        os.environ['OPENAI_API_KEY'] = api_key
        print(f"[OK] API key loaded from file")
    else:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("[ERROR] No API key found! Set it first.")
            return
    
    print(f"[OK] API key found: sk-...{api_key[-4:]}")
    
    # Initialize generator
    generator = OpenAIImageGenerator(api_key)
    
    # Test connection
    print("\nTesting OpenAI connection...")
    if generator.test_connection():
        print("[OK] OpenAI connection successful")
    else:
        print("[ERROR] OpenAI connection failed")
        return
    
    # Generate a test image
    print("\nGenerating test image...")
    try:
        prompt = "A beautiful sunset over mountains, photorealistic, high quality"
        output_dir = "test_output"
        
        image_path = generator.generate_and_save_image(
            prompt=prompt,
            output_dir=output_dir,
            filename="test_image",
            style="Photorealistic"
        )
        
        print(f"[OK] Image generated successfully: {image_path}")
        print(f"\nYou can view the image at: {os.path.abspath(image_path)}")
        
    except Exception as e:
        print(f"[ERROR] Image generation failed: {e}")

if __name__ == "__main__":
    print("=== Testing Image Generation Without Celery ===\n")
    asyncio.run(test_sync_generation())