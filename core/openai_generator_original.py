import openai
import os
import logging
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class OpenAIGenerator:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        self.model = "gpt-3.5-turbo"
        
        if not os.getenv('OPENAI_API_KEY'):
            logger.warning("OpenAI API key not found in environment variables")
    
    def generate_content(self, transcript: str, video_info: dict = None) -> Dict[str, str]:
        """Generate title and description from video transcript"""
        try:
            # Create prompt
            prompt = self._create_content_prompt(transcript, video_info)
            
            # Generate content
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a YouTube content creator assistant. Generate engaging titles and descriptions for videos."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            # Parse response
            content = response.choices[0].message.content
            return self._parse_content_response(content)
            
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            # Return fallback content
            return {
                "title": "Untitled Video",
                "description": "Generated video content",
                "tags": ["video", "content"]
            }
    
    def _create_content_prompt(self, transcript: str, video_info: dict = None) -> str:
        """Create prompt for content generation"""
        prompt = f"""
        Based on the following video transcript, generate:
        1. An engaging YouTube title (under 60 characters)
        2. A detailed description (200-300 words)
        3. 5-10 relevant tags
        
        Transcript:
        {transcript[:2000]}  # Limit transcript length
        
        """
        
        if video_info:
            prompt += f"\nVideo info: {json.dumps(video_info, indent=2)}"
        
        prompt += """
        Please format your response as:
        TITLE: [your title here]
        DESCRIPTION: [your description here]
        TAGS: [tag1, tag2, tag3, ...]
        """
        
        return prompt
    
    def _parse_content_response(self, content: str) -> Dict[str, str]:
        """Parse AI response into structured content"""
        try:
            lines = content.strip().split('\n')
            result = {
                "title": "Untitled Video",
                "description": "Generated video content",
                "tags": ["video", "content"]
            }
            
            current_section = None
            description_lines = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('TITLE:'):
                    result["title"] = line.replace('TITLE:', '').strip()
                    current_section = "title"
                elif line.startswith('DESCRIPTION:'):
                    description_lines = [line.replace('DESCRIPTION:', '').strip()]
                    current_section = "description"
                elif line.startswith('TAGS:'):
                    tags_str = line.replace('TAGS:', '').strip()
                    # Parse tags from various formats
                    if '[' in tags_str and ']' in tags_str:
                        tags_str = tags_str.strip('[]')
                    tags = [tag.strip().strip('"\'') for tag in tags_str.split(',')]
                    result["tags"] = [tag for tag in tags if tag]
                    current_section = "tags"
                elif current_section == "description" and line:
                    description_lines.append(line)
            
            if description_lines:
                result["description"] = '\n'.join(description_lines)
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return {
                "title": "Untitled Video",
                "description": "Generated video content",
                "tags": ["video", "content"]
            }
    
    def generate_hashtags(self, title: str, description: str) -> List[str]:
        """Generate hashtags based on title and description"""
        try:
            prompt = f"""
            Generate 5-10 relevant hashtags for this YouTube video:
            
            Title: {title}
            Description: {description[:500]}
            
            Return only the hashtags separated by spaces, without the # symbol.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a social media hashtag generator."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.5
            )
            
            hashtags = response.choices[0].message.content.strip().split()
            return [tag.strip('#') for tag in hashtags if tag]
            
        except Exception as e:
            logger.error(f"Error generating hashtags: {str(e)}")
            return ["video", "content", "youtube"]
    
    def improve_description(self, current_description: str, transcript: str) -> str:
        """Improve existing description using transcript"""
        try:
            prompt = f"""
            Improve this YouTube video description using the provided transcript:
            
            Current description:
            {current_description}
            
            Transcript:
            {transcript[:1500]}
            
            Make it more engaging and informative while keeping it under 300 words.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a YouTube content optimization expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.6
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error improving description: {str(e)}")
            return current_description
    
    def generate_thumbnail_ideas(self, title: str, transcript: str) -> List[str]:
        """Generate thumbnail ideas based on content"""
        try:
            prompt = f"""
            Generate 3 thumbnail ideas for this YouTube video:
            
            Title: {title}
            Content summary: {transcript[:800]}
            
            Describe each thumbnail idea in 1-2 sentences.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a YouTube thumbnail design expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.8
            )
            
            ideas = response.choices[0].message.content.strip().split('\n')
            return [idea.strip() for idea in ideas if idea.strip()]
            
        except Exception as e:
            logger.error(f"Error generating thumbnail ideas: {str(e)}")
            return ["Eye-catching thumbnail with main subject", "Bold text overlay", "Bright colors"]