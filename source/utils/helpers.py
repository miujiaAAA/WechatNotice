"""
工具函数模块
"""
from typing import Dict, Any


def validate_headers(headers: Dict[str, Any]) -> tuple[bool, str]:
    """
    验证请求头参数
    
    Args:
        headers: 请求头字典
        
    Returns:
        (是否有效, 错误信息)
    """
    corpid = headers.get('X-Corp-Id')
    if not corpid:
        return False, "请求头缺少 X-Corp-Id"
    
    corpsecret = headers.get('X-Corp-Secret')
    if not corpsecret:
        return False, "请求头缺少 X-Corp-Secret"
    
    agentid = headers.get('X-Agent-Id')
    if not agentid:
        return False, "请求头缺少 X-Agent-Id"
    
    try:
        int(agentid)
    except ValueError:
        return False, "X-Agent-Id 必须是数字"
    
    return True, ""


def format_response(success: bool, data: Any = None, error: str = None) -> Dict[str, Any]:
    """
    格式化响应数据
    
    Args:
        success: 是否成功
        data: 响应数据
        error: 错误信息
        
    Returns:
        格式化后的响应字典
    """
    response = {"success": success}
    
    if success and data:
        response.update(data)
    elif not success and error:
        response["error"] = error
    
    return response
