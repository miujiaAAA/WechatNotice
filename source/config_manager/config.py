"""
配置管理模块
"""
import json
from pathlib import Path
from typing import Dict, Any


class Config:
    """配置管理类"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        初始化配置
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        return self._config.get(key, default)
    
    @property
    def base_url(self) -> str:
        """获取API基础URL"""
        return self._config.get("base_url", "https://qyapi.weixin.qq.com/cgi-bin")
    
    @property
    def api_token(self) -> str:
        """获取API认证Token"""
        return self._config.get("api_token", "")
    
    def reload(self):
        """重新加载配置"""
        self._config = self._load_config()
