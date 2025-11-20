"""
Flask应用路由
"""
import time
from flask import Flask, request, jsonify
from ..wechat import WechatWorkClient
from ..config_manager import Config
from ..logging_manager import logger
from ..database import init_database


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
        start_time = time.time()
        client_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')
        method = request.method
        path = request.path
        
        # 初始化请求信息
        corpid = None
        agentid = None
        touser = None
        message = None
        status_code = 200
        success = True
        error_msg = None
        
        logger.info(f"收到消息推送请求 - IP: {client_ip}")
        
        try:
            # 从请求头获取企业微信配置
            corpid = request.headers.get('X-Corp-Id')
            corpsecret = request.headers.get('X-Corp-Secret')
            agentid = request.headers.get('X-Agent-Id')
            
            # 验证请求头参数
            if not corpid:
                status_code = 400
                success = False
                error_msg = "请求头缺少 X-Corp-Id"
                logger.warning(f"{error_msg} - IP: {client_ip}")
                return jsonify({
                    "success": False,
                    "error": error_msg
                }), status_code
            
            if not corpsecret:
                status_code = 400
                success = False
                error_msg = "请求头缺少 X-Corp-Secret"
                logger.warning(f"{error_msg} - IP: {client_ip}")
                return jsonify({
                    "success": False,
                    "error": error_msg
                }), status_code
            
            if not agentid:
                status_code = 400
                success = False
                error_msg = "请求头缺少 X-Agent-Id"
                logger.warning(f"{error_msg} - IP: {client_ip}")
                return jsonify({
                    "success": False,
                    "error": error_msg
                }), status_code
            
            try:
                agentid = int(agentid)
            except ValueError:
                status_code = 400
                success = False
                error_msg = "X-Agent-Id 必须是数字"
                logger.warning(f"{error_msg} - IP: {client_ip}")
                return jsonify({
                    "success": False,
                    "error": error_msg
                }), status_code
            
            # 获取请求参数
            data = request.get_json()
            
            if not data:
                status_code = 400
                success = False
                error_msg = "请求体为空"
                logger.warning(f"{error_msg} - IP: {client_ip}")
                return jsonify({
                    "success": False,
                    "error": "请求体不能为空"
                }), status_code
            
            message = data.get("message")
            if not message:
                status_code = 400
                success = False
                error_msg = "消息内容为空"
                logger.warning(f"{error_msg} - IP: {client_ip}")
                return jsonify({
                    "success": False,
                    "error": "消息内容不能为空"
                }), status_code
            
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
                status_code = 500
                success = False
                error_msg = result.get('errmsg', result.get('error'))
                logger.error(f"消息发送失败 - CorpId: {corpid}, Error: {error_msg}")
                return jsonify(result), status_code
                
        except Exception as e:
            status_code = 500
            success = False
            error_msg = str(e)
            logger.error(f"服务器错误 - IP: {client_ip}, Error: {error_msg}", exc_info=True)
            return jsonify({
                "success": False,
                "error": f"服务器错误: {error_msg}"
            }), status_code
        
        finally:
            # 计算响应时间(毫秒)
            response_time = (time.time() - start_time) * 1000
            
            # 将请求日志存入数据库
            try:
                db.insert_request_log(
                    method=method,
                    path=path,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    corp_id=corpid,
                    agent_id=agentid,
                    touser=touser,
                    message=message[:500] if message else None,  # 限制消息长度
                    status_code=status_code,
                    response_time=round(response_time, 2),
                    success=success,
                    error_message=error_msg
                )
            except Exception as db_error:
                logger.error(f"记录请求日志到数据库失败: {str(db_error)}")
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """健康检查接口"""
        logger.info("健康检查请求")
        return jsonify({
            "status": "ok",
            "service": "企业微信消息推送服务"
        }), 200
    
    @app.route('/logs', methods=['GET'])
    def get_logs():
        """
        获取请求日志
        
        请求参数:
            limit: 返回数量,默认100
            corp_id: 过滤企业ID(可选)
        """
        try:
            limit = request.args.get('limit', 100, type=int)
            corp_id = request.args.get('corp_id')
            
            if corp_id:
                logs = db.get_logs_by_corp_id(corp_id, limit)
            else:
                logs = db.get_recent_logs(limit)
            
            return jsonify({
                "success": True,
                "count": len(logs),
                "data": logs
            }), 200
        except Exception as e:
            logger.error(f"获取日志失败: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/statistics', methods=['GET'])
    def get_statistics():
        """
        获取统计数据
        
        请求参数:
            days: 统计天数,默认7天
        """
        try:
            days = request.args.get('days', 7, type=int)
            stats = db.get_statistics(days)
            
            return jsonify({
                "success": True,
                "data": stats
            }), 200
        except Exception as e:
            logger.error(f"获取统计数据失败: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    return app
