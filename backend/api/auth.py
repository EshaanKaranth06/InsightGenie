import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions

# Initialize Clerk client using your secret key from .env
clerk_client = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))

# Use HTTPBearer for JWT tokens
security = HTTPBearer()

# Clerk typically expects just the domain, not the full URL
ALLOWED_FRONTEND_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    # Add your production frontend URL here later
]

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Dependency to verify the Clerk JWT token and return the user ID.
    Raises HTTPException if the token is invalid or expired.
    """
    token = credentials.credentials
    
    print("\n--- Verifying Token ---")
    print(f"Received Token (first 10 chars): {token[:10]}...")
    
    # Check if Clerk secret key is configured
    clerk_secret = os.getenv("CLERK_SECRET_KEY")
    if not clerk_secret:
        print("CRITICAL ERROR: CLERK_SECRET_KEY is not set.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication configuration error.",
        )

    try:
        # Create an httpx.Request object with the Authorization header
        request = httpx.Request(
            method="GET",
            url="http://localhost",  # URL doesn't matter for token verification
            headers={"authorization": f"Bearer {token}"}
        )
        
        # Verify the JWT token using Clerk's authenticate_request
        request_state = clerk_client.authenticate_request(
            request=request,
            options=AuthenticateRequestOptions(
                authorized_parties=ALLOWED_FRONTEND_ORIGINS
            )
        )

        # Check if authentication was successful
        if not request_state.is_signed_in:
            print(f"Authentication FAILED: {request_state.reason}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired token: {request_state.reason}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract the user ID from the token payload
        user_id = request_state.payload.get("sub") if request_state.payload else None
        print(f"User ID from token: {user_id}")
        
        if not user_id:
            print("Authentication FAILED: User ID missing from payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials: User ID missing",
                headers={"WWW-Authenticate": "Bearer"},
            )

        print(f"Authentication SUCCESS for user: {user_id}")
        return user_id

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any other unexpected errors during verification
        print(f"Unexpected authentication error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )