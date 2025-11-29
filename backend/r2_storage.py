import boto3
import logging
from typing import Optional, BinaryIO
from datetime import timedelta
from botocore.exceptions import ClientError
from config import R2_ENDPOINT, R2_BUCKET_NAME, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_PUBLIC_URL

logger = logging.getLogger(__name__)

class R2StorageManager:
    """Cloudflare R2 storage manager using S3-compatible API."""
    
    def __init__(self):
        self.endpoint = R2_ENDPOINT
        self.bucket_name = R2_BUCKET_NAME
        self.public_url = R2_PUBLIC_URL
        self.client = None
        self.enabled = False
        
        # Only initialize if all required config is present
        if all([R2_ENDPOINT, R2_BUCKET_NAME, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
            try:
                # Initialize S3 client for R2
                self.client = boto3.client(
                    's3',
                    endpoint_url=self.endpoint,
                    aws_access_key_id=R2_ACCESS_KEY_ID,
                    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
                    region_name='auto'
                )
                self.enabled = True
                logger.info("R2 storage initialized successfully")
            except Exception as e:
                logger.warning(f"R2 storage initialization failed: {e}")
                self.enabled = False
        else:
            logger.info("R2 storage disabled - missing configuration")
    
    def upload_file(self, file_content: bytes, filename: str, content_hash: str) -> Optional[str]:
        """Upload file to R2 and return public URL."""
        if not self.enabled or not self.client:
            logger.debug("R2 storage not available, skipping upload")
            return None
            
        try:
            # Use hash-based path for deduplication
            object_key = f"{content_hash}/{filename}"
            
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_content,
                ContentType=self._get_content_type(filename)
            )
            
            # Return public URL
            public_url = f"{self.public_url}/{object_key}"
            logger.info(f"Uploaded {filename} to R2: {public_url}")
            return public_url
            
        except ClientError as e:
            logger.error(f"Failed to upload {filename} to R2: {e}")
            return None
    
    def download_file(self, object_key: str) -> Optional[bytes]:
        """Download file from R2."""
        if not self.enabled or not self.client:
            logger.debug("R2 storage not available, cannot download")
            return None
            
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return response['Body'].read()
            
        except ClientError as e:
            logger.error(f"Failed to download {object_key} from R2: {e}")
            return None
    
    def delete_file(self, object_key: str) -> bool:
        """Delete file from R2."""
        if not self.enabled or not self.client:
            logger.debug("R2 storage not available, cannot delete")
            return False
            
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            logger.info(f"Deleted {object_key} from R2")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete {object_key} from R2: {e}")
            return False
    
    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> Optional[str]:
        """Generate presigned URL for temporary access."""
        if not self.enabled or not self.client:
            logger.debug("R2 storage not available, cannot generate presigned URL")
            return None
            
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=expiration
            )
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {object_key}: {e}")
            return None
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension."""
        ext = filename.lower().split('.')[-1]
        content_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',
            'md': 'text/markdown',
            'csv': 'text/csv',
            'json': 'application/json',
            'py': 'text/x-python',
            'js': 'text/javascript',
            'html': 'text/html',
            'xml': 'application/xml'
        }
        return content_types.get(ext, 'application/octet-stream')

# Global instance
r2_storage = R2StorageManager()
