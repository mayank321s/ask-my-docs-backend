# utils/auth_utils.py
import bcrypt
from fastapi.params import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import HTTPException
from fastapi import status
import os

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 24))

class JWTHandler:
    @staticmethod
    def createAccessToken(userId: int, emailAddress: str, roleCode: str) -> str:
        """Create JWT token with user_id and email"""
        payload = {
            "userId": userId,
            "emailAddress": emailAddress,
            "roleCode": roleCode,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, JWT_SECRET_KEY)
        return token
    
    @staticmethod
    def decodeAccessToken(token: str) -> Optional[Dict]:
        """Decode JWT token and return payload"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid token"
            )


# Security scheme for JWT
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Dependency to get current user from JWT token"""
    token = credentials.credentials
    payload = JWTHandler.decodeAccessToken(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return payload
