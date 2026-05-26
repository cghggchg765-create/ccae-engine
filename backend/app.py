"""CCAE 跨文化适配引擎 (Cross-Cultural Adaptation Engine) - 主应用入口"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from database import init_db, get_db
from config import Config
import os, json, csv, hashlib

app = Flask(__name__, static_folder="../frontend", static_url_path="")
app.config["SECRET_KEY"] = Config.SECRET_KEY

# 从环境变量读取CORS来源，生产环境必须配置
cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5000").split(",")
CORS(app, origins=cors_origins)

# 注册API蓝图
from api.translate import translate_bp
from api.compliance import compliance_bp
from api.vision import vision_bp
from api.knowledge import knowledge_bp
from api.dashboard import dashboard_bp
from api.ai_providers import providers_bp

app.register_blueprint(translate_bp)
app.register_blueprint(compliance_bp)
app.register_blueprint(vision_bp)
app.register_blueprint(knowledge_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(providers_bp)


@app.route("/")
def index():
    """管理后台首页"""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api")
def api_info():
    """API信息"""
    return jsonify(
        {
            "name": "CCAE 跨文化适配引擎 (Cross-Cultural Adaptation Engine)",
            "version": "1.2.0",
            "priority_p0": ["翻译API", "合规审核API"],
            "priority_p1": ["视觉识别API", "知识库API", "AI供应商管理API"],
            "priority_p2": ["推荐API", "数据看板API", "权限管理API"],
            "endpoints": {
                "翻译": ["POST /api/translate", "GET/POST /api/corpus"],
                "合规": [
                    "POST /api/compliance/audit/text",
                    "POST /api/compliance/audit/image",
                    "GET/POST /api/compliance/rules",
                ],
                "视觉": [
                    "POST /api/vision/analyze",
                    "POST /api/vision/aesthetic-match",
                ],
                "知识库": [
                    "GET/POST /api/knowledge",
                    "POST /api/knowledge/generate-copy",
                ],
                "AI供应商": [
                    "GET /api/ai/providers",
                    "POST /api/ai/providers",
                    "GET /api/ai/providers/<id>",
                    "PUT /api/ai/providers/<id>",
                    "DELETE /api/ai/providers/<id>",
                    "POST /api/ai/providers/<id>/activate",
                    "POST /api/ai/providers/<id>/test",
                    "GET /api/ai/current",
                ],
                "推荐": ["POST /api/recommend"],
                "看板": ["GET /api/dashboard/overview"],
                "权限": ["GET/POST /api/users"],
            },
        }
    )


def seed_initial_data():
    """初始化种子数据"""
    db = get_db()
    cursor = db.cursor()

    # 检查是否已初始化
    cursor.execute("SELECT COUNT(*) as cnt FROM corpus")
    if cursor.fetchone()["cnt"] > 0:
        return

    print("[*] Seeding initial data...")

    # ---- 1. 汉服专业语料库种子数据 (22条) ----
    T = lambda en="", ja="", ko="", es="", fr="", ar="": json.dumps(
        {"en": en, "ja": ja, "ko": ko, "es": es, "fr": fr, "ar": ar}, ensure_ascii=False
    )
    corpus_seed = [
        # --- 形制类 (10条) ---
        (
            "马面裙",
            "形制",
            "明代流行的裙装形制，前后有平幅裙门，两侧打褶",
            "最具辨识度的汉服单品，非'马面'之意，源于裙门形似马面城墙垛口",
            json.dumps(["明制", "裙装", "标志性"], ensure_ascii=False),
            T(
                "Mamian Qun (Horse-Face Skirt)",
                "馬面裙（ばめんぐん）",
                "마면군",
                "Falda Mamian",
                "Jupe Mamian",
                "تنورة ماميان",
            ),
        ),
        (
            "云肩",
            "形制",
            "披在肩部的装饰性衣饰，多为圆形或云朵形",
            "云肩象征吉祥如意，唐代已有雏形，明清盛行",
            json.dumps(["肩饰", "装饰", "明制"], ensure_ascii=False),
            T(
                "Cloud Collar (Yunjian)",
                "雲肩（うんけん）",
                "운견",
                "Cuello Nube",
                "Col Nuage",
                "ياقة السحابة",
            ),
        ),
        (
            "补服",
            "形制",
            "明清官员官服，前胸后背缀有补子表示品级",
            "补子图案严格按品级：文官绣禽、武官绣兽",
            json.dumps(["官服", "明清"], ensure_ascii=False),
            T(
                "Mandarin Square Robe",
                "補服（ほふく）",
                "보복",
                "Toga Mandarina",
                "Robe Mandarine",
                "رداء الماندرين",
            ),
        ),
        (
            "交领",
            "形制",
            "汉服基本领型，左右衣襟交叉于胸前",
            "交领右衽是汉服核心特征，区别于少数民族左衽",
            json.dumps(["领型", "基础", "通用"], ensure_ascii=False),
            T(
                "Cross-Collar (Jiaoling)",
                "交領（こうりょう）",
                "교령",
                "Cuello Cruzado",
                "Col Croisé",
                "ياقة متقاطعة",
            ),
        ),
        (
            "齐胸襦裙",
            "形制",
            "唐代流行的高腰裙装，裙腰系于胸上",
            "唐代女性典型装束，搭配大袖衫或半臂，展现盛唐气象",
            json.dumps(["唐制", "女装", "高腰"], ensure_ascii=False),
            T(
                "High-Waist Ruqun",
                "斉胸襦裙（せいきょうじゅくん）",
                "제흉유군",
                "Falda Alto Pecho",
                "Jupe Haute Poitrine",
                "تنورة عالية الصدر",
            ),
        ),
        (
            "褙子",
            "形制",
            "宋代流行的直领对襟长外套，两侧开衩",
            "宋代女子常服，简约优雅，体现宋人'清雅'审美",
            json.dumps(["宋制", "外套", "女装"], ensure_ascii=False),
            T(
                "Beizi (Side-Slit Robe)",
                "褙子（はいし）",
                "배자",
                "Chaqueta Beizi",
                "Veste Beizi",
                "سترة بيزي",
            ),
        ),
        (
            "直裰",
            "形制",
            "明代男子日常服装，交领长袍，两侧开衩",
            "直裰为明代士人常服，儒雅简约",
            json.dumps(["男装", "明制", "士人"], ensure_ascii=False),
            T(
                "Straight Robe (Zhiduo)",
                "直綴（じきてつ）",
                "직철",
                "Túnica Recta",
                "Robe Droite",
                "رداء مستقيم",
            ),
        ),
        (
            "圆领袍",
            "形制",
            "圆领窄袖长袍，隋唐至明代的常服/官服",
            "唐代圆领袍影响深远，日本狩衣即源于此",
            json.dumps(["通用", "官服", "隋唐"], ensure_ascii=False),
            T(
                "Round-Collar Robe",
                "円領袍（えんりょうほう）",
                "원령포",
                "Túnica Cuello Redondo",
                "Robe Col Rond",
                "رداء بياقة مستديرة",
            ),
        ),
        (
            "袄裙",
            "形制",
            "明代女子上袄下裙的搭配，袄为短上衣",
            "袄裙为明制汉服代表性搭配，袄有交领/竖领之分",
            json.dumps(["明制", "女装", "套装"], ensure_ascii=False),
            T(
                "Aoqun (Jacket & Skirt)",
                "襖裙（おうくん）",
                "오군",
                "Conjunto Aoqun",
                "Ensemble Aoqun",
                "طقم أوكون",
            ),
        ),
        (
            "披风",
            "形制",
            "明代男女皆可穿着的直领对襟外套",
            "披风形似褙子但更宽大，为明代常见外搭",
            json.dumps(["明制", "外套", "通用"], ensure_ascii=False),
            T(
                "Pifeng Cape",
                "披風（ひふう）",
                "피봉",
                "Capa Pifeng",
                "Cape Pifeng",
                "عباءة بيفنغ",
            ),
        ),
        # --- 纹样类 (6条) ---
        (
            "云纹",
            "纹样",
            "象征高升和如意的传统纹样，形似祥云",
            "云纹起源商周青铜器，汉代广泛用于织物",
            json.dumps(["吉祥纹样", "常用", "基础"], ensure_ascii=False),
            T(
                "Cloud Pattern",
                "雲紋（うんもん）",
                "운문",
                "Patrón de Nubes",
                "Motif Nuage",
                "نمط السحابة",
            ),
        ),
        (
            "缠枝莲",
            "纹样",
            "莲花与枝蔓交织的连续纹样，寓意生生不息",
            "受佛教影响，莲花为圣洁象征，广泛应用于丝绸",
            json.dumps(["吉祥纹样", "佛教", "连续"], ensure_ascii=False),
            T(
                "Lotus Scroll Pattern",
                "蓮華唐草文（れんげからくさもん）",
                "연화당초문",
                "Patrón Loto Enredadera",
                "Motif Lotus Entrelacé",
                "نمط اللوتس المتشابك",
            ),
        ),
        (
            "海水江崖",
            "纹样",
            "波涛与山崖组合的纹样，象征江山永固",
            "明清官服常用，寓意'福山寿海'、'江山一统'",
            json.dumps(["官服纹样", "明清", "吉祥"], ensure_ascii=False),
            T(
                "Wave & Cliff Pattern",
                "海水江崖文（かいすいこうがいもん）",
                "해수강애문",
                "Patrón Olas y Acantilados",
                "Motif Vagues et Falaises",
                "نمط الأمواج والمنحدرات",
            ),
        ),
        (
            "龙凤纹",
            "纹样",
            "龙与凤组合的尊贵纹样，象征帝王与皇后",
            "龙纹在明清仅限皇室使用，民间使用蟒纹替代",
            json.dumps(["尊贵", "皇家", "明清"], ensure_ascii=False),
            T(
                "Dragon & Phoenix Pattern",
                "竜鳳文（りゅうほうもん）",
                "용봉문",
                "Patrón Dragón y Fénix",
                "Motif Dragon et Phénix",
                "نمط التنين والعنقاء",
            ),
        ),
        (
            "牡丹纹",
            "纹样",
            "以牡丹花为题材的纹样，象征富贵荣华",
            "牡丹为'花中之王'，唐代起即受追捧，宋元明清广泛使用",
            json.dumps(["花卉", "富贵", "吉祥"], ensure_ascii=False),
            T(
                "Peony Pattern",
                "牡丹文（ぼたんもん）",
                "모란문",
                "Patrón de Peonía",
                "Motif Pivoine",
                "نمط الفاوانيا",
            ),
        ),
        (
            "八宝纹",
            "纹样",
            "道教/佛教八种法宝组合纹样，寓意吉祥",
            "常见有宝伞、金鱼、宝瓶、莲花、法螺、吉祥结、宝幢、法轮",
            json.dumps(["宗教", "吉祥", "组合"], ensure_ascii=False),
            T(
                "Eight Treasures Pattern",
                "八宝文（はっぽうもん）",
                "팔보문",
                "Patrón Ocho Tesoros",
                "Motif Huit Trésors",
                "نمط الكنوز الثمانية",
            ),
        ),
        # --- 工艺类 (4条) ---
        (
            "缂丝",
            "工艺",
            "通经断纬的高级丝织工艺，可织出精细图案",
            "缂丝宋代达顶峰，'一寸缂丝一寸金'，为非遗",
            json.dumps(["非遗", "丝织", "高级"], ensure_ascii=False),
            T(
                "Kesi Silk Tapestry",
                "綴織（けし）",
                "극사",
                "Tapiz Kesi",
                "Tapisserie Kesi",
                "نسيج كيسي",
            ),
        ),
        (
            "刺绣",
            "工艺",
            "用针线在织物上绣制图案的传统工艺",
            "四大名绣：苏绣、湘绣、粤绣、蜀绣，各有特色",
            json.dumps(["非遗", "手工", "装饰"], ensure_ascii=False),
            T("Embroidery", "刺繍（ししゅう）", "자수", "Bordado", "Broderie", "تطريز"),
        ),
        (
            "织锦",
            "工艺",
            "用彩色丝线织出花纹的高级丝织品",
            "南京云锦、成都蜀锦、苏州宋锦并称三大名锦",
            json.dumps(["丝织", "高级", "多彩"], ensure_ascii=False),
            T("Brocade", "錦（にしき）", "직금", "Brocado", "Brocard", "ديباج"),
        ),
        (
            "蜡染",
            "工艺",
            "用蜡防染的印染工艺，图案独特",
            "苗族蜡染为国家级非遗，蓝白二色为经典配色",
            json.dumps(["非遗", "印染", "少数民族"], ensure_ascii=False),
            T("Batik", "蝋纈（ろうけつ）", "납염", "Batik", "Batik", "باتيك"),
        ),
        # --- 礼仪类 (2条) ---
        (
            "右衽",
            "礼仪",
            "衣襟向右掩的穿着方式，为汉服核心特征",
            "右衽为华夏衣冠标志，孔子赞管仲'微管仲，吾其被发左衽矣'",
            json.dumps(["基础", "标志性", "礼仪"], ensure_ascii=False),
            T(
                "Right Lapel (Youren)",
                "右衽（うじん）",
                "우임",
                "Solapa Derecha",
                "Revers Droit",
                "طية يمنى",
            ),
        ),
        (
            "冠礼",
            "礼仪",
            "古代汉族男子成年礼，加冠以示成人",
            "冠礼为'礼之始也'，周代已形成完整仪式，为儒家六礼之首",
            json.dumps(["成年礼", "礼仪", "周礼"], ensure_ascii=False),
            T(
                "Capping Ceremony (Guanli)",
                "冠礼（かんれい）",
                "관례",
                "Ceremonia de Coronación",
                "Cérémonie du Chapeau",
                "مراسم التتويج",
            ),
        ),
    ]

    for term_zh, category, definition, note, tags, trans in corpus_seed:
        cursor.execute(
            """
            INSERT INTO corpus (term_zh, category, definition, cultural_note, tags, translations)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (term_zh, category, definition, note, tags, trans),
        )

    # ---- 2. 合规规则库种子数据 (18条) ----
    rules_seed = [
        # 原有6条
        (
            "沙特阿拉伯",
            "中东",
            "宗教禁忌",
            json.dumps(
                ["猪", "猪肉", "猪皮", "酒精", "酒类", "十字架", "佛像"],
                ensure_ascii=False,
            ),
            None,
            "高风险",
            "含宗教禁忌元素，可能引发穆斯林消费者强烈反感",
            "移除与伊斯兰教义冲突的元素，替换为几何纹样或植物纹样",
        ),
        (
            "印度",
            "南亚",
            "宗教禁忌",
            json.dumps(["牛皮", "牛肉", "牛图案", "印度神像"], ensure_ascii=False),
            None,
            "高风险",
            "牛在印度教中为圣物，牛皮制品或牛图案可能造成严重冒犯",
            "避免使用牛皮材质和相关图案，替换为棉麻或丝绸材质",
        ),
        (
            "日本",
            "东亚",
            "文化冒犯",
            json.dumps(["龙纹过于张扬", "菊花徽章"], ensure_ascii=False),
            "菊花为日本皇室纹章，误用可能被视为不敬",
            "低风险",
            "注意日本皇室纹章使用规范，避免将特定纹样用于商业",
            "简化龙纹为祥云纹，避免使用菊花徽章作为装饰",
        ),
        (
            "美国",
            "北美",
            "文化挪用",
            json.dumps(["印第安羽饰", "图腾柱", "war bonnet"], ensure_ascii=False),
            "未经授权使用原住民文化符号属于文化挪用",
            "高风险",
            "原住民文化符号受法律保护，商业使用可能面临法律和文化风险",
            "与Native American tribes合作获得授权，或使用中国非遗元素替代",
        ),
        (
            "德国",
            "欧洲",
            "政治敏感",
            json.dumps(["纳粹", "万字符", "SS标志", "希特勒"], ensure_ascii=False),
            "卍字纹（左旋）为佛教吉祥纹样，需与纳粹标志严格区分",
            "高风险",
            "万字符在德国/欧洲语境中高度敏感，必须严格区分或避免使用",
            "如使用佛教卍字纹，必须在注释中明确标注'佛教吉祥纹样，左旋'",
        ),
        (
            "全球",
            "全球",
            "文化冒犯",
            json.dumps(["辱华", "眯眯眼", "Chinese virus", "支那"], ensure_ascii=False),
            None,
            "高风险",
            "含对华裔群体的歧视性表述",
            "坚决杜绝任何歧视性内容，使用尊重、平等的表达方式",
        ),
        # 新增12条
        (
            "阿联酋",
            "中东",
            "宗教禁忌",
            json.dumps(
                ["裸体", "比基尼", "短裙", "酒类广告", "猪", "狗"], ensure_ascii=False
            ),
            "伊斯兰教对裸露和酒精有严格限制，女性着装需遮蔽",
            "高风险",
            "阿联酋保守伊斯兰文化对裸露内容和酒精元素零容忍",
            "确保服装遮蔽度足够，避免酒类与裸露元素",
        ),
        (
            "韩国",
            "东亚",
            "文化冒犯",
            json.dumps(
                ["韩服", "kimchi", "泡菜起源中国", "端午节"], ensure_ascii=False
            ),
            "中韩文化归属争议敏感，涉及韩服起源等话题需格外谨慎",
            "中风险",
            "韩国民众对文化起源问题高度敏感，可能引发大规模抵制",
            "避免直接声称韩服/泡菜源于中国，强调东亚文化圈交流互鉴",
        ),
        (
            "法国",
            "欧洲",
            "文化冒犯",
            json.dumps(["贬低法语", "贬低法国文化", "辱法"], ensure_ascii=False),
            None,
            "低风险",
            "法国消费者对自身文化保护意识强",
            "尊重法国文化，使用正面表达，确保法语翻译地道",
        ),
        (
            "俄罗斯",
            "东欧",
            "政治敏感",
            json.dumps(
                ["苏联", "共产主义", "乌克兰旗帜", "克里米亚"], ensure_ascii=False
            ),
            None,
            "高风险",
            "涉及前苏联及近现代政治符号在俄乌冲突背景下高度敏感",
            "避免任何政治符号，专注于服饰美学本身",
        ),
        (
            "巴西",
            "拉美",
            "宗教禁忌",
            json.dumps(
                ["耶稣受难", "圣母像过度暴露", "十字架亵渎"], ensure_ascii=False
            ),
            "天主教国家，宗教符号需尊重使用",
            "中风险",
            "巴西为天主教大国，宗教符号不当使用可能冒犯信徒",
            "谨慎使用十字架等基督宗教符号，除非为正面展示",
        ),
        (
            "泰国",
            "东南亚",
            "文化冒犯",
            json.dumps(["佛像亵渎", "王室不敬", "佛头"], ensure_ascii=False),
            "泰国法律严格保护王室和佛教尊严",
            "高风险",
            "亵渎王室（大不敬罪）或佛教符号在泰国属严重违法行为",
            "绝对避免任何可能被视为不敬王室或佛教的内容",
        ),
        (
            "马来西亚",
            "东南亚",
            "宗教禁忌",
            json.dumps(["猪", "狗", "酒精", "裸露", "LGBT"], ensure_ascii=False),
            "伊斯兰教为国教，同时存在多元族群",
            "高风险",
            "马来西亚穆斯林人口占多数，伊斯兰禁忌需严格遵守",
            "去除猪/酒/LGBT等敏感元素，使用马来西亚本地化文化符号",
        ),
        (
            "印度尼西亚",
            "东南亚",
            "宗教禁忌",
            json.dumps(["猪", "色情", "裸体", "亵渎宗教"], ensure_ascii=False),
            "全球最大穆斯林人口国家",
            "高风险",
            "印尼穆斯林群体对猪/裸露/宗教亵渎内容高度敏感",
            "使用植物纹样替代，保持内容庄重保守",
        ),
        (
            "土耳其",
            "中东",
            "文化冒犯",
            json.dumps(["库尔德", "亚美尼亚", "奥斯曼贬低"], ensure_ascii=False),
            None,
            "中风险",
            "土耳其民族自豪感强，涉及少数民族话题需谨慎",
            "避免库尔德/亚美尼亚相关政治暗示，正面展示土耳其-中国丝绸文化交流",
        ),
        (
            "意大利",
            "欧洲",
            "文化冒犯",
            json.dumps(
                ["意大利面诋毁", "披萨诋毁", "黑手党刻板印象"], ensure_ascii=False
            ),
            None,
            "低风险",
            "意大利人对其美食文化极为自豪，刻板印象可能引发反感",
            "使用尊重意大利文化的表达，可类比丝绸与意大利时尚的关联",
        ),
        (
            "墨西哥",
            "拉美",
            "文化挪用",
            json.dumps(["亡灵节", "玛雅历", "阿兹特克符号"], ensure_ascii=False),
            "亡灵节等为墨西哥重要文化遗产，未经授权的商业使用属文化挪用",
            "中风险",
            "墨西哥原住民文化符号受国际关注，商业使用需获得文化认可",
            "优先使用中国非遗元素，如需引用墨西哥文化应注明来源并寻求合作",
        ),
        (
            "澳大利亚",
            "大洋洲",
            "文化挪用",
            json.dumps(["原住民点画", "didgeridoo", "原住民旗帜"], ensure_ascii=False),
            "澳大利亚原住民文化符号受法律和社区保护",
            "高风险",
            "未经土著社区许可使用其文化符号属于严重文化挪用",
            "与土著社区合作获授权，或使用通用的自然元素纹样替代",
        ),
    ]

    for country, region, category, keywords, pattern, risk, reason, sugg in rules_seed:
        cursor.execute(
            """
            INSERT INTO compliance_rules (country, region, category, keywords, pattern, risk_level, reason, suggestion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (country, region, category, keywords, pattern, risk, reason, sugg),
        )

    # ---- 3. 区域审美偏好种子数据 (18条) ----
    prefs_seed = [
        (
            "北美",
            "色彩",
            "红色（需搭配中性色）",
            0.7,
            "纯红色过于浓烈，搭配黑白灰更受欢迎",
        ),
        ("北美", "色彩", "金色（用作点缀）", 0.6, ""),
        ("北美", "色彩", "大地色系", 0.7, "驼色、米色、橄榄绿在北美市场接受度高"),
        ("北美", "风格", "极简东方风", 0.8, "强调线条和轮廓"),
        ("欧洲", "色彩", "深蓝+金色", 0.7, "皇家蓝调受欧洲市场青睐"),
        ("欧洲", "色彩", "莫兰迪色系", 0.6, "低饱和灰调在欧洲高级时装界流行"),
        ("欧洲", "纹样", "花卉纹（简洁版）", 0.7, ""),
        ("欧洲", "风格", "复古宫廷风", 0.6, "可类比维多利亚时期服饰"),
        ("日韩", "色彩", "淡雅粉彩", 0.8, "低饱和度的粉色、淡蓝、浅紫"),
        ("日韩", "色彩", "马卡龙色系", 0.7, "年轻女性群体偏爱"),
        ("日韩", "风格", "清雅简约", 0.9, "强调'侘寂'美学"),
        ("东南亚", "色彩", "鲜艳亮色", 0.8, "高饱和度在热带市场更受欢迎"),
        ("东南亚", "纹样", "热带花卉纹", 0.7, ""),
        ("中东", "色彩", "墨绿+金色", 0.7, "低调奢华色系"),
        ("中东", "色彩", "珍珠白+香槟金", 0.6, "婚礼及庆典服饰偏好"),
        ("中东", "风格", "端庄典雅", 0.9, "注重遮蔽度与优雅感"),
        ("拉美", "色彩", "浓郁暖色", 0.8, "大红、橙黄、紫色热情奔放"),
        ("拉美", "风格", "华丽繁复", 0.7, "偏好刺绣密集、装饰感强的设计"),
    ]

    for region, category, preference, weight, notes in prefs_seed:
        cursor.execute(
            """
            INSERT INTO aesthetic_preferences (region, category, preference, weight, notes)
            VALUES (?, ?, ?, ?, ?)
        """,
            (region, category, preference, weight, notes),
        )

    # ---- 4. 知识库种子数据 (10条) ----
    kb_seed = [
        (
            "形制",
            "马面裙的历史与文化",
            "马面裙是明代最具代表性的女裙形制之一，因裙门形似城墙马面而得名。前后各有平幅裙门，两侧打褶，行走时裙褶摆动，极具韵律感。马面裙自明代流行至民国，近年随汉服复兴再次成为热门单品。其设计兼顾实用与美观，褶裥工艺可使裙摆自然展开如扇形。",
            json.dumps(
                {
                    "en": "The History of Mamian Qun",
                    "ja": "馬面裙の歴史",
                    "ko": "마면군의 역사",
                },
                ensure_ascii=False,
            ),
            None,
            json.dumps(
                {
                    "北美": "如维多利亚时期裙撑的东方版本",
                    "日韩": "与韩服赤古里裙的东方共鸣",
                    "欧洲": "东方版的宫廷大裙摆",
                },
                ensure_ascii=False,
            ),
        ),
        (
            "工艺",
            "缂丝技艺 — 一寸缂丝一寸金",
            "缂丝是中国传统丝绸艺术品中的精华，采用'通经断纬'技法织就。与普通织锦不同，缂丝可以在织造过程中自由变换纬线颜色，从而织出精细的图案和文字，效果如雕琢缕刻。宋代缂丝达到艺术顶峰，南宋朱克柔的缂丝作品被视为国宝。2009年缂丝入选联合国人类非物质文化遗产代表作名录。",
            json.dumps(
                {
                    "en": "Kesi: The Pinnacle of Silk Art",
                    "ja": "綴織—究極の絹芸術",
                    "ko": "극사—비단 예술의 정점",
                },
                ensure_ascii=False,
            ),
            None,
            json.dumps(
                {
                    "欧洲": "堪比欧洲哥白林挂毯工艺",
                    "日韩": "与西阵织并称东亚丝织双璧",
                    "中东": "如波斯地毯般匠心独运",
                },
                ensure_ascii=False,
            ),
        ),
        (
            "纹样",
            "云纹的千年演变",
            "云纹是中国最古老的装饰纹样之一，起源于商周青铜器上的云雷纹，汉代开始广泛用于丝织品。云纹寓意'高升'和'如意'，不同朝代呈现不同风格：汉代云气纹流畅飘逸，唐代朵云纹饱满华丽，宋代如意云纹清雅含蓄，明清团云纹规整繁复。在汉服设计中，云纹是使用频率最高的吉祥纹样。",
            json.dumps(
                {
                    "en": "The Evolution of Cloud Patterns",
                    "ja": "雲紋の千年の歩み",
                    "ko": "운문의 천년 변천",
                },
                ensure_ascii=False,
            ),
            None,
            json.dumps(
                {
                    "欧洲": "如巴洛克卷草纹般华丽",
                    "北美": "东方极简主义的纹样源头",
                    "东南亚": "与蜡染云纹异曲同工",
                },
                ensure_ascii=False,
            ),
        ),
        (
            "礼仪",
            "汉服右衽的文化密码",
            "右衽（衣襟向右掩）是汉服区别于其他民族服饰的核心特征之一。孔子在《论语》中赞管仲曰'微管仲，吾其被发左衽矣'，将右衽视为华夏文明的标志。中国古代以右为尊，右衽不仅是穿着方式，更承载着'以右为尊、以中为正'的文化哲学。在全球化传播中，理解右衽的文化内涵有助于准确传达汉服的文化价值。",
            json.dumps(
                {
                    "en": "The Cultural Code of Right Lapel",
                    "ja": "右衽の文化的暗号",
                    "ko": "우임의 문화적 암호",
                },
                ensure_ascii=False,
            ),
            None,
            json.dumps(
                {
                    "欧洲": "如西装左襟在上般的着装礼仪",
                    "日韩": "与和服左前相同的东亚衣冠传统",
                    "中东": "如阿拉伯长袍右掩般的文化身份",
                },
                ensure_ascii=False,
            ),
        ),
        (
            "形制",
            "齐胸襦裙与盛唐气象",
            "齐胸襦裙是唐代女性最具代表性的装束之一，裙腰高系至胸部以上，搭配短襦或大袖衫，展现盛唐时期的开放与自信。唐代丝绸之路繁荣，胡风影响显著，使得唐代女装呈现出色彩艳丽、款式多样的特点。齐胸襦裙在当代汉服复兴中极受欢迎，是展现大唐风华的首选形制。",
            json.dumps(
                {
                    "en": "High-Waist Ruqun and Tang Splendor",
                    "ja": "斉胸襦裙と盛唐の気象",
                    "ko": "제흉유군과 성당의 기상",
                },
                ensure_ascii=False,
            ),
            None,
            json.dumps(
                {
                    "欧洲": "如帝政风格高腰裙般的优雅",
                    "北美": "堪比1920年代Flapper Dress的文化解放",
                    "中东": "如卡夫坦长袍般的飘逸感",
                },
                ensure_ascii=False,
            ),
        ),
        (
            "纹样",
            "龙凤纹的尊贵象征",
            "龙纹与凤纹是中国最具代表性的尊贵纹样组合。龙象征帝王权威与阳刚之气，凤象征皇后美德与阴柔之美。明清时期龙纹仅限于皇室使用，五爪为龙、四爪为蟒，民间只能使用蟒纹。在当代汉服设计中，龙凤纹的应用需注意文化语境的适度转化，既保留其尊贵内涵，又符合现代审美。",
            json.dumps(
                {
                    "en": "Dragon and Phoenix: Symbols of Nobility",
                    "ja": "竜鳳文の尊貴なる象徴",
                    "ko": "용봉문의 존귀한 상징",
                },
                ensure_ascii=False,
            ),
            None,
            json.dumps(
                {
                    "欧洲": "如皇室纹章般的身份象征",
                    "日韩": "与日本菊花纹章同为皇室专属",
                    "中东": "如阿拉伯书法艺术般的神圣感",
                },
                ensure_ascii=False,
            ),
        ),
        (
            "工艺",
            "四大名绣 — 苏湘粤蜀",
            "中国刺绣历史悠久，苏绣、湘绣、粤绣、蜀绣并称四大名绣。苏绣以精细雅洁著称，双面绣为其绝技；湘绣以狮虎题材见长，鬅毛针法独特；粤绣色彩富丽，金银线垫绣立体感强；蜀绣针法多达百余种，以软缎和彩丝为主要材料。刺绣工艺是汉服高端定制的核心价值所在。",
            json.dumps(
                {
                    "en": "Four Great Embroideries of China",
                    "ja": "中国四大名刺繍",
                    "ko": "중국 사대 명자수",
                },
                ensure_ascii=False,
            ),
            None,
            json.dumps(
                {
                    "欧洲": "如法国高级定制刺绣工坊般的匠艺",
                    "北美": "堪比印第安珠绣的文化传承",
                    "东南亚": "与泰国皇家刺绣同为宫廷工艺",
                },
                ensure_ascii=False,
            ),
        ),
        (
            "形制",
            "宋代褙子的极简美学",
            "褙子是宋代女性最具代表性的日常外套，直领对襟，两侧开衩，长度及膝或及踝。宋代审美崇尚'清雅'，褙子的简约线条与素净配色完美体现了宋人的美学追求。与唐代的华丽张扬形成鲜明对比，宋代褙子展现的是内敛含蓄的东方优雅。这种'少即是多'的设计理念，与当代极简主义不谋而合。",
            json.dumps(
                {
                    "en": "Song Dynasty Beizi: Minimalist Aesthetics",
                    "ja": "宋の褙子—極簡の美学",
                    "ko": "송대 배자—극간의 미학",
                },
                ensure_ascii=False,
            ),
            None,
            json.dumps(
                {
                    "日韩": "与和服羽织有异曲同工之妙",
                    "欧洲": "如Coco Chanel小黑裙般的简约革命",
                    "北美": "极简主义设计理念的东方先驱",
                },
                ensure_ascii=False,
            ),
        ),
        (
            "礼仪",
            "冠礼 — 华夏男子的成人礼",
            "冠礼是中国古代汉族男子的成人仪式，起源于周代，被列为儒家'六礼'之首。男子二十而冠，由父亲或族长为其加冠三次：始加缁布冠、再加皮弁、三加爵弁，分别象征治人、武力、祭祀的权利与责任。冠礼的核心是'弃幼志，顺成德'，标志着从少年到成人的社会身份转变。",
            json.dumps(
                {
                    "en": "Guanli: The Coming-of-Age Ceremony",
                    "ja": "冠礼—漢民族男子の成人式",
                    "ko": "관례—화하 남자의 성인식",
                },
                ensure_ascii=False,
            ),
            None,
            json.dumps(
                {
                    "北美": "如犹太Bar Mitzvah般的成人仪式",
                    "欧洲": "如骑士授剑礼般的身份转换",
                    "东南亚": "与佛教出家礼同具仪式感",
                },
                ensure_ascii=False,
            ),
        ),
        (
            "纹样",
            "八宝纹的吉祥密码",
            "八宝纹是中国传统吉祥纹样中的经典组合，源于佛教'八吉祥'（八瑞相），包括宝伞、金鱼、宝瓶、妙莲、右旋白螺、吉祥结、胜利幢、金轮。每件法宝各有寓意：宝伞遮蔽魔障、金鱼象征自由、宝瓶代表财富、莲花寓意纯洁。八宝纹广泛应用于明清织锦和瓷器装饰之中。",
            json.dumps(
                {
                    "en": "Eight Treasures: Auspicious Symbols",
                    "ja": "八宝文—吉祥の暗号",
                    "ko": "팔보문—길상의 암호",
                },
                ensure_ascii=False,
            ),
            None,
            json.dumps(
                {
                    "欧洲": "如基督教圣物象征体系",
                    "北美": "如印第安Medicine Wheel的象征系统",
                    "中东": "与伊斯兰几何纹样的精神寓意共鸣",
                },
                ensure_ascii=False,
            ),
        ),
    ]

    for cat, title, content, multilingual, img_url, analogies in kb_seed:
        cursor.execute(
            """
            INSERT INTO knowledge_base (category, title_zh, content_zh, multilingual, image_url, cultural_analogies)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (cat, title, content, multilingual, img_url, analogies),
        )

    db.commit()
    print(f"[OK] Seed data injected:")
    print(f"   - 语料库: {len(corpus_seed)} 条术语")
    print(f"   - 规则库: {len(rules_seed)} 条规则")
    print(f"   - 审美库: {len(prefs_seed)} 条偏好")
    print(f"   - 知识库: {len(kb_seed)} 条条目")


if __name__ == "__main__":
    init_db()
    seed_initial_data()
    print("[*] CCAE Engine starting...")
    print("[*] API Docs: http://127.0.0.1:5000/api")
    print("[*] Admin Panel: http://127.0.0.1:5000/")
    # Debug模式从环境变量读取，生产环境默认关闭
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
