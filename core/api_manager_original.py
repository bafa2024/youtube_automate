import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import logging

logger = logging.getLogger(__name__)

class APIManager:
    def __init__(self):
        self.youtube_service = None
        self.scopes = ['https://www.googleapis.com/auth/youtube.upload']
        self.credentials_file = 'youtube_credentials.json'
        self.token_file = 'youtube_token.pickle'
        
        # Initialize YouTube API
        self._setup_youtube_api()
    
    def _setup_youtube_api(self):
        """Setup YouTube API authentication"""
        try:
            creds = None
            
            # Load existing token
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if os.path.exists(self.credentials_file):
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_file, self.scopes)
                        creds = flow.run_local_server(port=0)
                    else:
                        logger.warning("YouTube credentials file not found")
                        return
                
                # Save credentials
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
            
            # Build YouTube service
            self.youtube_service = build('youtube', 'v3', credentials=creds)
            logger.info("YouTube API initialized successfully")
            
        except Exception as e:
            logger.error(f"Error setting up YouTube API: {str(e)}")
    
    def upload_to_youtube(self, video_path: str, title: str, description: str = "", 
                         tags: list = None, category_id: str = "22") -> str:
        """Upload video to YouTube"""
        if not self.youtube_service:
            raise Exception("YouTube API not initialized")
        
        try:
            tags = tags or []
            
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': 'private',  # Change to 'public' when ready
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Create media upload object
            media = MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True,
                mimetype='video/*'
            )
            
            # Execute upload
            insert_request = self.youtube_service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = self._resumable_upload(insert_request)
            
            if response:
                video_id = response['id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"Video uploaded successfully: {video_url}")
                return video_url
            else:
                raise Exception("Upload failed")
                
        except HttpError as e:
            logger.error(f"HTTP error during upload: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error uploading to YouTube: {str(e)}")
            raise
    
    def _resumable_upload(self, insert_request):
        """Handle resumable upload with progress tracking"""
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                status, response = insert_request.next_chunk()
                if status:
                    logger.info(f"Upload progress: {int(status.progress() * 100)}%")
                    
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    error = f"HTTP error {e.resp.status}: {e.content}"
                    logger.warning(f"Retryable error: {error}")
                else:
                    raise
                    
            except Exception as e:
                error = f"Unexpected error: {str(e)}"
                logger.error(error)
                raise
            
            if error is not None:
                retry += 1
                if retry > 3:
                    raise Exception(f"Maximum retries exceeded: {error}")
                
                # Wait before retrying
                import time
                time.sleep(2 ** retry)
                error = None
        
        return response
    
    def get_video_info(self, video_id: str) -> dict:
        """Get video information from YouTube"""
        if not self.youtube_service:
            raise Exception("YouTube API not initialized")
        
        try:
            request = self.youtube_service.videos().list(
                part='snippet,statistics,status',
                id=video_id
            )
            response = request.execute()
            
            if response['items']:
                return response['items'][0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            raise
    
    def update_video_metadata(self, video_id: str, title: str = None, 
                            description: str = None, tags: list = None) -> bool:
        """Update video metadata on YouTube"""
        if not self.youtube_service:
            raise Exception("YouTube API not initialized")
        
        try:
            # Get current video info
            current_info = self.get_video_info(video_id)
            if not current_info:
                return False
            
            # Update snippet
            snippet = current_info['snippet']
            if title:
                snippet['title'] = title
            if description:
                snippet['description'] = description
            if tags:
                snippet['tags'] = tags
            
            # Update video
            request = self.youtube_service.videos().update(
                part='snippet',
                body={
                    'id': video_id,
                    'snippet': snippet
                }
            )
            
            response = request.execute()
            return response is not None
            
        except Exception as e:
            logger.error(f"Error updating video metadata: {str(e)}")
            raise
    
    def delete_video(self, video_id: str) -> bool:
        """Delete video from YouTube"""
        if not self.youtube_service:
            raise Exception("YouTube API not initialized")
        
        try:
            request = self.youtube_service.videos().delete(id=video_id)
            request.execute()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting video: {str(e)}")
            raise