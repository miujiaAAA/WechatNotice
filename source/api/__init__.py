"""
API路由模块
"""
from .routes import create_app
from .wechat_blueprint import create_wechat_blueprint

__all__ = ['create_app', 'create_wechat_blueprint']
