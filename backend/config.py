"""CCAE引擎配置文件"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    # 从环境变量读取SECRET_KEY，开发环境提供默认值
    SECRET_KEY = os.environ.get("CCAE_SECRET_KEY", "dev-key-change-in-production")
    # 如果生产环境未设置SECRET_KEY，抛出错误提示
    if SECRET_KEY == "dev-key-change-in-production":
        import warnings

        warnings.warn(
            "⚠️  警告: 使用开发环境默认SECRET_KEY！生产环境请设置环境变量 CCAE_SECRET_KEY",
            UserWarning,
        )
    DATABASE = os.path.join(BASE_DIR, "data", "ccae.db")

    # 支持语种
    LANGUAGES = ["en", "ja", "ko", "es", "fr", "ar"]
    LANGUAGE_NAMES = {
        "en": "英语",
        "ja": "日语",
        "ko": "韩语",
        "es": "西班牙语",
        "fr": "法语",
        "ar": "阿拉伯语",
    }

    # 区域库
    REGIONS = ["北美", "欧洲", "日韩", "东南亚", "中东", "拉美"]

    # 风险等级
    RISK_LEVELS = ["合规", "低风险", "高风险"]

    # 文化禁忌类别
    TABOO_CATEGORIES = ["文化冒犯", "宗教禁忌", "政治敏感", "文化挪用"]

    # 汉服朝代
    DYNASTIES = ["商周", "秦汉", "魏晋", "唐", "宋", "明", "清", "民国", "现代改良"]

    # 汉服形制
    FORMATS = [
        "深衣",
        "袍服",
        "襦裙",
        "袄裙",
        "褙子",
        "马面裙",
        "披风",
        "直裰",
        "道袍",
        "圆领袍",
    ]

    # 用户角色
    ROLES = ["superadmin", "operator", "auditor", "readonly"]

    # API性能指标
    API_TIMEOUT = 3  # 秒
    TRANSLATE_TARGET_ACCURACY = 0.95
    TEXT_AUDIT_TARGET_ACCURACY = 0.98
    IMAGE_AUDIT_TARGET_ACCURACY = 0.95
    VISION_TARGET_ACCURACY = 0.90
    RECOMMEND_TARGET_ACCURACY = 0.35
