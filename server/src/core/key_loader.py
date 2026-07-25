"""Key loader for fetching PEM keys from S3 with caching."""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# In-memory cache for PEM keys
# Lives in Lambda execution environment's global scope; warm invocations skip S3 call
_key_cache: dict[str, str] = {}


def get_pem_key(key_name: str) -> Optional[str]:
    """
    Fetch a PEM key from S3 bucket and cache it in memory.

    Subsequent invocations on warm Lambda containers avoid S3 GetObject calls.
    Cold start incurs single GetObject cost (negligible).

    Args:
        key_name: Name of the key file (without .pem extension).
                 Looks for keys/{key_name}.pem in the bucket.

    Returns:
        PEM key content as string, or None if bucket/key not configured.

    Raises:
        botocore.exceptions.ClientError if S3 access fails (e.g., permission denied).
    """
    if key_name in _key_cache:
        logger.debug("Key '%s' loaded from memory cache", key_name)
        return _key_cache[key_name]

    # Terraform/Lambda uses AWS__KEYS_BUCKET_NAME; KEYS_BUCKET is kept as fallback.
    bucket_name = os.environ.get("AWS__KEYS_BUCKET_NAME") or os.environ.get("KEYS_BUCKET")
    if not bucket_name:
        logger.warning("AWS__KEYS_BUCKET_NAME/KEYS_BUCKET environment variable not set")
        return None

    try:
        import boto3

        region_name = os.environ.get("AWS__REGION") or os.environ.get("AWS_REGION")
        s3_client = boto3.client("s3", region_name=region_name)
        obj = s3_client.get_object(Bucket=bucket_name, Key=f"keys/{key_name}.pem")

        key_content = obj["Body"].read().decode("utf-8")
        _key_cache[key_name] = key_content
        logger.debug("Key '%s' fetched from S3 and cached", key_name)

        return key_content
    except Exception:
        logger.exception("Failed to fetch key '%s' from S3", key_name)
        raise
