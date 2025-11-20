"""
认证Blueprint模块
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, make_response
from flask_wtf.csrf import generate_csrf
from ..auth import UserManager
from ..config_manager import Config
import jwt
from datetime import datetime, timedelta


def create_auth_blueprint():
    """
    创建认证Blueprint
    
    Returns:
        Blueprint实例
    """
    auth_bp = Blueprint('auth', __name__, url_prefix='/auth', template_folder='templates')
    
    # 用户管理器
    user_manager = UserManager()
    
    @auth_bp.route('/login', methods=['GET', 'POST'])
    def login():
        """登录页面"""
        if request.method == 'GET':
            # 生成CSRF Token
            csrf_token = generate_csrf()
            return render_template('auth/login.html', csrf_token=csrf_token)
        
        # POST请求处理登录
        data = request.get_json() or request.form
        username = data.get('username')
        password = data.get('password')
        remember_me = data.get('remember_me', False)
        
        if not username or not password:
            if request.is_json:
                return jsonify({
                    "success": False,
                    "error": "用户名和密码不能为空"
                }), 400
            else:
                return render_template('auth/login.html', error="用户名和密码不能为空")
        
        # 用户认证
        user = user_manager.authenticate(username, password)
        if not user:
            if request.is_json:
                return jsonify({
                    "success": False,
                    "error": "用户名或密码错误"
                }), 401
            else:
                return render_template('auth/login.html', error="用户名或密码错误")
        
        # 生成JWT Token
        config = Config()
        secret_key = config.get("jwt_secret", "wechat_notice_secret_key")
        payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': (datetime.utcnow() + timedelta(days=7)).timestamp()
        }
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        # 设置Session
        session['user_id'] = user.id
        session['username'] = user.username
        
        if request.is_json:
            response = jsonify({
                "success": True,
                "message": "登录成功",
                "token": token
            })
        else:
            response = redirect(url_for('dashboard.index'))
        
        # 设置Cookie
        response.set_cookie('auth_token', token, max_age=7*24*60*60, httponly=True)
        if remember_me:
            response.set_cookie('username', username, max_age=30*24*60*60)
        
        return response
    
    @auth_bp.route('/logout', methods=['POST'])
    def logout():
        """退出登录"""
        # 清除Session
        session.pop('user_id', None)
        session.pop('username', None)
        
        # 清除Cookie
        response = jsonify({"success": True, "message": "退出成功"})
        response.set_cookie('auth_token', '', expires=0)
        
        return response
    
    @auth_bp.route('/check', methods=['GET'])
    def check_login():
        """检查登录状态"""
        if 'user_id' in session:
            return jsonify({
                "success": True,
                "logged_in": True,
                "user": {
                    "id": session['user_id'],
                    "username": session['username']
                }
            })
        
        token = request.cookies.get('auth_token') or request.headers.get('Authorization')
        if token:
            try:
                if token.startswith('Bearer '):
                    token = token[7:]
                
                config = Config()
                secret_key = config.get("jwt_secret", "wechat_notice_secret_key")
                payload = jwt.decode(token, secret_key, algorithms=['HS256'])
                
                return jsonify({
                    "success": True,
                    "logged_in": True,
                    "user": {
                        "id": payload['user_id'],
                        "username": payload['username']
                    }
                })
            except jwt.InvalidTokenError:
                pass
        
        return jsonify({
            "success": True,
            "logged_in": False
        })
    
    return auth_bp
