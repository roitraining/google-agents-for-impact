# app/auth.py
from flask import request

TEST_USER = "testuser@roitraining.com"

def current_user_id() -> str:
    """
    Return the current user's email.
    - If running behind IAP, pull from X-Goog-Authenticated-User-Email header.
    - Otherwise, return a test user for local/dev use.
    """
    hdr = request.headers.get("X-Goog-Authenticated-User-Email")
    if hdr:
        # Header looks like "accounts.google.com:someone@example.com"
        parts = hdr.split(":")
        if len(parts) == 2:
            return parts[1]
        return hdr  # fallback in case format changes
    return TEST_USER
