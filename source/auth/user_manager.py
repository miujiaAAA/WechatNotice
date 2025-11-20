"""
用户管理模块
"""
import hashlib
import secrets
from typing import Optional, Dict
from datetime import datetime, timedelta


class User:
    """用户类"""
    
    def __init__(self, user_id: str, username: str, password_hash: str, is_active: bool = True):
        self.id = user_id
        self.username = username
        self.password_hash = password_hash
        self.is_active = is_active
        self.is_authenticated = True
        self.is_anonymous = False
    
    def get_id(self):
        """获取用户ID"""
        return self.id
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple:
        """
        密码哈希
        
        Args:
            password: 明文密码
            salt: 盐值
            
        Returns:
            (password_hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        pwd_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        return pwd_hash, salt
    
    def check_password(self, password: str, salt: str) -> bool:
        """
        验证密码
        
        Args:
            password: 输入的密码
            salt: 盐值
            
        Returns:
            是否匹配
        """
        pwd_hash, _ = self.hash_password(password, salt)
        return pwd_hash == self.password_hash


class UserManager:
    """用户管理器"""
    
    def __init__(self):
        self.users = {}
        self.salts = {}
        self._init_default_user()
    
    def _init_default_user(self):
        """初始化默认管理员用户"""
        # 默认用户名: admin, 密码: admin123
        # 生产环境请修改默认密码
        password_hash, salt = User.hash_password("admin123")
        self.users["admin"] = User(
            user_id="1",
            username="admin",
            password_hash=password_hash
        )
        self.salts["admin"] = salt
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            用户对象或None
        """
        return self.users.get(username)
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        根据ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象或None
        """
        for user in self.users.values():
            if user.id == user_id:
                return user
        return None
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        用户认证
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            认证成功返回用户对象,否则返回None
        """
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        salt = self.salts.get(username)
        if not salt:
            return None
        
        if user.check_password(password, salt):
            return user
        
        return None
    
    def add_user(self, username: str, password: str) -> bool:
        """
        添加用户
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            是否成功
        """
        if username in self.users:
            return False
        
        user_id = str(len(self.users) + 1)
        password_hash, salt = User.hash_password(password)
        
        self.users[username] = User(
            user_id=user_id,
            username=username,
            password_hash=password_hash
        )
        self.salts[username] = salt
        return True
