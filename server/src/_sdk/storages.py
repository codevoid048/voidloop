import base64
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlencode
from botocore.signers import CloudFrontSigner
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from storages.backends.s3boto3 import S3Boto3Storage
from config import config
from core.key_loader import get_pem_key
import logging

logger = logging.getLogger(__name__)

def _get_cloudfront_signer() -> CloudFrontSigner:
    private_key = config.aws.cloudfront_private_key
    key_pair_id = config.aws.cloudfront_key_pair_id

    # Prefer loading the CloudFront private key from the dedicated keys bucket
    # in production Lambdas where secrets are not injected directly as env vars.
    if not private_key and config.aws.keys_bucket_name:
        private_key = get_pem_key("cloudfront_private_key")
    
    if not private_key or not key_pair_id:
        logger.warning("Cloudfront PK or Key ID is missing. Signed URLs will fail.")
        return None

    try:
        private_key_obj = serialization.load_pem_private_key(
            private_key.encode("utf-8"), password=None
        )
    except Exception as e:
        logger.error(f"Failed to load Cloudfront private key: {e}")
        return None
    
    def rsa_signer(message: bytes) -> bytes:
        return private_key_obj.sign(message, padding.PKCS1v15(), hashes.SHA1())
        
    return CloudFrontSigner(key_pair_id, rsa_signer)

class MediaStorage(S3Boto3Storage):
    default_acl = None
    file_overwrite = False
    bucket_name = config.aws.s3_bucket_name

    def url(self, name, parameters=None, expire=None, http_method=None):
        cloudfront_domain = config.aws.cloudfront_domain
        encoded_name = quote(str(name).lstrip("/"), safe="/~")
        base_url = f"https://{cloudfront_domain}/{encoded_name}"
        
        signer = _get_cloudfront_signer()
        if signer:
            ttl_seconds = max(60, int(config.aws.cloudfront_signed_url_ttl_seconds))
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

            # Wildcard policy allows the same signature to authenticate optimizer
            # query URLs that point to the same CloudFront distribution.
            if config.aws.cloudfront_sign_wildcard:
                private_key = config.aws.cloudfront_private_key
                key_pair_id = config.aws.cloudfront_key_pair_id
                if not private_key and config.aws.keys_bucket_name:
                    private_key = get_pem_key("cloudfront_private_key")

                if private_key and key_pair_id:
                    private_key_obj = serialization.load_pem_private_key(
                        private_key.encode("utf-8"),
                        password=None,
                    )

                    policy = {
                        "Statement": [
                            {
                                "Resource": f"https://{cloudfront_domain}/*",
                                "Condition": {
                                    "DateLessThan": {
                                        "AWS:EpochTime": int(expires_at.timestamp()),
                                    }
                                },
                            }
                        ]
                    }
                    policy_json = json.dumps(policy, separators=(",", ":"))
                    signature = private_key_obj.sign(
                        policy_json.encode("utf-8"),
                        padding.PKCS1v15(),
                        hashes.SHA1(),
                    )

                    def _cf_safe_b64(value: bytes) -> str:
                        return (
                            base64.b64encode(value)
                            .decode("utf-8")
                            .replace("+", "-")
                            .replace("=", "_")
                            .replace("/", "~")
                        )

                    signed_query = urlencode(
                        {
                            "Policy": _cf_safe_b64(policy_json.encode("utf-8")),
                            "Signature": _cf_safe_b64(signature),
                            "Key-Pair-Id": key_pair_id,
                        }
                    )
                    return f"{base_url}?{signed_query}"

            return signer.generate_presigned_url(base_url, date_less_than=expires_at)
            
        return base_url # Fallback if no signed config
