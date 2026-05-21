"""视觉识别API路由"""

from flask import Blueprint, request, jsonify
from services.vision_analyzer import VisionAnalyzer

vision_bp = Blueprint("vision", __name__)
analyzer = VisionAnalyzer()


@vision_bp.route("/api/vision/analyze", methods=["POST"])
def analyze():
    """汉服视觉识别"""
    data = request.json
    if not data or "image_path" not in data:
        return jsonify({"error": "缺少参数: image_path"}), 400
    return jsonify(analyzer.analyze(data["image_path"]))


@vision_bp.route("/api/vision/aesthetic-match", methods=["POST"])
def aesthetic_match():
    """区域审美匹配"""
    data = request.json
    if not data or "visual_tags" not in data or "region" not in data:
        return jsonify({"error": "缺少参数: visual_tags, region"}), 400
    return jsonify(analyzer.match_aesthetic(data["visual_tags"], data["region"]))


@vision_bp.route("/api/vision/preferences", methods=["GET"])
def list_preferences():
    region = request.args.get("region")
    return jsonify(analyzer.get_preferences(region))


@vision_bp.route("/api/vision/preferences", methods=["POST"])
def add_preference():
    data = request.json
    required = ["region", "category", "preference"]
    for f in required:
        if f not in data:
            return jsonify({"error": f"缺少字段: {f}"}), 400
    return jsonify(analyzer.add_preference(**data)), 201


@vision_bp.route("/api/vision/preferences/<int:pref_id>", methods=["DELETE"])
def delete_preference(pref_id):
    return jsonify(analyzer.delete_preference(pref_id))


@vision_bp.route("/api/vision/stats", methods=["GET"])
def vision_stats():
    return jsonify(analyzer.get_vision_stats())
