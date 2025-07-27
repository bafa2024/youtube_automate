import asyncio
import aiohttp
import os
import time
import json

# Test the Generate Image button functionality
async def test_generate_button():
    base_url = "http://localhost:8000"
    
    # Create test files
    test_script = "This is a test script about a beautiful sunset over mountains. The scene shows a peaceful landscape with golden light."
    test_audio_data = b"fake audio data for testing"
    
    async with aiohttp.ClientSession() as session:
        print("1. Testing API key check...")
        async with session.get(f"{base_url}/api/check-api-key") as resp:
            print(f"   API Key Status: {resp.status}")
            if resp.status != 200:
                print("   No API key set. Please set one through the UI first.")
                return
        
        print("\n2. Uploading test script...")
        # Create multipart form data for script
        data = aiohttp.FormData()
        data.add_field('file', test_script.encode(), filename='test_script.txt', content_type='text/plain')
        
        async with session.post(f"{base_url}/api/upload/script", data=data) as resp:
            if resp.status == 200:
                script_data = await resp.json()
                print(f"   Script uploaded: {script_data}")
            else:
                print(f"   Failed to upload script: {await resp.text()}")
                return
        
        print("\n3. Uploading test audio...")
        # Create multipart form data for audio
        data = aiohttp.FormData()
        data.add_field('file', test_audio_data, filename='test_audio.mp3', content_type='audio/mpeg')
        
        async with session.post(f"{base_url}/api/upload/audio", data=data) as resp:
            if resp.status == 200:
                audio_data = await resp.json()
                print(f"   Audio uploaded: {audio_data}")
            else:
                print(f"   Failed to upload audio: {await resp.text()}")
                return
        
        print("\n4. Testing image generation...")
        # Prepare generation request
        gen_data = aiohttp.FormData()
        gen_data.add_field('script_file_id', script_data['file_id'])
        gen_data.add_field('voice_file_id', audio_data['file_id'])
        gen_data.add_field('script_text', test_script)
        gen_data.add_field('image_count', '3')
        gen_data.add_field('style', 'Photorealistic')
        gen_data.add_field('character_description', 'Beautiful natural landscape')
        gen_data.add_field('voice_duration', '60')
        gen_data.add_field('export_options', json.dumps({
            'images': True,
            'clips': False,
            'full_video': False
        }))
        
        async with session.post(f"{base_url}/api/generate/ai-images", data=gen_data) as resp:
            if resp.status == 200:
                job_data = await resp.json()
                print(f"   Generation started: {job_data}")
                job_id = job_data['job_id']
            else:
                error_text = await resp.text()
                print(f"   Failed to start generation: {error_text}")
                return
        
        print("\n5. Monitoring job progress...")
        # Poll for job status
        for i in range(30):  # Check for up to 60 seconds
            await asyncio.sleep(2)
            async with session.get(f"{base_url}/api/jobs/{job_id}") as resp:
                if resp.status == 200:
                    job_status = await resp.json()
                    print(f"   Progress: {job_status['progress']}% - {job_status['status']} - {job_status['message']}")
                    
                    if job_status['status'] == 'completed':
                        print(f"\n   ✓ Job completed successfully!")
                        if job_status.get('result_url'):
                            print(f"   Result URL: {job_status['result_url']}")
                        break
                    elif job_status['status'] == 'failed':
                        print(f"\n   ✗ Job failed: {job_status['message']}")
                        break
                else:
                    print(f"   Failed to get job status: {resp.status}")

if __name__ == "__main__":
    print("Testing Generate Image Button...\n")
    asyncio.run(test_generate_button())