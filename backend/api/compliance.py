"""合规审核API路由"""

from flask import Blueprint, request, jsonify
from services.compliance_checker import ComplianceChecker

compliance_bp = Blueprint("compliance", __name__)
checker = ComplianceChecker()


@compliance_bp.route("/api/compliance/audit/text", methods=["POST"])
def audit_text():
    """文本合规审核"""
    data = request.json
    if not data or "text" not in data or "country" not in data:
        return jsonify({"error": "缺少必填参数: text, country"}), 400
    
    result = checker.audit_text(data["text"], data["country"])
    return jsonify(result)


@compliance_bp.route("/api/compliance/audit/image", methods=["POST"])
def audit_image():
    """图片合规审核"""
    data = request.json
    if not data or "image_path" not in data or "country" not in data:
        return jsonify({"error": "缺少必填参数: image_path, country"}), 400
    
    result = checker.audit_image(data["image_path"], data["country"])
    return jsonify(result)


@compliance_bp.route("/api/compliance/rules", methods=["GET"])
def list_rules():
    """规则列表"""
    page = request.args.get("page", 1, type=int)
    country = request.args.get("country")
    category = request.args.get("category")
    return jsonify(checker.get_rules(page=page, country=country, category=category))


@compliance_bp.route("/api/compliance/rules", methods=["POST"])
def add_rule():
    """添加规则"""
    data = request.json
    required = ["country", "category", "keywords", "reason", "suggestion"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"缺少必填字段: {field}"}), 400
    return jsonify(checker.add_rule(**data)), 201


@compliance_bp.route("/api/compliance/rules/<int:rule_id>", methods=["PUT"])
def update_rule(rule_id):
    return jsonify(checker.update_rule(rule_id, **request.json))


@compliance_bp.route("/api/compliance/rules/<int:rule_id>", methods=["DELETE"])
def delete_rule(rule_id):
    return jsonify(checker.delete_rule(rule_id))


@compliance_bp.route("/api/compliance/logs", methods=["GET"])
def audit_logs():
    page = request.args.get("page", 1, type=int)
    risk_level = request.args.get("risk_level")
    return jsonify(checker.get_audit_logs(page=page, risk_level=risk_level))


@compliance_bp.route("/api/compliance/stats", methods=["GET"])
def compliance_stats():
    return jsonify(checker.get_stats())
