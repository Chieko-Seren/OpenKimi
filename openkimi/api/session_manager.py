import time
import uuid
import logging
from typing import Dict, Optional, List, Any
from openkimi.core.engine import KimiEngine

# 设置日志
logger = logging.getLogger(__name__)

class SessionManager:
    """
    会话状态管理器，用于管理KimiEngine的会话状态
    
    使用字典存储会话状态，避免每次请求都重置引擎
    """
    
    def __init__(self, engine_factory):
        """
        初始化会话状态管理器
        
        Args:
            engine_factory: 创建KimiEngine实例的工厂函数
        """
        self.engine_factory = engine_factory
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeouts: Dict[str, float] = {}
        self.default_timeout = 3600  # 默认会话超时时间（秒）
        self.cleanup_interval = 300  # 清理间隔（秒）
        self.last_cleanup = time.time()
        
    def create_session(self, session_id: Optional[str] = None, timeout: Optional[int] = None) -> str:
        """
        创建新会话
        
        Args:
            session_id: 可选的会话ID，如果不提供则自动生成
            timeout: 可选的会话超时时间（秒）
            
        Returns:
            str: 会话ID
        """
        # 如果提供了会话ID且已存在，则返回该会话ID
        if session_id and session_id in self.sessions:
            # 更新超时时间
            self.session_timeouts[session_id] = time.time() + (timeout or self.default_timeout)
            return session_id
            
        # 生成新的会话ID
        new_session_id = session_id or f"session-{uuid.uuid4()}"
        
        # 创建新的KimiEngine实例
        try:
            engine = self.engine_factory()
            self.sessions[new_session_id] = {
                "engine": engine,
                "created_at": time.time(),
                "last_accessed": time.time()
            }
            self.session_timeouts[new_session_id] = time.time() + (timeout or self.default_timeout)
            logger.info(f"创建新会话: {new_session_id}")
            return new_session_id
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            raise RuntimeError(f"创建会话失败: {e}")
    
    def get_session(self, session_id: str) -> Optional[KimiEngine]:
        """
        获取会话的KimiEngine实例
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[KimiEngine]: KimiEngine实例，如果会话不存在则返回None
        """
        # 清理过期会话
        self._cleanup_expired_sessions()
        
        # 如果会话不存在，返回None
        if session_id not in self.sessions:
            logger.warning(f"会话不存在: {session_id}")
            return None
            
        # 更新最后访问时间
        self.sessions[session_id]["last_accessed"] = time.time()
        self.session_timeouts[session_id] = time.time() + self.default_timeout
        
        return self.sessions[session_id]["engine"]
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功删除
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            if session_id in self.session_timeouts:
                del self.session_timeouts[session_id]
            logger.info(f"删除会话: {session_id}")
            return True
        return False
    
    def _cleanup_expired_sessions(self) -> None:
        """清理过期会话"""
        current_time = time.time()
        
        # 如果距离上次清理时间不足清理间隔，则不清理
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
            
        self.last_cleanup = current_time
        expired_sessions = []
        
        # 找出过期会话
        for session_id, timeout in self.session_timeouts.items():
            if current_time > timeout:
                expired_sessions.append(session_id)
                
        # 删除过期会话
        for session_id in expired_sessions:
            self.delete_session(session_id)
            
        if expired_sessions:
            logger.info(f"清理了 {len(expired_sessions)} 个过期会话") 