"""
认证装饰器模块
"""
from functools import wraps
from flask import request, jsonify, redirect, url_for, session
from flask_login import current_user
import jwt
from datetime import datetime, timedelta
from ..config_manager import Config


def login_required_api(f):
    """
    API接口登录验证装饰器
    
    Returns:
        装饰器函数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查Session
        if 'user_id' not in session:
            # 检查JWT Token
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({
                    "success": False,
                    "error": "未登录，请先登录"
                }), 401
            
            # 验证Token
            try:
                config = Config()
                secret_key = config.get("jwt_secret", "wechat_notice_secret_key")
                payload = jwt.decode(token.replace('Bearer ', ''), secret_key, algorithms=['HS256'])
                if payload.get('exp') < datetime.utcnow().timestamp():
                    return jsonify({
                        "success": False,
                        "error": "Token已过期"
                    }), 401
            except jwt.InvalidTokenError:
                return jsonify({
                    "success": False,
                    "error": "无效的Token"
                }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def login_required_page(f):
    """
    页面登录验证装饰器
    
    Returns:
        装饰器函数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查Session
        if 'user_id' not in session:
            # 检查JWT Token
            token = request.cookies.get('auth_token')
            if not token:
                return redirect(url_for('auth.login'))
            
            # 验证Token
            try:
                config = Config()
                secret_key = config.get("jwt_secret", "wechat_notice_secret_key")
                payload = jwt.decode(token, secret_key, algorithms=['HS256'])
                if payload.get('exp') < datetime.utcnow().timestamp():
                    return redirect(url_for('auth.login'))
            except jwt.InvalidTokenError:
                return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function
