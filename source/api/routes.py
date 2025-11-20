"""
Flask应用路由
"""
from flask import Flask, jsonify
from ..config_manager import Config
from ..logging_manager import logger
from ..database import init_database
from ..utils import require_token
from .wechat_blueprint import create_wechat_blueprint


def create_app(config_path: str = "config/config.json") -> Flask:
    """
    创建Flask应用
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Flask应用实例
    """
    app = Flask(__name__)
    
    # 加载配置
    config = Config(config_path)
    
    # 初始化数据库
    db = init_database()
    
    # 注册Blueprint
    wechat_bp = create_wechat_blueprint(config, db, require_token)
    app.register_blueprint(wechat_bp)
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """健康检查接口"""
        logger.info("健康检查请求")
        return jsonify({
            "status": "ok",
            "service": "企业微信消息推送服务"
        }), 200
    
    return app
