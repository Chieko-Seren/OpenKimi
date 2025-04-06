import os
import logging
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, List, Union

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from openkimi.api.database import get_db, User, APIKey, verify_api_key
from openkimi.api.models import UserCreate, UserResponse, APIKeyCreate, APIKeyResponse

# 配置日志
logger = logging.getLogger(__name__)

# API密钥认证
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# 默认管理员用户设置
DEFAULT_ADMIN_USERNAME = os.environ.get("OPENKIMI_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.environ.get("OPENKIMI_ADMIN_PASSWORD", "adminpassword")
DEFAULT_ADMIN_EMAIL = os.environ.get("OPENKIMI_ADMIN_EMAIL", "admin@example.com")

# 密码处理函数
def hash_password(password: str) -> str:
    """对密码进行哈希处理"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# 创建默认管理员用户
def create_default_admin(db: Session):
    """创建默认管理员用户（如果不存在）"""
    admin = db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
    if not admin:
        admin = User(
            username=DEFAULT_ADMIN_USERNAME,
            email=DEFAULT_ADMIN_EMAIL,
            hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
            is_admin=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        logger.info(f"已创建默认管理员用户: {DEFAULT_ADMIN_USERNAME}")
    return admin

# 用户管理函数
def create_user(db: Session, user_data: UserCreate) -> User:
    """创建新用户"""
    # 检查用户名和邮箱是否已存在
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(status_code=400, detail="用户名已存在")
        else:
            raise HTTPException(status_code=400, detail="邮箱已存在")
    
    # 创建新用户
    hashed_password = hash_password(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_admin=user_data.is_admin if user_data.is_admin is not None else False
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """通过用户名获取用户"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """通过邮箱获取用户"""
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """验证用户密码"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# 依赖项：验证API密钥
async def get_api_key(
    api_key: str = Depends(api_key_header),
    db: Session = Depends(get_db)
) -> APIKey:
    """验证API密钥并返回对应的API密钥记录"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要API密钥",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    api_key_record = verify_api_key(db, api_key)
    if not api_key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API密钥",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    return api_key_record

# 依赖项：验证管理员权限
async def get_admin_user(
    api_key: APIKey = Depends(get_api_key),
    db: Session = Depends(get_db)
) -> User:
    """验证用户是否为管理员"""
    user = db.query(User).filter(User.id == api_key.user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限",
        )
    return user

# 将数据库模型转换为API响应模型
def user_to_response(user: User) -> UserResponse:
    """将用户模型转换为API响应"""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at
    )

def apikey_to_response(api_key: APIKey) -> APIKeyResponse:
    """将API密钥模型转换为API响应"""
    return APIKeyResponse(
        id=api_key.id,
        key=api_key.key,
        name=api_key.name,
        description=api_key.description,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at
    ) 