"""
Flask应用路由
"""
from flask import Flask, jsonify, render_template
from ..config_manager import Config
from ..logging_manager import logger
from ..database import init_database
from ..utils import require_token
from .wechat_blueprint import create_wechat_blueprint
from ..auth import create_auth_blueprint
from ..dashboard import create_dashboard_blueprint
import os


def create_app(config_path: str = "config/config.json") -> Flask:
    """
    创建Flask应用
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Flask应用实例
    """
    app = Flask(__name__)
    
    # 配置密钥
    config_obj = Config(config_path)
    app.secret_key = config_obj.get("flask_secret_key", "wechat_notice_secret_key_2025")
    
    # 配置模板和静态文件目录
    import os
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app.template_folder = os.path.join(current_dir, 'templates')
    app.static_folder = os.path.join(current_dir, 'static')
    
    # 初始化数据库
    db = init_database()
    
    # 注册Blueprint
    wechat_bp = create_wechat_blueprint(config_obj, db, require_token)
    app.register_blueprint(wechat_bp)
    
    auth_bp = create_auth_blueprint()
    app.register_blueprint(auth_bp)
    
    dashboard_bp = create_dashboard_blueprint()
    app.register_blueprint(dashboard_bp)
    
    @app.route('/')
    def index():
        """首页"""
        return render_template('index.html')
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """健康检查接口"""
        logger.info("健康检查请求")
        return jsonify({
            "status": "ok",
            "service": "企业微信消息推送服务"
        }), 200
    
    return app
