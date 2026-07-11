"""
文件夹管理控制器
处理文件夹的创建、修改、删除、移动等操作
"""
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required

from app.extensions import db
from app.models.folder import Folder
from app.models.file import File
from app.models.log import Log
from app.utils.decorators import login_required_json, active_required
from app.utils.response import success, error, bad_request, not_found
from app.utils.decorators import check_folder_permission

# 创建蓝图
folder_bp = Blueprint('folder', __name__)


@folder_bp.route('/list', methods=['GET'])
@login_required_json
@active_required
def get_folder_list():
    """
    获取文件夹列表（树形结构）
    GET /api/folder/list
    """
    # 获取用户的文件夹树
    folder_tree = Folder.get_folder_tree(current_user.id)

    # 获取用户所有未删除文件的总数（按记录数统计，不去重）
    total_files = File.query.filter(
        File.user_id == current_user.id,
        File.is_deleted == 0
    ).count()

    return success({
        'folders': folder_tree,
        'total_files': total_files
    })


@folder_bp.route('/', methods=['POST'])
@folder_bp.route('', methods=['POST'])
@login_required_json
@active_required
def create_folder():
    """
    创建文件夹
    POST /api/folder 或 /api/folder/

    请求体:
    {
        "name": "文件夹名称",
        "parent_id": "父文件夹ID（可选，默认为0）"
    }
    """
    data = request.get_json()

    if not data or not data.get('name'):
        return bad_request('文件夹名称不能为空')

    name = data.get('name', '').strip()
    parent_id = data.get('parent_id', 0)

    # 检查文件夹名称
    if not name:
        return bad_request('文件夹名称不能为空')

    # 检查父文件夹权限
    if parent_id != 0:
        if not check_folder_permission(current_user.id, parent_id):
            return error(message='没有权限访问父文件夹', code=403)

        parent = Folder.query.filter_by(id=parent_id).first()
        if not parent:
            return not_found('父文件夹不存在')

        if parent.user_id != current_user.id:
            return bad_request('只能在当前用户目录下创建文件夹')

    # 检查同级文件夹是否已存在同名（仅未删除的）
    existing = Folder.query.filter_by(
        user_id=current_user.id,
        parent_id=parent_id,
        name=name,
        is_deleted=0
    ).first()

    if existing:
        return bad_request('该文件夹下已存在同名文件夹')

    # 创建文件夹
    folder = Folder.create_folder(name, current_user.id, parent_id)

    return success({
        'folder': folder.to_dict()
    }, message='文件夹创建成功')


@folder_bp.route('/<int:folder_id>', methods=['GET'])
@login_required_json
@active_required
def get_folder(folder_id):
    """
    获取文件夹详情
    GET /api/folder/<folder_id>
    """
    folder = Folder.query.get_or_404(folder_id)

    # 权限检查
    if not check_folder_permission(current_user.id, folder_id):
        return error(message='没有权限访问该文件夹', code=403)

    return success({
        'folder': folder.to_dict(include_children=True)
    })


@folder_bp.route('/<int:folder_id>', methods=['PUT'])
@login_required_json
@active_required
def update_folder(folder_id):
    """
    修改文件夹
    PUT /api/folder/<folder_id>

    请求体:
    {
        "name": "新文件夹名称"
    }
    """
    folder = Folder.query.get_or_404(folder_id)

    # 权限检查
    if folder.user_id != current_user.id and not current_user.is_admin():
        return error(message='没有权限修改该文件夹', code=403)

    data = request.get_json()

    if not data:
        return bad_request('请求参数不能为空')

    # 修改名称
    if 'name' in data:
        name = data.get('name', '').strip()

        if not name:
            return bad_request('文件夹名称不能为空')

        # 检查同级文件夹是否已存在同名
        existing = Folder.query.filter(
            Folder.id != folder_id,
            Folder.user_id == current_user.id,
            Folder.parent_id == folder.parent_id,
            Folder.name == name
        ).first()

        if existing:
            return bad_request('该文件夹下已存在同名文件夹')

        folder.name = name
        folder.update_path()

    db.session.commit()

    return success({
        'folder': folder.to_dict()
    }, message='文件夹修改成功')


@folder_bp.route('/<int:folder_id>', methods=['DELETE'])
@login_required_json
@active_required
def delete_folder(folder_id):
    """
    删除文件夹（级联软删除，移入回收站）
    DELETE /api/folder/<folder_id>

    会同时软删除文件夹下的所有子文件夹和文件，可在回收站整体恢复。
    """
    folder = Folder.query.get_or_404(folder_id)

    # 权限检查
    if folder.user_id != current_user.id and not current_user.is_admin():
        return error(message='没有权限删除该文件夹', code=403)

    # 已在回收站中则不允许重复删除
    if folder.is_deleted == 1:
        return bad_request('该文件夹已在回收站中')

    # 级联软删除（文件夹 + 子孙文件夹 + 内部文件）
    folder.soft_delete()

    # 记录日志
    Log.create_log(
        user_id=current_user.id,
        action='delete',
        module='folder',
        description=f'删除文件夹（移入回收站）: {folder.name}',
        ip_address=request.remote_addr
    )

    return success(message='文件夹已移入回收站')


@folder_bp.route('/move', methods=['POST'])
@login_required_json
@active_required
def move_folder():
    """
    移动文件夹
    POST /api/folder/move

    请求体:
    {
        "folder_id": "文件夹ID",
        "target_id": "目标文件夹ID"
    }
    """
    data = request.get_json()

    if not data or not data.get('folder_id') or data.get('target_id') is None:
        return bad_request('文件夹ID和目标文件夹ID不能为空')

    folder_id = data.get('folder_id')
    target_id = data.get('target_id')

    # 获取文件夹
    folder = Folder.query.get_or_404(folder_id)

    # 权限检查
    if folder.user_id != current_user.id and not current_user.is_admin():
        return error(message='没有权限移动该文件夹', code=403)

    # 不能移动到自身或其子目录
    if target_id == folder_id:
        return bad_request('不能将文件夹移动到自身')

    # 检查目标文件夹
    if target_id != 0:
        target = Folder.query.filter_by(id=target_id).first()
        if not target:
            return not_found('目标文件夹不存在')

        if target.user_id != current_user.id:
            return bad_request('只能移动到当前用户的目录下')

        # 检查是否是子目录
        current = target
        while current.parent_id != 0:
            if current.parent_id == folder_id:
                return bad_request('不能将文件夹移动到其子目录')
            current = Folder.query.filter_by(id=current.parent_id).first()

    # 移动文件夹
    folder.parent_id = target_id
    folder.update_path()

    db.session.commit()

    return success({
        'folder': folder.to_dict()
    }, message='文件夹移动成功')


@folder_bp.route('/<int:folder_id>/files', methods=['GET'])
@login_required_json
@active_required
def get_folder_files(folder_id):
    """
    获取文件夹下的文档列表
    GET /api/folder/<folder_id>/files
    """
    folder = Folder.query.get_or_404(folder_id)

    # 权限检查
    if not check_folder_permission(current_user.id, folder_id):
        return error(message='没有权限访问该文件夹', code=403)

    # 获取文档列表
    files = File.get_files_by_folder(folder_id, user_id=current_user.id)

    return success({
        'files': [file.to_dict() for file in files],
        'folder': folder.to_dict()
    })


@folder_bp.route('/breadcrumb/<int:folder_id>', methods=['GET'])
@login_required_json
@active_required
def get_folder_breadcrumb(folder_id):
    """
    获取文件夹面包屑导航
    GET /api/folder/breadcrumb/<folder_id>
    """
    folder = Folder.query.get_or_404(folder_id)

    # 权限检查
    if not check_folder_permission(current_user.id, folder_id):
        return error(message='没有权限访问该文件夹', code=403)

    # 获取祖先文件夹
    ancestors = folder.get_ancestors()

    return success({
        'breadcrumb': [f.to_dict() for f in ancestors] + [folder.to_dict()]
    })
