"""
Flask应用路由
"""
from flask import Flask, request, jsonify
from ..wechat import WechatWorkClient
from ..config_manager import Config
from ..logging_manager import logger


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
    
    @app.route('/send', methods=['POST'])
    def send_message():
        """
        发送企业微信消息接口
        
        请求头:
            X-Corp-Id: 企业ID(必填)
            X-Corp-Secret: 应用密钥(必填)
            X-Agent-Id: 应用AgentId(必填)
            
        请求参数(JSON):
            message: 消息文本内容(必填)
            touser: 接收者用户ID,多个用'|'分隔,默认为@all(可选)
            
        返回:
            JSON格式的发送结果
        """
        client_ip = request.remote_addr
        logger.info(f"收到消息推送请求 - IP: {client_ip}")
        
        try:
            # 从请求头获取企业微信配置
            corpid = request.headers.get('X-Corp-Id')
            corpsecret = request.headers.get('X-Corp-Secret')
            agentid = request.headers.get('X-Agent-Id')
            
            # 验证请求头参数
            if not corpid:
                logger.warning(f"请求头缺少 X-Corp-Id - IP: {client_ip}")
                return jsonify({
                    "success": False,
                    "error": "请求头缺少 X-Corp-Id"
                }), 400
            
            if not corpsecret:
                logger.warning(f"请求头缺少 X-Corp-Secret - IP: {client_ip}")
                return jsonify({
                    "success": False,
                    "error": "请求头缺少 X-Corp-Secret"
                }), 400
            
            if not agentid:
                logger.warning(f"请求头缺少 X-Agent-Id - IP: {client_ip}")
                return jsonify({
                    "success": False,
                    "error": "请求头缺少 X-Agent-Id"
                }), 400
            
            try:
                agentid = int(agentid)
            except ValueError:
                logger.warning(f"X-Agent-Id 格式错误 - IP: {client_ip}")
                return jsonify({
                    "success": False,
                    "error": "X-Agent-Id 必须是数字"
                }), 400
            
            # 获取请求参数
            data = request.get_json()
            
            if not data:
                logger.warning(f"请求体为空 - IP: {client_ip}")
                return jsonify({
                    "success": False,
                    "error": "请求体不能为空"
                }), 400
            
            message = data.get("message")
            if not message:
                logger.warning(f"消息内容为空 - IP: {client_ip}")
                return jsonify({
                    "success": False,
                    "error": "消息内容不能为空"
                }), 400
            
            touser = data.get("touser", "@all")
            
            logger.info(f"准备发送消息 - CorpId: {corpid}, AgentId: {agentid}, Touser: {touser}, Message: {message[:50]}...")
            
            # 创建企业微信客户端
            client = WechatWorkClient(
                corpid=corpid,
                corpsecret=corpsecret,
                agentid=agentid,
                base_url=config.base_url
            )
            
            # 发送消息
            result = client.send_text_message(
                content=message,
                touser=touser
            )
            
            if result.get("success"):
                logger.info(f"消息发送成功 - CorpId: {corpid}, Touser: {touser}")
                return jsonify(result), 200
            else:
                logger.error(f"消息发送失败 - CorpId: {corpid}, Error: {result.get('errmsg', result.get('error'))}")
                return jsonify(result), 500
                
        except Exception as e:
            logger.error(f"服务器错误 - IP: {client_ip}, Error: {str(e)}", exc_info=True)
            return jsonify({
                "success": False,
                "error": f"服务器错误: {str(e)}"
            }), 500
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """健康检查接口"""
        logger.info("健康检查请求")
        return jsonify({
            "status": "ok",
            "service": "企业微信消息推送服务"
        }), 200
    
    return app
