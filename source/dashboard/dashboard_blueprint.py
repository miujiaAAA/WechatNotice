"""
仪表板Blueprint模块
"""
from flask import Blueprint, render_template, request, jsonify, session
from ..auth.decorators import login_required_page
from ..database import init_database


def create_dashboard_blueprint():
    """
    创建仪表板Blueprint
    
    Returns:
        Blueprint实例
    """
    dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard', template_folder='templates')
    
    # 初始化数据库
    db = init_database()
    
    @dashboard_bp.route('/')
    @login_required_page
    def index():
        """仪表板首页"""
        return render_template('dashboard/index.html')
    
    @dashboard_bp.route('/logs')
    @login_required_page
    def logs():
        """日志查询页面"""
        return render_template('dashboard/logs.html')
    
    @dashboard_bp.route('/api/logs')
    def api_logs():
        """日志查询API"""
        try:
            # 获取查询参数
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 20, type=int)
            corp_id = request.args.get('corp_id')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            keyword = request.args.get('keyword')
            
            # 分页查询
            offset = (page - 1) * limit
            
            # 构建查询条件
            where_clauses = []
            params = []
            
            if corp_id:
                where_clauses.append("corp_id = ?")
                params.append(corp_id)
            
            if start_date:
                where_clauses.append("timestamp >= ?")
                params.append(start_date)
            
            if end_date:
                where_clauses.append("timestamp <= ?")
                params.append(end_date)
            
            if keyword:
                where_clauses.append("(message LIKE ? OR error_message LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            
            # 构建SQL
            where_sql = ""
            if where_clauses:
                where_sql = "WHERE " + " AND ".join(where_clauses)
            
            # 查询总数
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) as total FROM request_logs {where_sql}", params)
                total = cursor.fetchone()['total']
            
            # 查询数据
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    SELECT * FROM request_logs 
                    {where_sql}
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                ''', params + [limit, offset])
                
                rows = cursor.fetchall()
                logs = [dict(row) for row in rows]
            
            return jsonify({
                "success": True,
                "data": logs,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @dashboard_bp.route('/api/statistics')
    def api_statistics():
        """统计数据API"""
        try:
            days = request.args.get('days', 7, type=int)
            stats = db.get_statistics(days)
            return jsonify({
                "success": True,
                "data": stats
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    return dashboard_bp
