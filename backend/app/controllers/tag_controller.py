"""
标签管理控制器
处理标签的创建、修改、删除等操作
"""
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required

from app.extensions import db
from app.models.tag import Tag
from app.models.file_tag import FileTag
from app.utils.decorators import login_required_json, active_required
from app.utils.response import success, error, bad_request, not_found

# 创建蓝图
tag_bp = Blueprint('tag', __name__)


@tag_bp.route('/list', methods=['GET'])
@login_required_json
@active_required
def get_tag_list():
    """
    获取标签列表
    GET /api/tag/list
    """
    tags = Tag.get_tags_by_user(current_user.id)

    return success({
        'tags': [tag.to_dict() for tag in tags]
    })


@tag_bp.route('/', methods=['POST'])
@login_required_json
@active_required
def create_tag():
    """
    创建标签
    POST /api/tag

    请求体:
    {
        "name": "标签名称",
        "color": "标签颜色（可选）"
    }
    """
    data = request.get_json()

    if not data or not data.get('name'):
        return bad_request('标签名称不能为空')

    name = data.get('name', '').strip()
    color = data.get('color', '#409EFF').strip()

    if not name:
        return bad_request('标签名称不能为空')

    # 创建标签
    tag = Tag.create_tag(name, current_user.id, color)

    return success({
        'tag': tag.to_dict()
    }, message='标签创建成功')


@tag_bp.route('/<int:tag_id>', methods=['PUT'])
@login_required_json
@active_required
def update_tag(tag_id):
    """
    修改标签
    PUT /api/tag/<tag_id>

    请求体:
    {
        "name": "新标签名称",
        "color": "新颜色"
    }
    """
    tag = Tag.query.get_or_404(tag_id)

    # 权限检查
    if tag.user_id != current_user.id:
        return error(message='没有权限修改该标签', code=403)

    data = request.get_json()

    if not data:
        return bad_request('请求参数不能为空')

    # 修改名称
    if 'name' in data:
        name = data.get('name', '').strip()
        if name:
            # 检查是否已存在同名标签
            existing = Tag.query.filter(
                Tag.id != tag_id,
                Tag.user_id == current_user.id,
                Tag.name == name
            ).first()

            if existing:
                return bad_request('标签名称已存在')

            tag.name = name

    # 修改颜色
    if 'color' in data:
        color = data.get('color', '#409EFF').strip()
        tag.color = color

    db.session.commit()

    return success({
        'tag': tag.to_dict()
    }, message='标签修改成功')


@tag_bp.route('/<int:tag_id>', methods=['DELETE'])
@login_required_json
@active_required
def delete_tag(tag_id):
    """
    删除标签
    DELETE /api/tag/<tag_id>
    """
    tag = Tag.query.get_or_404(tag_id)

    # 权限检查
    if tag.user_id != current_user.id:
        return error(message='没有权限删除该标签', code=403)

    # 删除标签（会自动删除关联）
    db.session.delete(tag)
    db.session.commit()

    return success(message='标签删除成功')


@tag_bp.route('/file/<int:file_id>/tags', methods=['GET'])
@login_required_json
@active_required
def get_file_tags(file_id):
    """
    获取文档的所有标签
    GET /api/tag/file/<file_id>/tags
    """
    from app.models.file import File

    file = File.query.get_or_404(file_id)

    # 权限检查
    if file.user_id != current_user.id and not current_user.is_admin():
        return error(message='没有权限访问该文档', code=403)

    tags = FileTag.get_file_tags(file_id)

    return success({
        'tags': [tag.to_dict() for tag in tags if tag]
    })


@tag_bp.route('/file/<int:file_id>/tag', methods=['POST'])
@login_required_json
@active_required
def add_file_tag():
    """
    为文档添加标签
    POST /api/tag/file/<file_id>/tag

    请求体:
    {
        "file_id": 文档ID,
        "tag_id": 标签ID
    }
    """
    data = request.get_json()

    if not data or not data.get('file_id') or not data.get('tag_id'):
        return bad_request('文档ID和标签ID不能为空')

    file_id = data.get('file_id')
    tag_id = data.get('tag_id')

    # 检查权限
    from app.models.file import File
    file = File.query.get_or_404(file_id)

    if file.user_id != current_user.id:
        return error(message='没有权限修改该文档', code=403)

    # 检查标签
    tag = Tag.query.get_or_404(tag_id)

    if tag.user_id != current_user.id:
        return error(message='没有权限使用该标签', code=403)

    # 添加标签
    FileTag.add_file_tag(file_id, tag_id)

    return success(message='标签添加成功')


@tag_bp.route('/file/<int:file_id>/tag/<int:tag_id>', methods=['DELETE'])
@login_required_json
@active_required
def remove_file_tag(file_id, tag_id):
    """
    移除文档标签
    DELETE /api/tag/file/<file_id>/tag/<tag_id>
    """
    # 检查权限
    from app.models.file import File
    file = File.query.get_or_404(file_id)

    if file.user_id != current_user.id:
        return error(message='没有权限修改该文档', code=403)

    # 移除标签
    FileTag.remove_file_tag(file_id, tag_id)

    return success(message='标签移除成功')
