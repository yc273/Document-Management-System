"""
响应封装工具
统一API响应格式
"""
from flask import jsonify
from datetime import datetime


def success(data=None, message='success', code=200):
    """
    成功响应

    Args:
        data: 响应数据
        message: 响应消息
        code: 状态码

    Returns:
        JSON: 响应对象
    """
    response = {
        'code': code,
        'message': message,
        'data': data,
        'timestamp': int(datetime.now().timestamp())
    }

    return jsonify(response)


def error(message='error', code=400, data=None):
    """
    错误响应

    Args:
        message: 错误消息
        code: 状态码
        data: 响应数据

    Returns:
        JSON: 响应对象
    """
    response = {
        'code': code,
        'message': message,
        'data': data,
        'timestamp': int(datetime.now().timestamp())
    }

    return jsonify(response), code


def success_with_pagination(data, total, page=1, per_page=20, message='success'):
    """
    分页成功响应

    Args:
        data: 数据列表
        total: 总数
        page: 当前页
        per_page: 每页数量
        message: 响应消息

    Returns:
        JSON: 响应对象
    """
    response = {
        'code': 200,
        'message': message,
        'data': data,
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        },
        'timestamp': int(datetime.now().timestamp())
    }

    return jsonify(response)


def not_found(message='资源不存在'):
    """
    404响应

    Args:
        message: 错误消息

    Returns:
        JSON: 响应对象
    """
    return error(message=message, code=404)


def unauthorized(message='未授权，请先登录'):
    """
    401响应

    Args:
        message: 错误消息

    Returns:
        JSON: 响应对象
    """
    return error(message=message, code=401)


def forbidden(message='禁止访问'):
    """
    403响应

    Args:
        message: 错误消息

    Returns:
        JSON: 响应对象
    """
    return error(message=message, code=403)


def bad_request(message='请求参数错误', data=None):
    """
    400响应

    Args:
        message: 错误消息
        data: 响应数据

    Returns:
        JSON: 响应对象
    """
    return error(message=message, code=400, data=data)


def server_error(message='服务器内部错误'):
    """
    500响应

    Args:
        message: 错误消息

    Returns:
        JSON: 响应对象
    """
    return error(message=message, code=500)
