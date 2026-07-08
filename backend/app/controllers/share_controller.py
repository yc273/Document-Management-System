"""
分享管理控制器
处理文档分享、访问权限等操作
"""
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required

from app.extensions import db
from app.models.share import Share
from app.models.file import File
from app.utils.decorators import login_required_json, active_required
from app.utils.response import success, error, bad_request, not_found

# 创建蓝图
share_bp = Blueprint('share', __name__)


@share_bp.route('/create', methods=['POST'])
@login_required_json
@active_required
def create_share():
    """
    创建分享
    POST /api/share/create

    请求体:
    {
        "file_id": 文档ID,
        "password": 密码（可选）,
        "expire_days": 有效天数（可选）
    }
    """
    data = request.get_json()

    if not data or not data.get('file_id'):
        return bad_request('文档ID不能为空')

    file_id = data.get('file_id')
    password = (data.get('password') or '').strip()
    expire_days = data.get('expire_days', 7)

    # 检查文档权限
    file = File.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        return error(message='没有权限分享该文档', code=403)

    # 创建分享
    share = Share.create_share(
        file_id=file_id,
        created_by=current_user.id,
        password=password if password else None,
        expire_days=expire_days
    )

    return success({
        'share': share.to_dict()
    }, message='分享创建成功')


@share_bp.route('/list', methods=['GET'])
@login_required_json
@active_required
def get_share_list():
    """
    获取我的分享列表
    GET /api/share/list
    """
    shares = Share.get_user_shares(current_user.id)

    return success({
        'shares': [share.to_dict() for share in shares]
    })


@share_bp.route('/<int:share_id>', methods=['DELETE'])
@login_required_json
@active_required
def delete_share(share_id):
    """
    取消分享
    DELETE /api/share/<share_id>
    """
    share = Share.query.get_or_404(share_id)

    # 权限检查
    if share.created_by != current_user.id:
        return error(message='没有权限取消该分享', code=403)

    db.session.delete(share)
    db.session.commit()

    return success(message='分享已取消')


@share_bp.route('/<share_code>', methods=['GET'])
def access_share(share_code):
    """
    访问分享
    GET /api/share/<share_code>
    """
    share = Share.get_share_by_code(share_code)

    if not share:
        return not_found('分享不存在')

    # 检查是否过期
    if share.is_expired():
        return error(message='分享已过期', code=403)

    # 增加查看次数
    share.increment_view()

    return success({
        'share': share.to_dict(include_file=True)
    })


@share_bp.route('/<share_code>/verify', methods=['POST'])
def verify_share_password(share_code):
    """
    验证分享密码
    POST /api/share/<share_code>/verify

    请求体:
    {
        "password": 密码
    }
    """
    share = Share.get_share_by_code(share_code)

    if not share:
        return not_found('分享不存在')

    if share.is_expired():
        return error(message='分享已过期', code=403)

    data = request.get_json()
    password = data.get('password', '') if data else ''

    # 验证密码
    if not share.verify_password(password):
        return error(message='密码错误', code=401)

    return success(message='密码验证成功')


@share_bp.route('/stats/<int:share_id>', methods=['GET'])
@login_required_json
@active_required
def get_share_stats(share_id):
    """
    获取分享统计
    GET /api/share/stats/<share_id>
    """
    share = Share.query.get_or_404(share_id)

    # 权限检查
    if share.created_by != current_user.id:
        return error(message='没有权限查看该分享统计', code=403)

    return success({
        'share': share.to_dict()
    })
