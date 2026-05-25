"""AI供应商管理API路由

提供供应商配置的增删改查接口。
"""

from flask import Blueprint, request, jsonify
from services.provider_config import get_provider_manager

providers_bp = Blueprint("providers", __name__)


@providers_bp.route("/api/ai/providers", methods=["GET"])
def list_providers():
    """获取所有供应商配置

    Returns:
        list: 供应商列表，包含端点和模型映射信息
    """
    manager = get_provider_manager()
    providers = manager.list_providers()
    return jsonify({
        "success": True,
        "data": providers,
        "count": len(providers)
    })


@providers_bp.route("/api/ai/providers", methods=["POST"])
def add_provider():
    """添加供应商

    Request Body:
        {
            "id": "provider-id",
            "name": "显示名称",
            "provider_type": "openai|deepseek|qwen|custom",
            "endpoints": [
                {
                    "id": "endpoint-id",
                    "name": "端点名称",
                    "base_url": "https://api.example.com/v1",
                    "api_key": "sk-xxx",
                    "model_mapping": {
                        "primary": "model-name",
                        "light": "light-model",
                        "balanced": "balanced-model",
                        "strongest": "strongest-model"
                    },
                    "is_default": true
                }
            ]
        }

    Returns:
        dict: 添加后的供应商配置
    """
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "请求体不能为空"}), 400

    manager = get_provider_manager()
    try:
        provider = manager.add_provider(data)
        return jsonify({
            "success": True,
            "data": provider,
            "message": f"供应商 '{provider['name']}' 添加成功"
        }), 201
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@providers_bp.route("/api/ai/providers/<provider_id>", methods=["GET"])
def get_provider(provider_id):
    """获取单个供应商配置

    Args:
        provider_id: 供应商ID

    Returns:
        dict: 供应商配置详情
    """
    manager = get_provider_manager()
    provider = manager.get_provider(provider_id)
    if not provider:
        return jsonify({
            "success": False,
            "error": f"供应商 '{provider_id}' 不存在"
        }), 404

    return jsonify({
        "success": True,
        "data": provider
    })


@providers_bp.route("/api/ai/providers/<provider_id>", methods=["PUT"])
def update_provider(provider_id):
    """更新供应商配置

    Args:
        provider_id: 供应商ID

    Request Body:
        供应商完整配置（会替换现有配置）

    Returns:
        dict: 更新后的供应商配置
    """
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "请求体不能为空"}), 400

    manager = get_provider_manager()
    try:
        provider = manager.update_provider(provider_id, data)
        return jsonify({
            "success": True,
            "data": provider,
            "message": f"供应商 '{provider['name']}' 更新成功"
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@providers_bp.route("/api/ai/providers/<provider_id>", methods=["DELETE"])
def delete_provider(provider_id):
    """删除供应商

    Args:
        provider_id: 供应商ID

    Returns:
        dict: 删除结果
    """
    manager = get_provider_manager()
    try:
        manager.delete_provider(provider_id)
        return jsonify({
            "success": True,
            "message": f"供应商 '{provider_id}' 已删除"
        })
    except ValueError as e:
        error_msg = str(e)
        if "不存在" in error_msg:
            return jsonify({"success": False, "error": error_msg}), 404
        return jsonify({"success": False, "error": error_msg}), 400


@providers_bp.route("/api/ai/providers/<provider_id>/activate", methods=["POST"])
def activate_provider(provider_id):
    """激活供应商

    将指定供应商设为当前使用的供应商，同时取消其他供应商的激活状态。

    Args:
        provider_id: 供应商ID

    Returns:
        dict: 激活后的供应商配置
    """
    manager = get_provider_manager()
    try:
        provider = manager.activate_provider(provider_id)
        return jsonify({
            "success": True,
            "data": provider,
            "message": f"供应商 '{provider['name']}' 已激活"
        })
    except ValueError as e:
        error_msg = str(e)
        if "不存在" in error_msg:
            return jsonify({"success": False, "error": error_msg}), 404
        return jsonify({"success": False, "error": error_msg}), 400


@providers_bp.route("/api/ai/providers/<provider_id>/test", methods=["POST"])
def test_provider(provider_id):
    """测试供应商连接

    发送测试请求验证API配置是否正确。

    Args:
        provider_id: 供应商ID

    Request Body (可选):
        {
            "endpoint_id": "指定端点ID，不传则使用默认端点"
        }

    Returns:
        dict: 测试结果
            - success: 是否成功
            - message: 结果消息
            - latency: 响应延迟（毫秒）
    """
    data = request.json or {}
    endpoint_id = data.get("endpoint_id")

    manager = get_provider_manager()
    result = manager.test_connection(provider_id, endpoint_id)

    status_code = 200 if result.get("success") else 400
    return jsonify({
        "success": result.get("success", False),
        "data": result
    }), status_code


@providers_bp.route("/api/ai/current", methods=["GET"])
def get_current_provider():
    """获取当前激活的供应商

    Returns:
        dict: 当前激活的供应商配置，包含完整API密钥（用于API调用）
            若无激活供应商则返回 null
    """
    manager = get_provider_manager()
    provider = manager.get_active_provider()

    if not provider:
        return jsonify({
            "success": True,
            "data": None,
            "message": "当前无激活的供应商"
        })

    return jsonify({
        "success": True,
        "data": provider
    })
