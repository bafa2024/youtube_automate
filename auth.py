"""
Authentication and authorization module
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from config import settings
from db_utils import get_user_by_username, get_user_by_email, create_user, verify_user_password, get_user_by_id

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Token models
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime
    has_api_key: bool

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Removed: async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
# Removed: async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
# Removed: async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:

async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> Any: # Changed return type hint to Any as User is removed
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        if username is None or user_id is None:
            raise credentials_exception
            
        token_data = TokenData(username=username, user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    # In a real application, you would fetch the user from a database here
    # For now, we'll simulate a user object
    # This part needs to be replaced with actual database interaction
    # Example: user = await get_user_by_username(db, username=token_data.username)
    # For now, we'll return a placeholder user
    class MockUser:
        def __init__(self, id: int, username: str, email: str, is_active: bool, created_at: datetime):
            self.id = id
            self.username = username
            self.email = email
            self.is_active = is_active
            self.created_at = created_at
            self.hashed_password = "mock_hashed_password" # Placeholder
            self.is_superuser = False # Placeholder
            self.encrypted_api_key = "mock_encrypted_api_key" # Placeholder

    # Simulate fetching a user
    # In a real app, this would be:
    # user = await get_user_by_username(db, username=token_data.username)
    # if user is None:
    #     raise credentials_exception
    
    # Simulate user existence
    if username == "testuser":
        user = MockUser(id=1, username=username, email="test@example.com", is_active=True, created_at=datetime.utcnow())
    else:
        raise credentials_exception # Simulate user not found

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user

async def get_current_active_superuser(
    current_user: Any # Changed type hint to Any
) -> Any: # Changed return type hint to Any
    """Get current superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Authentication endpoints (to be added to main.py)
from fastapi import APIRouter

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@auth_router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    existing_username = await get_user_by_username(user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user_id = await create_user(user_data.username, user_data.email, hashed_password)
    user = await get_user_by_id(user_id)
    return UserResponse(
        id=user['id'],
        email=user['email'],
        username=user['username'],
        is_active=bool(user['is_active']),
        created_at=user['created_at'],
        has_api_key=bool(user['encrypted_api_key'])
    )

@auth_router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await verify_user_password(form_data.username, form_data.password, verify_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['username'], "user_id": user['id']},
        expires_delta=access_token_expires
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Any # Changed type hint to Any
):
    """Get current user information"""
    # In a real app, this would involve fetching user details from a database
    # For now, we'll simulate fetching
    class MockUser:
        def __init__(self, id: int, email: str, username: str, is_active: bool, created_at: datetime):
            self.id = id
            self.email = email
            self.username = username
            self.is_active = is_active
            self.created_at = created_at
            self.hashed_password = "mock_hashed_password" # Placeholder
            self.is_superuser = False # Placeholder
            self.encrypted_api_key = None # Placeholder

    user = MockUser(id=1, email="test@example.com", username="testuser", is_active=True, created_at=datetime.utcnow())

    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        created_at=user.created_at,
        has_api_key=bool(user.encrypted_api_key)
    )

@auth_router.post("/logout")
async def logout(current_user: Any # Changed type hint to Any
):
    """Logout (client should discard token)"""
    # In a more complex setup, you might want to blacklist the token
    return {"message": "Successfully logged out"}

@auth_router.put("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: Any # Changed type hint to Any
    # db: AsyncSession = Depends(get_db) # Removed db dependency
):
    """Change user password"""
    # In a real app, this would involve updating the user's password in a database
    # For now, we'll simulate the update
    if not verify_password(current_password, "mock_hashed_password"): # Simulate current password check
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # In a real app, you would update current_user.hashed_password in a database session
    # For now, we'll just return a success message
    return {"message": "Password changed successfully"}