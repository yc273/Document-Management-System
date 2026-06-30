"""
用户认证控制器
处理用户注册、登录、退出、个人信息管理等
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, current_user

from app.extensions import db
from app.models.user import User
from app.utils.decorators import login_required_json, active_required, admin_required
from app.utils.response import success, error, bad_request
from app.utils.auth_util import validate_email, validate_username, validate_password

# 创建蓝图
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册
    POST /api/auth/register

    请求体:
    {
        "username": "用户名",
        "password": "密码",
        "email": "邮箱(可选)",
        "nickname": "昵称(可选)"
    }
    """
    data = request.get_json()

    # 验证必填字段
    if not data or not data.get('username') or not data.get('password'):
        return bad_request('用户名和密码不能为空')

    username = data.get('username').strip()
    password = data.get('password')
    email = data.get('email', '').strip()
    nickname = data.get('nickname', '').strip()

    # 验证用户名格式
    if not validate_username(username):
        return bad_request('用户名格式不正确（4-20位字母数字下划线）')

    # 验证密码强度
    is_valid, msg = validate_password(password)
    if not is_valid:
        return bad_request(msg)

    # 验证邮箱格式
    if email and not validate_email(email):
        return bad_request('邮箱格式不正确')

    # 检查用户名是否存在
    if User.query.filter_by(username=username).first():
        return bad_request('用户名已存在')

    # 检查邮箱是否存在
    if email and User.query.filter_by(email=email).first():
        return bad_request('邮箱已被注册')

    # 创建用户
    user = User(
        username=username,
        email=email if email else None,
        nickname=nickname if nickname else username
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return success({
        'user': user.to_dict()
    }, message='注册成功')


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录
    POST /api/auth/login

    请求体:
    {
        "username": "用户名或邮箱",
        "password": "密码"
    }
    """
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return bad_request('用户名和密码不能为空')

    username = data.get('username').strip()
    password = data.get('password')

    # 查找用户（支持用户名或邮箱登录）
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User.query.filter_by(email=username).first()

    # 验证用户
    if not user or not user.check_password(password):
        return error(message='用户名或密码错误', code=401)

    # 检查账户状态
    if not user.is_active():
        return error(message='账户已被禁用', code=403)

    # 登录用户
    login_user(user)

    return success({
        'user': user.to_dict()
    }, message='登录成功')


@auth_bp.route('/logout', methods=['POST'])
@login_required_json
def logout():
    """
    用户退出
    POST /api/auth/logout
    """
    logout_user()
    return success(message='退出成功')


@auth_bp.route('/info', methods=['GET'])
@login_required_json
def get_info():
    """
    获取当前用户信息
    GET /api/auth/info
    """
    return success({
        'user': current_user.to_dict()
    })


@auth_bp.route('/password', methods=['PUT'])
@login_required_json
@active_required
def change_password():
    """
    修改密码
    PUT /api/auth/password

    请求体:
    {
        "old_password": "旧密码",
        "new_password": "新密码"
    }
    """
    data = request.get_json()

    if not data or not data.get('old_password') or not data.get('new_password'):
        return bad_request('旧密码和新密码不能为空')

    old_password = data.get('old_password')
    new_password = data.get('new_password')

    # 验证旧密码
    if not current_user.check_password(old_password):
        return bad_request('旧密码错误')

    # 验证新密码强度
    is_valid, msg = validate_password(new_password)
    if not is_valid:
        return bad_request(msg)

    # 修改密码
    current_user.set_password(new_password)
    db.session.commit()

    return success(message='密码修改成功')


@auth_bp.route('/profile', methods=['PUT'])
@login_required_json
@active_required
def update_profile():
    """
    修改个人信息
    PUT /api/auth/profile

    请求体:
    {
        "nickname": "昵称",
        "email": "邮箱"
    }
    """
    data = request.get_json()

    if not data:
        return bad_request('请求参数不能为空')

    # 修改昵称
    if 'nickname' in data:
        nickname = data.get('nickname', '').strip()
        if nickname:
            current_user.nickname = nickname

    # 修改邮箱
    if 'email' in data:
        email = data.get('email', '').strip()

        if email:
            # 验证邮箱格式
            if not validate_email(email):
                return bad_request('邮箱格式不正确')

            # 检查邮箱是否被占用
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != current_user.id:
                return bad_request('邮箱已被其他用户使用')

            current_user.email = email

    db.session.commit()

    return success({
        'user': current_user.to_dict()
    }, message='个人信息更新成功')


@auth_bp.route('/avatar', methods=['POST'])
@login_required_json
@active_required
def upload_avatar():
    """
    上传头像
    POST /api/auth/avatar

    请求体: multipart/form-data
    {
        "file": 头像文件
    }
    """
    from werkzeug.utils import secure_filename
    import os
    from datetime import datetime

    if 'file' not in request.files:
        return bad_request('请选择头像文件')

    file = request.files['file']

    if file.filename == '':
        return bad_request('未选择文件')

    # 检查文件类型
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return bad_request('只支持上传图片文件（png, jpg, jpeg, gif, webp）')

    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"avatar_{current_user.id}_{timestamp}.jpg"
    filepath = os.path.join(current_app.config['UPLOAD_AVATARS'], filename)

    # 保存文件
    file.save(filepath)

    # 删除旧头像
    if current_user.avatar:
        old_avatar_path = os.path.join(current_app.config['UPLOAD_AVATARS'],
                                      os.path.basename(current_user.avatar))
        if os.path.exists(old_avatar_path):
            os.remove(old_avatar_path)

    # 更新用户头像
    current_user.avatar = f"/uploads/avatars/{filename}"
    db.session.commit()

    return success({
        'avatar': current_user.avatar
    }, message='头像上传成功')


@auth_bp.route('/users', methods=['GET'])
@login_required_json
@admin_required
def get_users():
    """
    获取用户列表（管理员）
    GET /api/auth/users
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()

    query = User.query

    # 关键词搜索
    if keyword:
        query = query.filter(
            db.or_(
                User.username.like(f'%{keyword}%'),
                User.email.like(f'%{keyword}%'),
                User.nickname.like(f'%{keyword}%')
            )
        )

    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success({
        'users': [user.to_dict() for user in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required_json
@admin_required
def update_user(user_id):
    """
    更新用户信息（管理员）
    PUT /api/auth/users/<user_id>
    """
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    # 修改状态
    if 'status' in data:
        user.status = data.get('status', 1)

    # 修改角色
    if 'role' in data:
        user.role = data.get('role', 'user')

    # 修改存储限制
    if 'storage_limit' in data:
        user.storage_limit = data.get('storage_limit')

    db.session.commit()

    return success({
        'user': user.to_dict()
    }, message='用户信息更新成功')


@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required_json
@admin_required
def delete_user(user_id):
    """
    删除用户（管理员）
    DELETE /api/auth/users/<user_id>
    """
    user = User.query.get_or_404(user_id)

    # 不能删除自己
    if user.id == current_user.id:
        return bad_request('不能删除当前登录用户')

    db.session.delete(user)
    db.session.commit()

    return success(message='用户删除成功')
