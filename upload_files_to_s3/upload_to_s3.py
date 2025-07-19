"""
AWS S3 File Upload Script

This script uploads a file to an S3 bucket using credentials from a .env file.
You can optionally specify a destination folder in the S3 bucket using the S3_BUCKET_FOLDER
environment variable in your .env file.

Environment Variables:
    AWS_ACCESS_KEY_ID: Your AWS access key
    AWS_SECRET_ACCESS_KEY: Your AWS secret key
    AWS_DEFAULT_REGION: AWS region (e.g., us-west-2)
    S3_BUCKET_NAME: Name of your S3 bucket
    S3_BUCKET_FOLDER: (Optional) Folder path in the bucket (e.g., 'uploads/2023')

Usage:
    1. Copy .env.example to .env and fill in your AWS credentials
    2. Optionally set S3_BUCKET_FOLDER in .env
    3. Run: python upload_to_s3.py <path_to_file>
"""

import os
import sys
import logging
import glob
import boto3
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_environment():
    """Load environment variables from .env file."""
    try:
        load_dotenv()
        required_vars = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_DEFAULT_REGION',
            'S3_BUCKET_NAME'
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            logger.info("Please check your .env file and ensure all required variables are set.")
            return False

        return True
    except Exception as e:
        logger.error(f"Error loading environment variables: {str(e)}")
        return False


def upload_large_file(file_path, bucket_name, object_name, s3_client, part_size=8 * 1024 * 1024):
    """Upload large file using S3's multipart upload

    Args:
        file_path: Path to the file to upload
        bucket_name: Name of the S3 bucket
        object_name: S3 object name
        s3_client: Initialized S3 client
        part_size: Part size in bytes (default: 8MB, minimum: 5MB)
    """
    file_size = os.path.getsize(file_path)
    part_size = max(part_size, 5 * 1024 * 1024)  # Ensure minimum part size of 5MB

    # Create multipart upload
    mpu = s3_client.create_multipart_upload(
        Bucket=bucket_name,
        Key=object_name
    )
    mpu_id = mpu['UploadId']

    try:
        parts = []
        uploaded_bytes = 0

        with open(file_path, 'rb') as f:
            i = 1
            while True:
                # Read part of the file
                data = f.read(part_size)
                if not data:
                    break

                # Upload part
                part = s3_client.upload_part(
                    Bucket=bucket_name,
                    Key=object_name,
                    PartNumber=i,
                    UploadId=mpu_id,
                    Body=data
                )

                parts.append({
                    'PartNumber': i,
                    'ETag': part['ETag']
                })

                uploaded_bytes += len(data)
                progress = (uploaded_bytes / file_size) * 100
                logger.info(f"Upload progress: {progress:.1f}% ({uploaded_bytes:,} / {file_size:,} bytes)")

                i += 1

        # Complete multipart upload
        s3_client.complete_multipart_upload(
            Bucket=bucket_name,
            Key=object_name,
            UploadId=mpu_id,
            MultipartUpload={'Parts': parts}
        )
        return True

    except Exception as e:
        logger.error(f"Error during multipart upload: {str(e)}")
        # Abort the upload if something went wrong
        s3_client.abort_multipart_upload(
            Bucket=bucket_name,
            Key=object_name,
            UploadId=mpu_id
        )
        return False


def upload_file_to_s3(file_path, bucket_name, object_name=None, folder=None):
    """Upload a file to an S3 bucket

    :param file_path: File to upload
    :param bucket_name: Name of the S3 bucket
    :param object_name: S3 object name. If not specified, file_name is used
    :param folder: Optional folder path in the bucket (without leading/trailing slashes)
    :return: True if file was uploaded, else False
    """
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_path)

    # Prepend folder to object_name if folder is specified
    if folder:
        # Remove any leading/trailing slashes from folder and add a single trailing slash
        folder = folder.strip('/')
        if folder:
            object_name = f"{folder}/{object_name}"

    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_DEFAULT_REGION'),
            config=boto3.session.Config(
                max_pool_connections=50,
                retries={
                    'max_attempts': 3,
                    'mode': 'standard'
                }
            )
        )

        file_size = os.path.getsize(file_path)
        logger.info(
            f"Starting upload: {file_path} ({file_size / 1024 / 1024:.2f} MB) to s3://{bucket_name}/{object_name}")

        # For large files, use multipart upload
        if file_size > 100 * 1024 * 1024:  # 100MB threshold for multipart
            logger.info("Using multipart upload for large file")
            return upload_large_file(file_path, bucket_name, object_name, s3_client)
        else:
            # For smaller files, use standard upload
            s3_client.upload_file(file_path, bucket_name, object_name)
            logger.info(f"Successfully uploaded {object_name}")
            return True

    except FileNotFoundError:
        logger.error(f"The file {file_path} was not found")
        return False
    except NoCredentialsError:
        logger.error("AWS credentials not found. Please check your .env file.")
        return False
    except ClientError as e:
        logger.error(f"AWS Client error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return False


def get_matching_files(file_pattern):
    """Get list of files matching the given pattern.

    Args:
        file_pattern (str): File path pattern (can include '*' wildcard)

    Returns:
        list: List of matching file paths
    """
    if file_pattern.endswith('*'):
        # Get the directory and base pattern
        dir_path = os.path.dirname(file_pattern)
        if not dir_path:
            dir_path = '.'
        base_pattern = os.path.basename(file_pattern)
        # Find all files matching the pattern
        matching_files = glob.glob(os.path.join(dir_path, base_pattern))
        # Filter out directories
        return [f for f in matching_files if os.path.isfile(f)]
    elif os.path.isfile(file_pattern):
        return [file_pattern]
    return []


def get_s3_folder():
    """Generate a folder path in [S3_BUCKET_FOLDER]/YYYY-MM-DD format.

    Returns:
        str: Folder path including both the base folder from env and date
    """
    date_folder = datetime.now().strftime("%Y-%m-%d")
    base_folder = os.getenv('S3_BUCKET_FOLDER', '').strip('/')

    if base_folder:
        return f"{base_folder}/{date_folder}"
    return date_folder


def ensure_s3_folder_exists(s3_client, bucket_name, folder):
    """Ensure the folder exists in S3 by creating an empty object with the folder prefix.

    Args:
        s3_client: Initialized S3 client
        bucket_name: Name of the S3 bucket
        folder: Folder path to ensure exists
    """
    try:
        # Add trailing slash to make it a folder
        if not folder.endswith('/'):
            folder = f"{folder}/"

        # Check if folder exists by listing objects with the prefix
        result = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=folder,
            MaxKeys=1
        )

        # If no contents and no common prefixes, create the folder
        if 'Contents' not in result and 'CommonPrefixes' not in result:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=folder,
                Body=b''
            )
            logger.info(f"Created S3 folder: {folder}")

    except Exception as e:
        logger.warning(f"Could not ensure folder exists: {str(e)}")


def main():
    # Check if file path is provided as command line argument
    if len(sys.argv) != 2:
        logger.error("Usage: python upload_to_s3.py <path_to_file_or_pattern>")
        logger.info("Note: Use '*' at the end of a path to upload multiple files (e.g., 'uploads/*' or '*.txt')")
        sys.exit(1)

    file_pattern = sys.argv[1]

    # Load environment variables
    if not load_environment():
        sys.exit(1)

    # Get bucket name from environment
    bucket_name = os.getenv('S3_BUCKET_NAME')

    # Get list of files to upload
    files_to_upload = get_matching_files(file_pattern)

    if not files_to_upload:
        logger.error(f"No files found matching pattern: {file_pattern}")
        sys.exit(1)

    # Initialize S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION'),
        config=boto3.session.Config(
            max_pool_connections=50,
            retries={
                'max_attempts': 3,
                'mode': 'standard'
            }
        )
    )

    # Create date-based folder
    date_folder = get_s3_folder()
    logger.info(f"Using S3 folder: {date_folder}")

    # Ensure the folder exists in S3
    ensure_s3_folder_exists(s3_client, bucket_name, date_folder)

    # Upload all matching files
    all_success = True
    for file_path in files_to_upload:
        try:
            logger.info(f"Processing: {file_path}")
            # Pass the date folder to the upload function
            success = upload_file_to_s3(
                file_path,
                bucket_name,
                folder=date_folder
            )
            if not success:
                all_success = False
                logger.error(f"Failed to upload: {file_path}")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            all_success = False

    if all_success:
        logger.info("All files uploaded successfully!")
    else:
        logger.error("Some files failed to upload")

    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
