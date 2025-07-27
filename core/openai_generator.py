"""
OpenAI Image Generator using DALL-E API
"""
import os
import logging
import base64
import requests
from typing import Optional, Dict, Any
from pathlib import Path
import time

logger = logging.getLogger(__name__)

class OpenAIImageGenerator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        logger.info("OpenAI Image Generator initialized")
    
    def create_scene_prompt(self, script_segment: str, character_description: str, 
                           style: str, scene_number: int) -> str:
        """Create an optimized prompt for image generation"""
        # Clean and enhance the script segment
        clean_script = script_segment.strip()
        if len(clean_script) > 500:
            clean_script = clean_script[:500] + "..."
        
        # Style mapping for better DALL-E prompts
        style_mapping = {
            "Photorealistic": "photorealistic, high quality, detailed, professional photography",
            "Cinematic": "cinematic, movie still, dramatic lighting, film photography",
            "Anime": "anime style, Japanese animation, vibrant colors, stylized",
            "3D": "3D rendered, CGI, computer generated, modern 3D graphics",
            "Artistic": "artistic, painterly, creative, expressive",
            "Minimalist": "minimalist, simple, clean, modern design",
            "Vintage": "vintage, retro, classic, nostalgic",
            "Futuristic": "futuristic, sci-fi, modern technology, sleek"
        }
        
        style_prompt = style_mapping.get(style, "high quality, detailed")
        
        # Build the prompt
        prompt = f"Scene {scene_number}: {character_description}, {style_prompt}. {clean_script}. Professional composition, high resolution, 4K quality."
        
        logger.info(f"Created prompt for scene {scene_number}: {prompt[:100]}...")
        return prompt
    
    def generate_and_save_image(self, prompt: str, output_dir: str, 
                               filename: str, style: str) -> str:
        """Generate image using DALL-E and save to file"""
        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate image using DALL-E 3
            image_data = self._generate_image_dalle3(prompt)
            
            if not image_data:
                # Fallback to DALL-E 2
                logger.warning("DALL-E 3 failed, trying DALL-E 2...")
                image_data = self._generate_image_dalle2(prompt)
            
            if not image_data:
                raise Exception("Failed to generate image with both DALL-E 3 and DALL-E 2")
            
            # Save the image
            output_path = os.path.join(output_dir, f"{filename}.png")
            self._save_image_from_data(image_data, output_path)
            
            logger.info(f"Successfully generated and saved image: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            # Create a placeholder image as fallback
            return self._create_placeholder_image(output_dir, filename, str(e))
    
    def _generate_image_dalle3(self, prompt: str) -> Optional[bytes]:
        """Generate image using DALL-E 3"""
        try:
            url = f"{self.base_url}/images/generations"
            data = {
                "model": "dall-e-3",
                "prompt": prompt,
                "size": "1024x1024",
                "quality": "standard",
                "n": 1
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                image_url = result['data'][0]['url']
                
                # Download the image
                img_response = requests.get(image_url, timeout=30)
                if img_response.status_code == 200:
                    return img_response.content
                else:
                    logger.error(f"Failed to download image: {img_response.status_code}")
                    return None
            else:
                logger.error(f"DALL-E 3 API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"DALL-E 3 generation error: {str(e)}")
            return None
    
    def _generate_image_dalle2(self, prompt: str) -> Optional[bytes]:
        """Generate image using DALL-E 2 (fallback)"""
        try:
            url = f"{self.base_url}/images/generations"
            data = {
                "model": "dall-e-2",
                "prompt": prompt,
                "size": "1024x1024",
                "n": 1
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                image_url = result['data'][0]['url']
                
                # Download the image
                img_response = requests.get(image_url, timeout=30)
                if img_response.status_code == 200:
                    return img_response.content
                else:
                    logger.error(f"Failed to download image: {img_response.status_code}")
                    return None
            else:
                logger.error(f"DALL-E 2 API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"DALL-E 2 generation error: {str(e)}")
            return None
    
    def _save_image_from_data(self, image_data: bytes, output_path: str):
        """Save image data to file"""
        try:
            with open(output_path, 'wb') as f:
                f.write(image_data)
            logger.info(f"Image saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            raise
    
    def _create_placeholder_image(self, output_dir: str, filename: str, error_msg: str) -> str:
        """Create a placeholder image when generation fails"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple placeholder image
            img = Image.new('RGB', (1024, 1024), color='#f0f0f0')
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font, fallback to basic if not available
            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except:
                font = ImageFont.load_default()
            
            # Add text to the placeholder
            text = f"Image Generation Failed\n{error_msg[:50]}..."
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (1024 - text_width) // 2
            y = (1024 - text_height) // 2
            
            draw.text((x, y), text, fill='#666666', font=font)
            
            output_path = os.path.join(output_dir, f"{filename}.png")
            img.save(output_path)
            
            logger.warning(f"Created placeholder image: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating placeholder image: {str(e)}")
            # Create a simple text file as last resort
            output_path = os.path.join(output_dir, f"{filename}.txt")
            with open(output_path, 'w') as f:
                f.write(f"Image generation failed: {error_msg}")
            return output_path
    
    def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        if not self.api_key:
            logger.error("No API key provided")
            return False
        
        try:
            # Test with a simple API call
            url = f"{self.base_url}/models"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                logger.info("OpenAI API connection successful")
                return True
            else:
                logger.error(f"API test failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Connection test error: {str(e)}")
            return False
    
    def get_available_models(self) -> list:
        """Get list of available OpenAI models"""
        try:
            url = f"{self.base_url}/models"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                models = response.json()
                return [model['id'] for model in models['data'] if 'dall-e' in model['id']]
            else:
                logger.error(f"Failed to get models: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting models: {str(e)}")
            return []
    
    def estimate_cost(self, image_count: int, model: str = "dall-e-3") -> Dict[str, float]:
        """Estimate the cost of generating images"""
        # OpenAI pricing (as of 2024, may need updates)
        pricing = {
            "dall-e-3": {
                "1024x1024": 0.040,  # per image
                "1792x1024": 0.080,  # per image
                "1024x1792": 0.080   # per image
            },
            "dall-e-2": {
                "1024x1024": 0.020,  # per image
                "512x512": 0.018,     # per image
                "256x256": 0.016      # per image
            }
        }
        
        model_pricing = pricing.get(model, pricing["dall-e-3"])
        cost_per_image = model_pricing.get("1024x1024", 0.040)
        total_cost = image_count * cost_per_image
        
        return {
            "cost_per_image": cost_per_image,
            "total_cost": total_cost,
            "currency": "USD"
        } 