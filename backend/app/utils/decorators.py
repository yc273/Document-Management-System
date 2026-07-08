"""
认证装饰器
包含登录验证、权限检查等装饰器
"""
from functools import wraps
from flask import jsonify
from flask_login import current_user


def login_required_json(func):
    """
    JSON接口登录验证装饰器
    如果未登录，返回JSON格式的401错误
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'code': 401,
                'message': '未授权，请先登录',
                'data': None
            }), 401
        return func(*args, **kwargs)
    return decorated_function


def admin_required(func):
    """
    管理员权限验证装饰器
    如果不是管理员，返回403错误
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'code': 401,
                'message': '未授权，请先登录',
                'data': None
            }), 401

        if not current_user.is_admin():
            return jsonify({
                'code': 403,
                'message': '权限不足，需要管理员权限',
                'data': None
            }), 403

        return func(*args, **kwargs)
    return decorated_function


def active_required(func):
    """
    账户激活状态验证装饰器
    如果账户被禁用，返回403错误
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'code': 401,
                'message': '未授权，请先登录',
                'data': None
            }), 401

        if not current_user.is_active():
            return jsonify({
                'code': 403,
                'message': '账户已被禁用',
                'data': None
            }), 403

        return func(*args, **kwargs)
    return decorated_function


def check_file_permission(user_id, file_id):
    """
    检查用户是否有权限访问文档

    Args:
        user_id: 用户ID
        file_id: 文档ID

    Returns:
        bool: 是否有权限
    """
    from app.models.file import File

    file = File.query.filter_by(id=file_id).first()

    if not file:
        return False

    # 文档所有者有权限
    if file.user_id == user_id:
        return True

    # 管理员有权限
    from app.models.user import User
    user = User.query.filter_by(id=user_id).first()
    if user and user.is_admin():
        return True

    # TODO: 检查共享权限和授权权限

    return False


def check_folder_permission(user_id, folder_id):
    """
    检查用户是否有权限访问文件夹

    Args:
        user_id: 用户ID
        folder_id: 文件夹ID

    Returns:
        bool: 是否有权限
    """
    # 根目录（folder_id=0）所有用户都有权限
    if folder_id == 0:
        return True

    from app.models.folder import Folder

    folder = Folder.query.filter_by(id=folder_id).first()

    if not folder:
        return False

    # 文件夹所有者有权限
    if folder.user_id == user_id:
        return True

    # 管理员有权限
    from app.models.user import User
    user = User.query.filter_by(id=user_id).first()
    if user and user.is_admin():
        return True

    return False
