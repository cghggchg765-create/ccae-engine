"""知识库与推荐API路由"""

from flask import Blueprint, request, jsonify
from services.recommender import KnowledgeBase, Recommender

knowledge_bp = Blueprint("knowledge", __name__)
kb = KnowledgeBase()
recommender = Recommender()


# ---- 知识库 ----
@knowledge_bp.route("/api/knowledge", methods=["GET"])
def search_knowledge():
    page = request.args.get("page", 1, type=int)
    keyword = request.args.get("keyword")
    category = request.args.get("category")
    return jsonify(kb.search(keyword, category, page))


@knowledge_bp.route("/api/knowledge", methods=["POST"])
def add_entry():
    data = request.json
    required = ["category", "title_zh"]
    for f in required:
        if f not in data:
            return jsonify({"error": f"缺少字段: {f}"}), 400
    return jsonify(kb.add_entry(**data)), 201


@knowledge_bp.route("/api/knowledge/<int:entry_id>", methods=["PUT"])
def update_entry(entry_id):
    return jsonify(kb.update_entry(entry_id, **request.json))


@knowledge_bp.route("/api/knowledge/<int:entry_id>", methods=["DELETE"])
def delete_entry(entry_id):
    return jsonify(kb.delete_entry(entry_id))


@knowledge_bp.route("/api/knowledge/generate-copy", methods=["POST"])
def generate_copy():
    data = request.json
    if not data or "topic" not in data or "region" not in data:
        return jsonify({"error": "缺少参数: topic, region"}), 400
    return jsonify(kb.generate_copy(data["topic"], data["region"]))


# ---- 推荐 ----
@knowledge_bp.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.json
    if not data or "user_profile" not in data or "visual_tags" not in data or "region" not in data:
        return jsonify({"error": "缺少参数: user_profile, visual_tags, region"}), 400
    return jsonify(recommender.recommend(
        data["user_profile"], data["visual_tags"], data["region"]))


@knowledge_bp.route("/api/recommend/logs", methods=["GET"])
def recommend_logs():
    page = request.args.get("page", 1, type=int)
    return jsonify(recommender.get_recommend_logs(page))
