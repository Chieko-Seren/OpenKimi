import os
import secrets
import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# 配置日志
logger = logging.getLogger(__name__)

# 获取数据库URL
DATABASE_URL = os.environ.get(
    "OPENKIMI_DATABASE_URL", 
    "postgresql://postgres:postgres@localhost/openkimi"
)

# 创建SQLAlchemy引擎和会话
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info(f"已连接到数据库: {DATABASE_URL}")
except Exception as e:
    logger.error(f"数据库连接失败: {e}")
    # 使用SQLite作为备用选项
    SQLITE_DATABASE_URL = "sqlite:///./openkimi.db"
    engine = create_engine(SQLITE_DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.warning(f"回退到SQLite数据库: {SQLITE_DATABASE_URL}")

# 声明基类
Base = declarative_base()

# API密钥模型
class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 关系
    user = relationship("User", back_populates="api_keys")
    usage_records = relationship("UsageRecord", back_populates="api_key", cascade="all, delete-orphan")
    
    def is_valid(self) -> bool:
        """检查API密钥是否有效"""
        now = datetime.utcnow()
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < now:
            return False
        return True

# 用户模型
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # 关系
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="user", cascade="all, delete-orphan")

# 使用记录模型
class UsageRecord(Base):
    __tablename__ = "usage_records"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    endpoint = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
    
    # 关系
    user = relationship("User", back_populates="usage_records")
    api_key = relationship("APIKey", back_populates="usage_records")

# 创建数据库表
def create_tables():
    """创建所有表"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"创建数据库表时出错: {e}")

# 数据库会话依赖项
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API密钥管理功能
def generate_api_key() -> str:
    """生成新的API密钥"""
    return f"kimi-{secrets.token_hex(24)}"

def create_api_key(db: Session, name: str, user_id: int, description: Optional[str] = None, 
                  expires_at: Optional[datetime] = None) -> APIKey:
    """创建新的API密钥"""
    api_key = APIKey(
        key=generate_api_key(),
        name=name,
        description=description,
        user_id=user_id,
        expires_at=expires_at
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key

def verify_api_key(db: Session, api_key: str) -> Optional[APIKey]:
    """验证API密钥是否有效"""
    key = db.query(APIKey).filter(APIKey.key == api_key).first()
    if not key:
        return None
    
    if not key.is_valid():
        return None
    
    # 更新最后使用时间
    key.last_used_at = datetime.utcnow()
    db.commit()
    
    return key

def get_all_api_keys(db: Session, user_id: int) -> List[APIKey]:
    """获取用户的所有API密钥"""
    return db.query(APIKey).filter(APIKey.user_id == user_id).all()

def revoke_api_key(db: Session, key_id: int, user_id: int) -> bool:
    """撤销API密钥"""
    key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user_id).first()
    if not key:
        return False
    
    key.is_active = False
    db.commit()
    return True

# 记录API使用情况
def record_api_usage(db: Session, user_id: int, api_key_id: int, endpoint: str, 
                     prompt_tokens: int, completion_tokens: int) -> UsageRecord:
    """记录API使用情况"""
    total_tokens = prompt_tokens + completion_tokens
    record = UsageRecord(
        user_id=user_id,
        api_key_id=api_key_id,
        endpoint=endpoint,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_user_usage(db: Session, user_id: int, start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> dict:
    """获取用户API使用情况统计"""
    query = db.query(
        func.sum(UsageRecord.prompt_tokens).label("prompt_tokens"),
        func.sum(UsageRecord.completion_tokens).label("completion_tokens"),
        func.sum(UsageRecord.total_tokens).label("total_tokens")
    ).filter(UsageRecord.user_id == user_id)
    
    if start_date:
        query = query.filter(UsageRecord.timestamp >= start_date)
    if end_date:
        query = query.filter(UsageRecord.timestamp <= end_date)
    
    result = query.first()
    return {
        "prompt_tokens": result.prompt_tokens or 0,
        "completion_tokens": result.completion_tokens or 0,
        "total_tokens": result.total_tokens or 0
    } 