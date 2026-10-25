from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.db import get_db
from app.models import User
ALGORITHM="HS256"
pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
def hash_password(password:str)->str:
    if len(password)<12: raise ValueError("Password must contain at least 12 characters")
    return pwd_context.hash(password)
def verify_password(password:str,password_hash:str)->bool: return pwd_context.verify(password,password_hash)
def create_access_token(user_id:str)->str:
    exp=datetime.now(timezone.utc)+timedelta(minutes=30)
    return jwt.encode({"sub":user_id,"exp":exp},settings.secret_key,algorithm=ALGORITHM)
def get_current_user(token:str=Depends(oauth2_scheme),db:Session=Depends(get_db))->User:
    try: user_id=jwt.decode(token,settings.secret_key,algorithms=[ALGORITHM]).get("sub")
    except JWTError: user_id=None
    user=db.get(User,user_id) if user_id else None
    if not user or not user.is_active: raise HTTPException(401,"Invalid authentication")
    return user
