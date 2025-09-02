# utils/auth_utils.py
import bcrypt
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
    def createAccessToken(userId: int, emailAddress: str) -> str:
        """Create JWT token with user_id and email"""
        payload = {
            "userId": userId,
            "emailAddress": emailAddress,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, JWT_SECRET_KEY)
        return token
    
    @staticmethod
    def decodeAccessToken(token: str) -> Optional[Dict]:
        """Decode JWT token and return payload"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
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
