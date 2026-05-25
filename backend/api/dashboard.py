"""数据看板与权限管理API"""

import os
import json
from flask import Blueprint, request, jsonify
from database import get_db
from datetime import datetime, timedelta

dashboard_bp = Blueprint("dashboard", __name__)

# AI配置文件路径
AI_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")


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


# ---- AI配置管理 ----
@dashboard_bp.route("/api/ai-config", methods=["GET"])
def get_ai_config():
    """获取AI配置"""
    config = {
        "provider": os.environ.get("AI_PROVIDER", ""),
        "api_key": "",  # 不返回API密钥
        "api_key_set": bool(os.environ.get("AI_API_KEY", "")),
        "base_url": os.environ.get("AI_BASE_URL", ""),
        "model": os.environ.get("AI_MODEL", ""),
        "enabled": bool(os.environ.get("AI_PROVIDER") and os.environ.get("AI_API_KEY"))
    }

    # 尝试从.env文件读取完整配置
    try:
        if os.path.exists(AI_CONFIG_FILE):
            with open(AI_CONFIG_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("AI_PROVIDER="):
                        config["provider"] = line.split("=", 1)[1]
                    elif line.startswith("AI_API_KEY="):
                        key = line.split("=", 1)[1]
                        config["api_key"] = key[:8] + "****" if len(key) > 8 else "****"
                        config["api_key_set"] = bool(key)
                    elif line.startswith("AI_BASE_URL="):
                        config["base_url"] = line.split("=", 1)[1]
                    elif line.startswith("AI_MODEL="):
                        config["model"] = line.split("=", 1)[1]
    except Exception:
        pass

    return jsonify(config)


@dashboard_bp.route("/api/ai-config", methods=["POST"])
def save_ai_config():
    """保存AI配置到.env文件"""
    data = request.json
    provider = data.get("provider", "")
    api_key = data.get("api_key", "")
    base_url = data.get("base_url", "")
    model = data.get("model", "")

    # 读取现有.env内容
    env_lines = []
    env_path = AI_CONFIG_FILE

    try:
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                env_lines = f.read().split("\n")
    except Exception:
        pass

    # 更新或添加配置项
    updated = {"AI_PROVIDER": False, "AI_API_KEY": False, "AI_BASE_URL": False, "AI_MODEL": False}

    for i, line in enumerate(env_lines):
        if line.strip().startswith("AI_PROVIDER="):
            env_lines[i] = f"AI_PROVIDER={provider}"
            updated["AI_PROVIDER"] = True
        elif line.strip().startswith("AI_API_KEY="):
            if api_key and not api_key.endswith("****"):
                env_lines[i] = f"AI_API_KEY={api_key}"
            updated["AI_API_KEY"] = True
        elif line.strip().startswith("AI_BASE_URL="):
            env_lines[i] = f"AI_BASE_URL={base_url}"
            updated["AI_BASE_URL"] = True
        elif line.strip().startswith("AI_MODEL="):
            env_lines[i] = f"AI_MODEL={model}"
            updated["AI_MODEL"] = True

    # 添加未存在的配置
    if not updated["AI_PROVIDER"]:
        env_lines.append(f"AI_PROVIDER={provider}")
    if not updated["AI_API_KEY"] and api_key and not api_key.endswith("****"):
        env_lines.append(f"AI_API_KEY={api_key}")
    if not updated["AI_BASE_URL"] and base_url:
        env_lines.append(f"AI_BASE_URL={base_url}")
    if not updated["AI_MODEL"] and model:
        env_lines.append(f"AI_MODEL={model}")

    # 写入文件
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("\n".join(env_lines))

        # 更新当前进程环境变量
        os.environ["AI_PROVIDER"] = provider
        if api_key and not api_key.endswith("****"):
            os.environ["AI_API_KEY"] = api_key
        if base_url:
            os.environ["AI_BASE_URL"] = base_url
        if model:
            os.environ["AI_MODEL"] = model

        # 重置AI服务单例
        try:
            from services.ai.factory import AIFactory
            AIFactory.reset()
        except Exception:
            pass

        return jsonify({"message": "AI配置已保存，重启服务后生效", "restart_required": True})
    except Exception as e:
        return jsonify({"error": f"保存失败: {str(e)}"}), 500


@dashboard_bp.route("/api/ai-config/test", methods=["POST"])
def test_ai_config():
    """测试AI连接"""
    try:
        from services.ai_service import get_ai_service
        ai = get_ai_service()

        if not ai or not ai.enabled:
            return jsonify({"success": False, "message": "AI服务未配置或未启用"})

        # 尝试简单翻译测试
        result = ai.translate("测试", "en")
        if result:
            return jsonify({
                "success": True,
                "message": f"AI服务正常 ({ai.adapter.get_provider_name() if ai.adapter else 'unknown'})",
                "model": ai.adapter.get_model_name() if ai.adapter else "unknown"
            })
        else:
            return jsonify({"success": False, "message": "AI服务返回空结果"})

    except Exception as e:
        return jsonify({"success": False, "message": f"连接失败: {str(e)}"})
