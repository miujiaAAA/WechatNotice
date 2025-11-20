"""
SQLite数据库管理
"""
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import contextmanager


class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self, db_path: str = "data/wechat_notice.db"):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_tables()
    
    def _ensure_db_dir(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    @contextmanager
    def get_connection(self):
        """
        获取数据库连接(上下文管理器)
        
        Yields:
            sqlite3.Connection: 数据库连接
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使查询结果可以按列名访问
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_tables(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建请求日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS request_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    method VARCHAR(10),
                    path VARCHAR(255),
                    client_ip VARCHAR(50),
                    user_agent TEXT,
                    corp_id VARCHAR(100),
                    agent_id INTEGER,
                    touser VARCHAR(255),
                    message TEXT,
                    status_code INTEGER,
                    response_time REAL,
                    success BOOLEAN,
                    error_message TEXT,
                    created_at DATETIME
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON request_logs(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_corp_id 
                ON request_logs(corp_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_status 
                ON request_logs(status_code)
            ''')
            
            conn.commit()
    
    def insert_request_log(
        self,
        method: str,
        path: str,
        client_ip: str,
        user_agent: Optional[str] = None,
        corp_id: Optional[str] = None,
        agent_id: Optional[int] = None,
        touser: Optional[str] = None,
        message: Optional[str] = None,
        status_code: Optional[int] = None,
        response_time: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> int:
        """
        插入请求日志
        
        Args:
            method: 请求方法
            path: 请求路径
            client_ip: 客户端IP
            user_agent: User-Agent
            corp_id: 企业ID
            agent_id: 应用ID
            touser: 接收者
            message: 消息内容
            status_code: HTTP状态码
            response_time: 响应时间(毫秒)
            success: 是否成功
            error_message: 错误信息
            
        Returns:
            插入记录的ID
        """
        # 获取当前本地时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO request_logs (
                    timestamp, method, path, client_ip, user_agent,
                    corp_id, agent_id, touser, message,
                    status_code, response_time, success, error_message, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                current_time, method, path, client_ip, user_agent,
                corp_id, agent_id, touser, message,
                status_code, response_time, success, error_message, current_time
            ))
            return cursor.lastrowid
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取最近的请求日志
        
        Args:
            limit: 返回记录数量
            
        Returns:
            日志记录列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM request_logs 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_logs_by_corp_id(self, corp_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        根据企业ID获取日志
        
        Args:
            corp_id: 企业ID
            limit: 返回记录数量
            
        Returns:
            日志记录列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM request_logs 
                WHERE corp_id = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (corp_id, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        获取统计数据
        
        Args:
            days: 统计天数
            
        Returns:
            统计数据
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 计算截止时间(本地时间)
            cutoff_time = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            
            # 总请求数
            cursor.execute('''
                SELECT COUNT(*) as total_requests
                FROM request_logs
                WHERE timestamp >= ?
            ''', (cutoff_time,))
            total_requests = cursor.fetchone()['total_requests']
            
            # 成功请求数
            cursor.execute('''
                SELECT COUNT(*) as success_requests
                FROM request_logs
                WHERE timestamp >= ?
                AND success = 1
            ''', (cutoff_time,))
            success_requests = cursor.fetchone()['success_requests']
            
            # 失败请求数
            failed_requests = total_requests - success_requests
            
            # 平均响应时间
            cursor.execute('''
                SELECT AVG(response_time) as avg_response_time
                FROM request_logs
                WHERE timestamp >= ?
                AND response_time IS NOT NULL
            ''', (cutoff_time,))
            avg_response_time = cursor.fetchone()['avg_response_time'] or 0
            
            return {
                'total_requests': total_requests,
                'success_requests': success_requests,
                'failed_requests': failed_requests,
                'success_rate': (success_requests / total_requests * 100) if total_requests > 0 else 0,
                'avg_response_time': round(avg_response_time, 2)
            }
    
    def clean_old_logs(self, days: int = 30):
        """
        清理旧日志
        
        Args:
            days: 保留天数
        """
        # 计算截止时间(本地时间)
        cutoff_time = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM request_logs
                WHERE timestamp < ?
            ''', (cutoff_time,))
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count


# 全局数据库实例
_db_instance = None


def init_database(db_path: str = "data/wechat_notice.db") -> DatabaseManager:
    """
    初始化数据库
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        数据库管理器实例
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager(db_path)
    return _db_instance


def log_request(
    method: str,
    path: str,
    client_ip: str,
    **kwargs
) -> int:
    """
    记录请求日志
    
    Args:
        method: 请求方法
        path: 请求路径
        client_ip: 客户端IP
        **kwargs: 其他参数
        
    Returns:
        日志ID
    """
    db = init_database()
    return db.insert_request_log(method, path, client_ip, **kwargs)
