"""数据看板与权限管理API"""

from flask import Blueprint, request, jsonify
from database import get_db
from datetime import datetime, timedelta

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/dashboard/overview", methods=["GET"])
def overview():
    """全模块数据概览"""
    db = get_db()
    stats = {}
    
    # 语料库
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM corpus WHERE status='active'")
    stats["corpus_count"] = cursor.fetchone()["cnt"]
    
    # 规则库
    cursor.execute("SELECT COUNT(*) as cnt FROM compliance_rules WHERE status='active'")
    stats["rules_count"] = cursor.fetchone()["cnt"]
    
    # 翻译量（近30天）
    cursor.execute("""
        SELECT COUNT(*) as cnt, AVG(confidence) as avg_conf
        FROM translation_log WHERE created_at > datetime('now', '-30 days')
    """)
    row = cursor.fetchone()
    stats["monthly_translations"] = row["cnt"]
    stats["avg_translation_confidence"] = round(row["avg_conf"] or 0, 2)
    
    # 审核统计（近30天）
    cursor.execute("""
        SELECT risk_level, COUNT(*) as cnt FROM audit_log
        WHERE created_at > datetime('now', '-30 days')
        GROUP BY risk_level
    """)
    risk_stats = {r["risk_level"]: r["cnt"] for r in cursor.fetchall()}
    total = sum(risk_stats.values())
    stats["monthly_audits"] = total
    stats["pass_rate"] = round(risk_stats.get("合规", 0) / max(1, total), 2)
    stats["high_risk_rate"] = round(risk_stats.get("高风险", 0) / max(1, total), 2)
    
    # 视觉识别量
    cursor.execute("SELECT COUNT(*) as cnt FROM vision_log")
    stats["vision_analyses"] = cursor.fetchone()["cnt"]
    
    # 知识库
    cursor.execute("SELECT COUNT(*) as cnt FROM knowledge_base")
    stats["knowledge_entries"] = cursor.fetchone()["cnt"]
    
    return jsonify(stats)


@dashboard_bp.route("/api/dashboard/daily", methods=["GET"])
def daily_stats():
    """每日数据趋势"""
    db = get_db()
    
    cursor = db.cursor()
    cursor.execute("""
        SELECT date(created_at) as day,
               COUNT(*) as translations,
               AVG(confidence) as avg_conf
        FROM translation_log
        WHERE created_at > datetime('now', '-30 days')
        GROUP BY date(created_at)
        ORDER BY day
    """)
    translations = [dict(r) for r in cursor.fetchall()]
    
    cursor.execute("""
        SELECT date(created_at) as day,
               SUM(CASE WHEN risk_level='合规' THEN 1 ELSE 0 END) as passed,
               SUM(CASE WHEN risk_level='高风险' THEN 1 ELSE 0 END) as high_risk
        FROM audit_log
        WHERE created_at > datetime('now', '-30 days')
        GROUP BY date(created_at)
        ORDER BY day
    """)
    audits = [dict(r) for r in cursor.fetchall()]
    
    return jsonify({"translations": translations, "audits": audits})


# ---- 权限管理 ----
@dashboard_bp.route("/api/users", methods=["GET"])
def list_users():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, username, role, status, created_at FROM users ORDER BY id")
    return jsonify([dict(r) for r in cursor.fetchall()])


@dashboard_bp.route("/api/users", methods=["POST"])
def create_user():
    data = request.json
    required = ["username", "password", "role"]
    for f in required:
        if f not in data:
            return jsonify({"error": f"缺少字段: {f}"}), 400
    
    import hashlib
    pw_hash = hashlib.sha256(data["password"].encode()).hexdigest()
    db = get_db()
    try:
        db.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                   (data["username"], pw_hash, data["role"]))
        db.commit()
        return jsonify({"message": "用户创建成功"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@dashboard_bp.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id=? AND role!='superadmin'", (user_id,))
    db.commit()
    return jsonify({"message": "用户已删除"})
