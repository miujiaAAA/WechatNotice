"""
企业微信消息推送服务启动入口
"""
from source import create_app, logger


if __name__ == "__main__":
    logger.info("="*50)
    logger.info("企业微信消息推送服务启动")
    logger.info("="*50)
    
    app = create_app("config/config.json")
    
    logger.info("服务启动在 http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
