"""翻译API路由"""

from flask import Blueprint, request, jsonify
from services.translator import TranslatorService

translate_bp = Blueprint("translate", __name__)
service = TranslatorService()


@translate_bp.route("/api/translate", methods=["POST"])
def translate():
    """翻译接口"""
    data = request.json
    if not data or "text" not in data or "target_lang" not in data:
        return jsonify({"error": "缺少必填参数: text, target_lang"}), 400
    
    result = service.translate(data["text"], data["target_lang"])
    return jsonify(result)


@translate_bp.route("/api/corpus", methods=["GET"])
def list_corpus():
    """语料库列表"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    category = request.args.get("category")
    keyword = request.args.get("keyword")
    result = service.get_corpus(page, per_page, category, keyword)
    return jsonify(result)


@translate_bp.route("/api/corpus", methods=["POST"])
def add_term():
    """添加术语"""
    data = request.json
    required = ["term_zh", "category", "translations"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"缺少必填字段: {field}"}), 400
    
    result = service.add_term(**data)
    return jsonify(result), 201


@translate_bp.route("/api/corpus/<int:term_id>", methods=["PUT"])
def update_term(term_id):
    """更新术语"""
    result = service.update_term(term_id, **request.json)
    return jsonify(result)


@translate_bp.route("/api/corpus/<int:term_id>", methods=["DELETE"])
def delete_term(term_id):
    """删除术语"""
    result = service.delete_term(term_id)
    return jsonify(result)


@translate_bp.route("/api/translate/stats", methods=["GET"])
def translate_stats():
    """翻译模块统计"""
    return jsonify(service.get_stats())
