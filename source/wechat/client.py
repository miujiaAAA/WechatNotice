"""
企业微信客户端
"""
import requests
import time
from typing import Optional, Dict, Any, List
from ..logging_manager import logger


class WechatWorkClient:
    """企业微信应用客户端"""
    
    def __init__(self, corpid: str, corpsecret: str, agentid: int, base_url: str = "https://qyapi.weixin.qq.com/cgi-bin"):
        """
        初始化企业微信客户端
        
        Args:
            corpid: 企业ID
            corpsecret: 应用的凭证密钥
            agentid: 应用的AgentId
            base_url: API基础地址,默认为官方API,可配置为第三方代理
        """
        self.corpid = corpid
        self.corpsecret = corpsecret
        self.agentid = agentid
        self.access_token = None
        self.token_expires_at = 0
        self.base_url = base_url
    
    def get_access_token(self) -> str:
        """
        获取access_token
        
        Returns:
            access_token字符串
            
        Raises:
            Exception: 获取access_token失败时抛出异常
        """
        # 如果token还在有效期内,直接返回
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        url = f"{self.base_url}/gettoken"
        params = {
            "corpid": self.corpid,
            "corpsecret": self.corpsecret
        }
        
        try:
            logger.info(f"请求access_token - CorpId: {self.corpid}")
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                self.access_token = result.get("access_token")
                # 提前5分钟过期,避免临界点问题
                expires_in = result.get("expires_in", 7200)
                self.token_expires_at = time.time() + expires_in - 300
                logger.info(f"access_token获取成功 - CorpId: {self.corpid}")
                return self.access_token
            else:
                logger.error(f"access_token获取失败 - CorpId: {self.corpid}, Error: {result.get('errmsg')}")
                raise Exception(f"获取access_token失败: {result.get('errmsg')}")
        except requests.RequestException as e:
            logger.error(f"access_token请求异常 - CorpId: {self.corpid}, Error: {str(e)}")
            raise Exception(f"请求access_token异常: {str(e)}")
    
    def send_text_message(
        self, 
        content: str, 
        touser: Optional[str] = "@all",
        toparty: Optional[str] = None,
        totag: Optional[str] = None,
        safe: int = 0,
        enable_id_trans: int = 0,
        enable_duplicate_check: int = 0,
        duplicate_check_interval: int = 1800
    ) -> Dict[str, Any]:
        """
        发送文本消息
        
        Args:
            content: 消息内容,最长不超过2048个字节
            touser: 成员ID列表,多个接收者用'|'分隔,最多支持1000个。@all表示全体成员
            toparty: 部门ID列表,多个接收者用'|'分隔,最多支持100个
            totag: 标签ID列表,多个接收者用'|'分隔,最多支持100个
            safe: 是否是保密消息,0表示否,1表示是
            enable_id_trans: 是否开启id转译,0表示否,1表示是
            enable_duplicate_check: 是否开启重复消息检查,0表示否,1表示是
            duplicate_check_interval: 重复消息检查的时间间隔,默认1800s,最大不超过4小时
            
        Returns:
            发送结果字典
        """
        access_token = self.get_access_token()
        url = f"{self.base_url}/message/send?access_token={access_token}"
        
        data = {
            "touser": touser,
            "msgtype": "text",
            "agentid": self.agentid,
            "text": {
                "content": content
            },
            "safe": safe,
            "enable_id_trans": enable_id_trans,
            "enable_duplicate_check": enable_duplicate_check,
            "duplicate_check_interval": duplicate_check_interval
        }
        
        if toparty:
            data["toparty"] = toparty
        if totag:
            data["totag"] = totag
        
        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                return {
                    "success": True,
                    "message": "消息发送成功",
                    "invaliduser": result.get("invaliduser", ""),
                    "invalidparty": result.get("invalidparty", ""),
                    "invalidtag": result.get("invalidtag", "")
                }
            else:
                return {
                    "success": False,
                    "errcode": result.get("errcode"),
                    "errmsg": result.get("errmsg")
                }
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"发送消息异常: {str(e)}"
            }
    
    def send_markdown_message(
        self,
        content: str,
        touser: Optional[str] = "@all",
        toparty: Optional[str] = None,
        totag: Optional[str] = None,
        safe: int = 0,
        enable_duplicate_check: int = 0,
        duplicate_check_interval: int = 1800
    ) -> Dict[str, Any]:
        """
        发送markdown消息
        
        Args:
            content: markdown格式的消息内容,最长不超过2048个字节
            touser: 成员ID列表
            toparty: 部门ID列表
            totag: 标签ID列表
            safe: 是否是保密消息
            enable_duplicate_check: 是否开启重复消息检查
            duplicate_check_interval: 重复消息检查的时间间隔
            
        Returns:
            发送结果字典
        """
        access_token = self.get_access_token()
        url = f"{self.base_url}/message/send?access_token={access_token}"
        
        data = {
            "touser": touser,
            "msgtype": "markdown",
            "agentid": self.agentid,
            "markdown": {
                "content": content
            },
            "safe": safe,
            "enable_duplicate_check": enable_duplicate_check,
            "duplicate_check_interval": duplicate_check_interval
        }
        
        if toparty:
            data["toparty"] = toparty
        if totag:
            data["totag"] = totag
        
        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                return {
                    "success": True,
                    "message": "消息发送成功",
                    "invaliduser": result.get("invaliduser", ""),
                    "invalidparty": result.get("invalidparty", ""),
                    "invalidtag": result.get("invalidtag", "")
                }
            else:
                return {
                    "success": False,
                    "errcode": result.get("errcode"),
                    "errmsg": result.get("errmsg")
                }
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"发送消息异常: {str(e)}"
            }
    
    def send_textcard_message(
        self,
        title: str,
        description: str,
        url: str,
        btntxt: str = "详情",
        touser: Optional[str] = "@all",
        toparty: Optional[str] = None,
        totag: Optional[str] = None,
        enable_duplicate_check: int = 0,
        duplicate_check_interval: int = 1800
    ) -> Dict[str, Any]:
        """
        发送文本卡片消息
        
        Args:
            title: 标题,不超过128个字节
            description: 描述,不超过512个字节
            url: 点击后跳转的链接
            btntxt: 按钮文字,默认为"详情"
            touser: 成员ID列表
            toparty: 部门ID列表
            totag: 标签ID列表
            enable_duplicate_check: 是否开启重复消息检查
            duplicate_check_interval: 重复消息检查的时间间隔
            
        Returns:
            发送结果字典
        """
        access_token = self.get_access_token()
        url_api = f"{self.base_url}/message/send?access_token={access_token}"
        
        data = {
            "touser": touser,
            "msgtype": "textcard",
            "agentid": self.agentid,
            "textcard": {
                "title": title,
                "description": description,
                "url": url,
                "btntxt": btntxt
            },
            "enable_duplicate_check": enable_duplicate_check,
            "duplicate_check_interval": duplicate_check_interval
        }
        
        if toparty:
            data["toparty"] = toparty
        if totag:
            data["totag"] = totag
        
        try:
            response = requests.post(url_api, json=data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                return {
                    "success": True,
                    "message": "消息发送成功",
                    "invaliduser": result.get("invaliduser", ""),
                    "invalidparty": result.get("invalidparty", ""),
                    "invalidtag": result.get("invalidtag", "")
                }
            else:
                return {
                    "success": False,
                    "errcode": result.get("errcode"),
                    "errmsg": result.get("errmsg")
                }
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"发送消息异常: {str(e)}"
            }
    
    def send_news_message(
        self,
        articles: List[Dict[str, str]],
        touser: Optional[str] = "@all",
        toparty: Optional[str] = None,
        totag: Optional[str] = None,
        enable_duplicate_check: int = 0,
        duplicate_check_interval: int = 1800
    ) -> Dict[str, Any]:
        """
        发送图文消息
        
        Args:
            articles: 图文消息列表,最多8条
                每条包含:
                - title: 标题,不超过128个字节
                - description: 描述,不超过512个字节
                - url: 点击后跳转的链接
                - picurl: 图文消息的图片链接
            touser: 成员ID列表
            toparty: 部门ID列表
            totag: 标签ID列表
            enable_duplicate_check: 是否开启重复消息检查
            duplicate_check_interval: 重复消息检查的时间间隔
            
        Returns:
            发送结果字典
        """
        access_token = self.get_access_token()
        url = f"{self.base_url}/message/send?access_token={access_token}"
        
        data = {
            "touser": touser,
            "msgtype": "news",
            "agentid": self.agentid,
            "news": {
                "articles": articles[:8]  # 最多8条
            },
            "enable_duplicate_check": enable_duplicate_check,
            "duplicate_check_interval": duplicate_check_interval
        }
        
        if toparty:
            data["toparty"] = toparty
        if totag:
            data["totag"] = totag
        
        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                return {
                    "success": True,
                    "message": "消息发送成功",
                    "invaliduser": result.get("invaliduser", ""),
                    "invalidparty": result.get("invalidparty", ""),
                    "invalidtag": result.get("invalidtag", "")
                }
            else:
                return {
                    "success": False,
                    "errcode": result.get("errcode"),
                    "errmsg": result.get("errmsg")
                }
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"发送消息异常: {str(e)}"
            }
