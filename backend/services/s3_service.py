import boto3
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import uuid
from io import BytesIO
from datetime import datetime
import re

load_dotenv()

class S3Uploader:
    def __init__(self):
        # Validate environment variables
        required_vars = {
            "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
            "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
            "AWS_REGION": os.getenv("AWS_REGION"),
            "S3_BUCKET_NAME": os.getenv("S3_BUCKET_NAME")
        }
        
        missing_vars = [key for key, value in required_vars.items() if not value]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Initialize S3 client
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=required_vars["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=required_vars["AWS_SECRET_ACCESS_KEY"],
            region_name=required_vars["AWS_REGION"]
        )
        self.bucket = required_vars["S3_BUCKET_NAME"]
        self.region = required_vars["AWS_REGION"]


    # Generating Individual Folder For Every session
    

    def generate_folder_name(job_description: str) -> str:
        """Generate folder name: JobDescription-YYYY-MM-DD-HH-MM-SS"""
        clean_desc = re.sub(r'[^\w\s-]', '', job_description)[:30]  # Keep only alphanumeric, spaces, hyphens
        clean_desc = re.sub(r'\s+', '-', clean_desc.strip())  # Replace spaces with hyphens
        
        # Add timestamp
        now = datetime.now()
        timestamp = now.strftime('%d-%m-%y-Time-%H-%M-%S')
        
        return f"{clean_desc}-Resume-List-{timestamp}"


    def upload_file(self, file_obj, filename: str) -> str:
        """Upload file to S3 and return the URL"""
        try:
            file_obj.seek(0)
            
            self.s3.upload_fileobj(
                file_obj, 
                self.bucket, 
                filename,
                ExtraArgs={
                    'ContentType': 'application/pdf',
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{filename}"
            
        except ClientError as e:
            raise RuntimeError(f"S3 upload failed: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Upload failed: {str(e)}")


    def test_s3_connection(self):
        """Test S3 connection and bucket access"""
        try:
            # Test bucket access
            self.s3.head_bucket(Bucket=self.bucket)
            
            # Test upload
            test_content = BytesIO(b"test")
            test_filename = f"test_{uuid.uuid4()}.txt"
            
            self.upload_file(test_content, test_filename)
            
            # Cleanup
            self.s3.delete_object(Bucket=self.bucket, Key=test_filename)
            
            return True
        except:
            return False
        
    


