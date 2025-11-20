"""
认证模块
"""
from functools import wraps
from flask import request, jsonify
from typing import Callable


def require_token(config):
    """
    Token认证装饰器
    
    Args:
        config: 配置对象
        
    Returns:
        装饰器函数
    """
    def decorator(f: Callable):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 从请求头获取Token
            token = request.headers.get('X-API-Token')
            
            # 验证Token
            if not token:
                return jsonify({
                    "success": False,
                    "error": "缺少认证Token,请在请求头中添加 X-API-Token"
                }), 401
            
            # 检查Token是否匹配
            if token != config.api_token:
                return jsonify({
                    "success": False,
                    "error": "Token验证失败"
                }), 403
            
            # Token验证通过,执行原函数
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
