"""
回收站管理控制器
处理回收站相关操作
"""
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required

from app.extensions import db
from app.models.file import File
from app.utils.decorators import login_required_json, active_required
from app.utils.response import success, error, not_found
from app.utils.file_util import delete_file

# 创建蓝图
trash_bp = Blueprint('trash', __name__)


@trash_bp.route('/list', methods=['GET'])
@login_required_json
@active_required
def get_trash_list():
    """
    获取回收站列表
    GET /api/trash/list

    参数:
    - page: 页码
    - per_page: 每页数量
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 获取已删除的文档
    query = File.query.filter_by(user_id=current_user.id, is_deleted=1)

    # 分页
    pagination = query.order_by(File.deleted_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return success({
        'files': [file.to_dict() for file in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@trash_bp.route('/restore/<int:file_id>', methods=['POST'])
@login_required_json
@active_required
def restore_file(file_id):
    """
    恢复文档
    POST /api/trash/restore/<file_id>
    """
    file = File.query.get_or_404(file_id)

    # 权限检查
    if file.user_id != current_user.id:
        return error(message='没有权限恢复该文档', code=403)

    # 恢复文档
    file.restore()

    return success(message='文档已恢复')


@trash_bp.route('/delete/<int:file_id>', methods=['DELETE'])
@login_required_json
@active_required
def delete_file_permanently(file_id):
    """
    永久删除文档
    DELETE /api/trash/delete/<file_id>
    """
    file = File.query.get_or_404(file_id)

    # 权限检查
    if file.user_id != current_user.id:
        return error(message='没有权限删除该文档', code=403)

    # 删除文件
    if file.file_path:
        delete_file(file.file_path)

    # 删除数据库记录
    db.session.delete(file)
    db.session.commit()

    return success(message='文档已永久删除')


@trash_bp.route('/clear', methods=['DELETE'])
@login_required_json
@active_required
def clear_trash():
    """
    清空回收站
    DELETE /api/trash/clear
    """
    # 获取所有已删除文档
    files = File.query.filter_by(user_id=current_user.id, is_deleted=1).all()

    # 删除文件和记录
    deleted_count = 0
    for file in files:
        if file.file_path:
            delete_file(file.file_path)
        db.session.delete(file)
        deleted_count += 1

    db.session.commit()

    return success({
        'deleted_count': deleted_count
    }, message=f'回收站已清空，删除了{deleted_count}个文档')
