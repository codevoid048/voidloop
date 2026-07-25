"""
Firebase Authentication Token Verification Utilities
"""

import logging
import requests
import jwt
from django.core.cache import cache

logger = logging.getLogger(__name__)

def verify_firebase_id_token(token: str, project_id: str) -> dict:
    """
    Verify a Firebase ID Token (JWT) locally.
    Returns the decoded token payload.
    """
    if not project_id:
        raise ValueError("FIREBASE_PROJECT_ID is not configured")

    # 1. Get header to find kid
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise ValueError("No kid found in token header")
    except Exception as e:
        raise ValueError(f"Invalid token format: {str(e)}")

    # 2. Fetch public keys (Google certificates) and cache them for 1 hour
    cache_key = "firebase_public_certs"
    certs = cache.get(cache_key)
    if not certs:
        try:
            res = requests.get(
                "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com",
                timeout=5
            )
            res.raise_for_status()
            certs = res.json()
            # Cache for 1 hour
            cache.set(cache_key, certs, timeout=3600)
        except Exception as e:
            raise ValueError(f"Failed to fetch Firebase public certs: {str(e)}")

    # 3. Retrieve the cert corresponding to the kid
    cert_pem = certs.get(kid)
    if not cert_pem:
        raise ValueError(f"Public key not found for kid: {kid}")

    # Parse public key from X509 certificate
    try:
        from cryptography.x509 import load_pem_x509_certificate
        cert_obj = load_pem_x509_certificate(cert_pem.encode("utf-8"))
        public_key = cert_obj.public_key()
    except Exception as e:
        raise ValueError(f"Failed to parse public key from certificate: {str(e)}")

    # 4. Decode and verify signature
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=project_id,
            issuer=f"https://securetoken.google.com/{project_id}"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Firebase token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid Firebase token: {str(e)}")
