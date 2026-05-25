"""数据库模型与初始化"""

import sqlite3
import os
from config import Config

DB_PATH = Config.DATABASE


def get_db():
    """获取数据库连接（线程安全）"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """初始化所有数据表"""
    conn = get_db()
    cursor = conn.cursor()

    # 1. 语料库表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS corpus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term_zh TEXT NOT NULL,
            category TEXT NOT NULL,          -- 形制/纹样/工艺/礼仪/朝代
            definition TEXT,
            cultural_note TEXT,              -- 文化注释
            tags TEXT,                       -- JSON标签
            translations TEXT,               -- JSON: {"en":"...","ja":"..."}
            status TEXT DEFAULT 'active',    -- active/review/draft
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. 翻译日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS translation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_text TEXT NOT NULL,
            target_lang TEXT NOT NULL,
            translated_text TEXT,
            matched_terms TEXT,              -- 匹配到的术语JSON
            confidence REAL,
            response_time_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. 合规规则库表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compliance_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            region TEXT,
            category TEXT NOT NULL,          -- 文化冒犯/宗教禁忌/政治敏感/文化挪用
            keywords TEXT,                   -- 敏感词JSON数组
            pattern TEXT,                    -- 纹样/符号描述
            risk_level TEXT DEFAULT '高风险',
            reason TEXT NOT NULL,
            suggestion TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. 审核日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT NOT NULL,       -- text/image
            content_hash TEXT,
            target_country TEXT,
            risk_level TEXT,
            matched_rules TEXT,               -- 命中的规则ID JSON
            reason TEXT,
            suggestion TEXT,
            response_time_ms INTEGER,
            auditor TEXT DEFAULT 'system',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 5. 视觉识别日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vision_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_hash TEXT,
            dynasty TEXT,
            format TEXT,
            colors TEXT,                      -- JSON
            patterns TEXT,                    -- JSON
            confidence REAL,
            response_time_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 6. 区域审美库表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aesthetic_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL,
            category TEXT,                    -- 色彩/纹样/风格
            preference TEXT NOT NULL,
            weight REAL DEFAULT 0.5,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 7. 文化知识库表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,           -- 形制/纹样/工艺/礼仪
            title_zh TEXT NOT NULL,
            content_zh TEXT,
            multilingual TEXT,                -- JSON多语内容
            image_url TEXT,
            cultural_analogies TEXT,          -- 跨文化类比JSON
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 8. 推荐日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommend_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_profile TEXT,                -- 用户画像JSON
            visual_tags TEXT,                 -- 视觉标签JSON
            region TEXT,
            recommended_items TEXT,           -- 推荐结果JSON
            click_rate REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 9. 视频审核日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS video_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_hash TEXT,
            frame_count INTEGER,
            flagged_frames TEXT,              -- 标记的帧JSON
            risk_level TEXT,
            reason TEXT,
            response_time_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 10. 用户权限表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'readonly',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 11. 操作日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS operation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            module TEXT NOT NULL,
            detail TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 12. API调用统计表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT NOT NULL,
            method TEXT,
            response_time_ms INTEGER,
            status_code INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 插入默认管理员 - 使用bcrypt哈希
    import secrets
    import hashlib

    # 生成随机强密码
    default_password = secrets.token_urlsafe(16)
    # 使用SHA256作为bcrypt不可用时的备选方案
    # 生产环境建议安装bcrypt: pip install bcrypt
    try:
        import bcrypt

        admin_pw = bcrypt.hashpw(default_password.encode(), bcrypt.gensalt()).decode()
        hash_method = "bcrypt"
    except ImportError:
        # bcrypt不可用时使用SHA256+salt
        salt = secrets.token_hex(16)
        admin_pw = f"sha256${salt}${hashlib.sha256((salt + default_password).encode()).hexdigest()}"
        hash_method = "sha256"

    cursor.execute(
        """
        INSERT OR IGNORE INTO users (username, password_hash, role)
        VALUES ('admin', ?, 'superadmin')
    """,
        (admin_pw,),
    )

    conn.commit()
    conn.close()
    print("[OK] Database initialized:", DB_PATH)
    print(f"[!] Default admin account: admin")
    print(f"[!] Default password: {default_password}")
    print(f"[!] Hash method: {hash_method}")
    print("[!] WARNING: Please login and change the default password immediately!")
    print("[!] WARNING: Delete this account in production environment!")


if __name__ == "__main__":
    init_db()
