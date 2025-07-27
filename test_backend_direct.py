import asyncio
import aiohttp
import json

async def test_backend():
    """Test the backend directly to see what's failing"""
    base_url = "http://localhost:8080"
    
    async with aiohttp.ClientSession() as session:
        # 1. Check if server is running
        try:
            async with session.get(f"{base_url}/") as resp:
                print(f"Server status: {resp.status}")
        except Exception as e:
            print(f"Server not reachable: {e}")
            return
        
        # 2. Check API key
        print("\n1. Checking API key...")
        async with session.get(f"{base_url}/api/check-api-key") as resp:
            print(f"API key check: {resp.status}")
            if resp.status != 200:
                print("API key not set!")
                return
        
        # 3. Upload test files
        print("\n2. Uploading test script...")
        script_text = "A beautiful sunset over mountains"
        data = aiohttp.FormData()
        data.add_field('file', script_text.encode(), filename='test.txt', content_type='text/plain')
        
        async with session.post(f"{base_url}/api/upload/script", data=data) as resp:
            if resp.status == 200:
                script_data = await resp.json()
                print(f"Script uploaded: {script_data}")
            else:
                print(f"Script upload failed: {await resp.text()}")
                return
        
        print("\n3. Uploading test audio...")
        data = aiohttp.FormData()
        data.add_field('file', b'fake audio', filename='test.mp3', content_type='audio/mpeg')
        
        async with session.post(f"{base_url}/api/upload/audio", data=data) as resp:
            if resp.status == 200:
                audio_data = await resp.json()
                print(f"Audio uploaded: {audio_data}")
            else:
                print(f"Audio upload failed: {await resp.text()}")
                return
        
        # 4. Try to generate images
        print("\n4. Testing image generation...")
        gen_data = aiohttp.FormData()
        gen_data.add_field('script_file_id', script_data['file_id'])
        gen_data.add_field('voice_file_id', audio_data['file_id'])
        gen_data.add_field('script_text', script_text)
        gen_data.add_field('image_count', '1')
        gen_data.add_field('style', 'Photorealistic')
        gen_data.add_field('character_description', 'Natural landscape')
        gen_data.add_field('voice_duration', '60')
        gen_data.add_field('export_options', json.dumps({
            'images': True,
            'clips': False,
            'full_video': False
        }))
        
        async with session.post(f"{base_url}/api/generate/ai-images", data=gen_data) as resp:
            print(f"Generation response status: {resp.status}")
            response_text = await resp.text()
            print(f"Response: {response_text}")
            
            if resp.status == 200:
                try:
                    job_data = json.loads(response_text)
                    print(f"Success! Job ID: {job_data.get('job_id')}")
                except:
                    print("Failed to parse response as JSON")
            else:
                print(f"Generation failed with status {resp.status}")

if __name__ == "__main__":
    print("Testing backend image generation...\n")
    asyncio.run(test_backend())