"""
Authentication and authorization module
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, validator

from config import settings
from db_utils import get_user_by_username, get_user_by_email, create_user, verify_user_password, get_user_by_id

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create router
auth_router = APIRouter(prefix="/api/auth", tags=["authentication"])

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
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    password: str = Field(..., min_length=10, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

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
) -> Dict[str, Any]:
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
    
    # Fetch user from database
    user = await get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception

    if not user['is_active']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user

async def get_current_active_superuser(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current superuser"""
    if not current_user.get('is_superuser', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Authentication endpoints
@auth_router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    # Check if username already exists
    existing_user = await get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = await get_user_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_password = get_password_hash(user_data.password)
    user = await create_user(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password
    )
    
    return UserResponse(
        id=user['id'],
        email=user['email'],
        username=user['username'],
        is_active=user['is_active'],
        created_at=user['created_at'],
        has_api_key=bool(user.get('api_key'))
    )

@auth_router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user and return access token"""
    # Verify user credentials
    user = await verify_user_password(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user['is_active']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
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
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user['id'],
        email=current_user['email'],
        username=current_user['username'],
        is_active=current_user['is_active'],
        created_at=current_user['created_at'],
        has_api_key=bool(current_user.get('api_key'))
    )

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=10, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

@auth_router.put("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Change user password"""
    # Verify current password
    if not verify_password(request.current_password, current_user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Hash new password and update in database
    from db_utils import update_user_password
    new_hashed_password = get_password_hash(request.new_password)
    await update_user_password(current_user['id'], new_hashed_password)
    
    return {"message": "Password changed successfully"}