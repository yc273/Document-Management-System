"""
回收站管理控制器
处理回收站相关操作
"""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user, login_required

from app.extensions import db
from app.models.file import File
from app.models.folder import Folder
from app.models.log import Log
from app.utils.decorators import login_required_json, active_required
from app.utils.response import success, error, not_found
from app.utils.file_util import delete_file

# 创建蓝图
trash_bp = Blueprint('trash', __name__)


def auto_cleanup_expired_trash(user_id=None):
    """
    自动清理过期回收站内容（文件和文件夹）。
    删除时间超过 TRASH_RETENTION_DAYS 天的记录将被永久删除（含物理文件）。

    Args:
        user_id: 指定用户ID则只清理该用户；为None则清理所有用户
    """
    retention_days = current_app.config.get('TRASH_RETENTION_DAYS', 30)
    deadline = datetime.now() - timedelta(days=retention_days)
    cleaned = 0

    # 1. 清理过期的文件夹（级联：包含子孙文件夹和内部文件）
    folder_query = Folder.query.filter(Folder.is_deleted == 1, Folder.deleted_at <= deadline)
    if user_id is not None:
        folder_query = folder_query.filter(Folder.user_id == user_id)
    expired_folders = folder_query.all()
    for folder in expired_folders:
        # 收集该文件夹 + 子孙文件夹
        all_ids = [folder.id] + folder.get_descendant_folder_ids()
        # 删除这些文件夹下的所有文件的物理文件（安全删除）
        files_in = File.query.filter(File.folder_id.in_(all_ids)).all()
        for f in files_in:
            _safe_remove_physical_file(f)
            db.session.delete(f)
        # 删除这些文件夹记录
        for fid in all_ids:
            f_obj = Folder.query.filter_by(id=fid).first()
            if f_obj:
                db.session.delete(f_obj)
        cleaned += 1

    # 2. 清理过期的散落文件（不属于任何已删除文件夹的）
    file_query = File.query.filter(File.is_deleted == 1, File.deleted_at <= deadline)
    if user_id is not None:
        file_query = file_query.filter(File.user_id == user_id)
    expired_files = file_query.all()
    for file in expired_files:
        _safe_remove_physical_file(file)
        db.session.delete(file)
        cleaned += 1

    if cleaned:
        db.session.commit()

    return cleaned


@trash_bp.route('/list', methods=['GET'])
@login_required_json
@active_required
def get_trash_list():
    """
    获取回收站列表（包含文件和文件夹）
    GET /api/trash/list

    参数:
    - page: 页码
    - per_page: 每页数量
    """
    # 先清理过期的回收站内容（超过保留天数的自动永久删除）
    auto_cleanup_expired_trash(current_user.id)

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # --- 收集顶层软删除文件夹（父文件夹未软删除的，避免显示嵌套子文件夹）---
    all_deleted_folders = Folder.query.filter_by(user_id=current_user.id, is_deleted=1).all()
    top_folders = []
    for folder in all_deleted_folders:
        if not folder.parent_id or folder.parent_id == 0:
            top_folders.append(folder)
        else:
            parent = Folder.query.get(folder.parent_id)
            # 父文件夹未软删除 → 这是顶层被删文件夹
            if not parent or parent.is_deleted == 0:
                top_folders.append(folder)

    folder_items = []
    for folder in top_folders:
        item = folder.to_dict()
        item['item_type'] = 'folder'
        # 统计内部文件数（含子孙）
        all_ids = [folder.id] + folder.get_descendant_folder_ids()
        item['inner_file_count'] = File.query.filter(File.folder_id.in_(all_ids)).count()
        folder_items.append((folder.deleted_at, item))

    # --- 收集散落的已删除文件（其所在文件夹未被整体软删除的）---
    all_deleted_files = File.query.filter_by(user_id=current_user.id, is_deleted=1).all()
    file_items = []
    deleted_folder_ids = set(f.id for f in all_deleted_folders)
    for file in all_deleted_files:
        # 如果文件属于某个被软删除的文件夹，则不单独显示（随文件夹整体显示）
        if file.folder_id and file.folder_id in deleted_folder_ids:
            continue
        item = file.to_dict()
        item['item_type'] = 'file'
        item['original_folder_id'] = file.folder_id or 0
        if file.folder_id and file.folder_id != 0:
            item['original_folder_exists'] = Folder.query.filter_by(id=file.folder_id).first() is not None
        else:
            item['original_folder_exists'] = True
        file_items.append((file.deleted_at, item))

    # --- 合并并按删除时间倒序 ---
    all_items = folder_items + file_items
    all_items.sort(key=lambda x: x[0] or datetime.min, reverse=True)
    total = len(all_items)

    # 手动分页
    start = (page - 1) * per_page
    end = start + per_page
    page_items = [item for _, item in all_items[start:end]]
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    return success({
        'files': page_items,  # 保持字段名兼容前端
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': pages
    })


@trash_bp.route('/restore/<int:file_id>', methods=['POST'])
@login_required_json
@active_required
def restore_file(file_id):
    """
    恢复文档
    POST /api/trash/restore/<file_id>

    请求体（可选）:
    {
        "folder_id": "恢复到的目标文件夹ID，不传或为0表示根目录"
    }
    """
    file = File.query.get_or_404(file_id)

    # 权限检查
    if file.user_id != current_user.id:
        return error(message='没有权限恢复该文档', code=403)

    # 解析目标文件夹ID
    data = request.get_json(silent=True) or {}
    target_folder_id = data.get('folder_id')

    # 判断文件原文件夹是否还存在
    original_folder_id = file.folder_id or 0
    original_exists = True
    if original_folder_id != 0:
        original_exists = Folder.query.filter_by(id=original_folder_id).first() is not None

    # 决定恢复到哪个文件夹
    if target_folder_id is not None:
        # 用户显式指定了目标文件夹（不允许为根目录 0，文件必须放到某个文件夹下）
        target_folder_id = int(target_folder_id)
        if target_folder_id == 0:
            return error(message='请选择一个文件夹，不能恢复到根目录', code=400)
        # 校验目标文件夹存在且属于当前用户
        target = Folder.query.filter_by(id=target_folder_id, user_id=current_user.id).first()
        if not target:
            return error(message='目标文件夹不存在或无权限', code=400)
        file.folder_id = target_folder_id
    else:
        # 用户未指定：若原文件夹还在，恢复到原位置；否则要求用户选择目标文件夹
        if not original_exists:
            return error(message='原文件夹已被删除，请选择一个文件夹后再恢复', code=400)

    # 恢复文档（清除软删除标记）
    file.restore()

    return success(message='文档已恢复')


@trash_bp.route('/restore-folder/<int:folder_id>', methods=['POST'])
@login_required_json
@active_required
def restore_folder(folder_id):
    """
    恢复文件夹（整体级联恢复）
    POST /api/trash/restore-folder/<folder_id>
    """
    folder = Folder.query.get_or_404(folder_id)

    # 权限检查
    if folder.user_id != current_user.id:
        return error(message='没有权限恢复该文件夹', code=403)

    if folder.is_deleted != 1:
        return bad_request('该文件夹不在回收站中')

    # 检查原父文件夹情况：若不存在（被硬删除，理论上软删除不会出现）则挂到根目录
    if folder.parent_id and folder.parent_id != 0:
        parent = Folder.query.get(folder.parent_id)
        if not parent:
            folder.parent_id = 0
            folder.path = f'/{folder.name}'
            folder.level = 1

    # 级联恢复（文件夹 + 子孙 + 内部文件，若父级链也被删则一并恢复）
    folder.restore_cascade()

    # 记录日志
    Log.create_log(
        user_id=current_user.id,
        action='restore',
        module='folder',
        description=f'恢复文件夹: {folder.name}',
        ip_address=request.remote_addr
    )

    return success(message='文件夹已恢复')


def _safe_remove_physical_file(file):
    """
    安全删除物理文件：仅当没有其他数据库记录引用同一物理文件时才删除。
    （系统支持秒传，同一物理文件可能被多条记录共享。）
    """
    if not file.file_path:
        return
    other_refs = File.query.filter(
        File.id != file.id,
        File.file_path == file.file_path
    ).count()
    if other_refs == 0:
        delete_file(file.file_path)


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

    # 删除物理文件（仅在无其他记录引用时）
    _safe_remove_physical_file(file)

    # 删除数据库记录
    db.session.delete(file)
    db.session.commit()

    return success(message='文档已永久删除')


@trash_bp.route('/delete-folder/<int:folder_id>', methods=['DELETE'])
@login_required_json
@active_required
def delete_folder_permanently(folder_id):
    """
    永久删除文件夹（级联删除子孙文件夹和内部文件的物理文件及记录）
    DELETE /api/trash/delete-folder/<folder_id>
    """
    folder = Folder.query.get_or_404(folder_id)

    # 权限检查
    if folder.user_id != current_user.id:
        return error(message='没有权限删除该文件夹', code=403)

    if folder.is_deleted != 1:
        return bad_request('该文件夹不在回收站中')

    # 收集子孙文件夹
    all_ids = [folder.id] + folder.get_descendant_folder_ids()

    # 删除这些文件夹下的所有文件的物理文件（安全删除）+ 记录
    files_in = File.query.filter(File.folder_id.in_(all_ids)).all()
    for f in files_in:
        _safe_remove_physical_file(f)
        db.session.delete(f)

    # 删除文件夹记录
    for fid in all_ids:
        f_obj = Folder.query.filter_by(id=fid).first()
        if f_obj:
            db.session.delete(f_obj)

    db.session.commit()

    return success(message='文件夹已永久删除')


@trash_bp.route('/clear', methods=['DELETE'])
@login_required_json
@active_required
def clear_trash():
    """
    清空回收站（文件和文件夹）
    DELETE /api/trash/clear
    """
    deleted_count = 0

    # 1. 清空所有已删除文件夹（级联）
    folders = Folder.query.filter_by(user_id=current_user.id, is_deleted=1).all()
    for folder in folders:
        all_ids = [folder.id] + folder.get_descendant_folder_ids()
        files_in = File.query.filter(File.folder_id.in_(all_ids)).all()
        for f in files_in:
            _safe_remove_physical_file(f)
            db.session.delete(f)
        for fid in all_ids:
            f_obj = Folder.query.filter_by(id=fid).first()
            if f_obj:
                db.session.delete(f_obj)
        deleted_count += 1

    # 2. 清空所有散落的已删除文件
    files = File.query.filter_by(user_id=current_user.id, is_deleted=1).all()
    for file in files:
        _safe_remove_physical_file(file)
        db.session.delete(file)
        deleted_count += 1

    db.session.commit()

    return success({
        'deleted_count': deleted_count
    }, message=f'回收站已清空，删除了{deleted_count}项')
