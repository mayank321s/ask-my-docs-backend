from fastapi import HTTPException
from fastapi import status
from app.core.models.pydantic.auth import LoginRequestDto, RegisterRequestDto
from app.core.repository.users_repository import UserRepository
from app.utils.jwt import JWTHandler
from app.utils.password_hasher import PasswordHasher

class AuthService:
    @staticmethod
    async def handleLogin(request: LoginRequestDto):
        try:
            user = await UserRepository.findOneByClause({"emailAddress": request.emailAddress})
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="User not found"
                )
            
            if not PasswordHasher.verifyPassword(request.password, user.password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    detail="Incorrect password"
                )
            
            accessToken = JWTHandler.createAccessToken(
                userId=user.id, 
                emailAddress=user.emailAddress,
                roleCode=user.roleCode
            )
            
            return {
                "message": "Login successful",
                "firstName": user.firstName,
                "lastName": user.lastName,
                "emailAddress": user.emailAddress,
                "roleCode": user.roleCode,
                "accessToken": accessToken,
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=str(e)
            )
        
    @staticmethod
    async def handleRegister(request: RegisterRequestDto):
        try:
            existing_user = await UserRepository.findOneByClause({"emailAddress": request.emailAddress})
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, 
                    detail="User already exists"
                )
            
            hashed_password = PasswordHasher.hashPassword(request.password)
            
            userDataToCreate = {
                "firstName": request.firstName,
                "lastName": request.lastName,
                "emailAddress": request.emailAddress,
                "password": hashed_password,
                "roleCode": "user"
            }
            
            newUser = await UserRepository.create(userDataToCreate)
            
            accessToken = JWTHandler.createAccessToken(
                userId=newUser.id, 
                emailAddress=newUser.emailAddress,
                roleCode=newUser.roleCode
            )
            
            return {
                "message": "Registration successful",
                "accessToken": accessToken,
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=str(e)
            )
