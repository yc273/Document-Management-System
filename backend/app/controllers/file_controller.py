"""
文档管理控制器
处理文档上传、下载、删除、移动等操作
"""
import os
import io
import zipfile
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import current_user, login_required
from werkzeug.datastructures import FileStorage

from app.extensions import db
from app.models.file import File
from app.models.folder import Folder
from app.models.log import Log
from app.utils.decorators import login_required_json, active_required, admin_required
from app.utils.response import success, error, bad_request, not_found
from app.utils.decorators import check_file_permission, check_folder_permission
from app.services.upload_service import UploadService

# 创建蓝图
file_bp = Blueprint('file', __name__)


@file_bp.route('/upload', methods=['POST'])
@login_required_json
@active_required
def upload_file():
    """
    上传文档
    POST /api/file/upload

    请求体: multipart/form-data
    {
        "file": 文件,
        "folder_id": 文件夹ID（可选）
    }
    """
    # 检查文件
    if 'file' not in request.files:
        return bad_request('请选择文件')

    file = request.files['file']
    folder_id = request.form.get('folder_id', 0)

    try:
        folder_id = int(folder_id)
    except:
        folder_id = 0

    # 验证文件
    is_valid, error_msg = UploadService.validate_file(file)
    if not is_valid:
        return bad_request(error_msg)

    # 检查文件夹权限
    if folder_id != 0:
        if not check_folder_permission(current_user.id, folder_id):
            return error(message='没有权限访问该文件夹', code=403)

        folder = Folder.query.filter_by(id=folder_id).first()
        if not folder:
            return not_found('文件夹不存在')

    # 先保存文件到临时位置获取哈希
    import tempfile
    import shutil

    temp_fd, temp_path = tempfile.mkstemp()
    try:
        # 保存到临时文件
        file.seek(0)
        with os.fdopen(temp_fd, 'wb') as temp_file:
            shutil.copyfileobj(file.stream, temp_file)

        # 计算哈希
        from app.utils.file_util import get_file_hash
        file_hash = get_file_hash(temp_path)

        # 检查重复文件（秒传）
        duplicate = UploadService.handle_duplicate_file(file_hash, current_user.id, folder_id)
        if duplicate['status'] == 'exists':
            # 同一文件夹内已存在相同文件，拒绝重复上传
            os.remove(temp_path)
            return error(message='已有相同文件，请勿重复上传', code=400)

        if duplicate['status'] == 'created':
            # 秒传成功（跨文件夹复制）
            os.remove(temp_path)

            # 记录日志
            Log.create_log(
                user_id=current_user.id,
                action='upload',
                module='file',
                description=f'秒传文档: {duplicate["file"].original_name}',
                ip_address=request.remote_addr
            )

            return success({
                'file': duplicate['file'].to_dict(),
                'duplicate': True
            }, message='文档上传成功（秒传）')

        # 检查存储空间
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        has_space, storage_info = UploadService.check_storage_limit(current_user.id, file_size)
        if not has_space:
            return error(
                message=f'存储空间不足，可用空间：{storage_info["available"] / 1024 / 1024:.2f}MB',
                code=400,
                data=storage_info
            )

        # 保存文件（重置流位置，因为前面已读取到临时文件）
        file.seek(0)
        file_info = UploadService.save_file(file, current_user.id, folder_id)

        # 创建文档记录
        new_file = File.create_file(
            filename=file_info['filename'],
            original_name=file_info['original_name'],
            file_type=file_info['file_type'],
            file_size=file_info['file_size'],
            file_path=file_info['file_path'],
            user_id=current_user.id,
            folder_id=folder_id
        )

        # 记录日志
        Log.create_log(
            user_id=current_user.id,
            action='upload',
            module='file',
            description=f'上传文档: {file_info["original_name"]}',
            ip_address=request.remote_addr
        )

        return success({
            'file': new_file.to_dict()
        }, message='文档上传成功')

    finally:
        # 确保临时文件被删除
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass


@file_bp.route('/list', methods=['GET'])
@login_required_json
@active_required
def get_file_list():
    """
    获取文档列表
    GET /api/file/list

    参数:
    - folder_id: 文件夹ID（可选）
    - keyword: 搜索关键词（可选，传入后在当前文件夹及其所有子文件夹内按文件名模糊搜索）
    - page: 页码（可选）
    - per_page: 每页数量（可选）
    """
    folder_id = request.args.get('folder_id', 0, type=int)
    keyword = request.args.get('keyword', '', type=str).strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 检查文件夹权限
    if folder_id != 0:
        if not check_folder_permission(current_user.id, folder_id):
            return error(message='没有权限访问该文件夹', code=403)

    # 基础查询：当前用户的未删除文档
    query = File.query.filter_by(user_id=current_user.id, is_deleted=0)

    if keyword:
        # 关键词搜索：范围 = 当前文件夹 + 其所有子孙文件夹
        # 用 BFS 收集当前文件夹下的全部子文件夹 ID
        folder_ids = [folder_id] if folder_id != 0 else []
        if folder_id != 0:
            queue = [folder_id]
            while queue:
                current_fid = queue.pop(0)
                child_ids = [f.id for f in Folder.query.filter_by(parent_id=current_fid).all()]
                folder_ids.extend(child_ids)
                queue.extend(child_ids)
        # 只按原始文件名（用户可见的名字）模糊匹配
        # 注意：filename 是系统生成的存储名（含时间戳/UUID），不应参与搜索
        like = f'%{keyword}%'
        query = query.filter(File.original_name.like(like))
        if folder_id != 0:
            query = query.filter(File.folder_id.in_(folder_ids))
    else:
        # 无关键词：仅显示当前文件夹下的文档
        query = query.filter_by(folder_id=folder_id)

    # 分页
    pagination = query.order_by(File.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return success({
        'files': [file.to_dict() for file in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@file_bp.route('/<int:file_id>', methods=['GET'])
@login_required_json
@active_required
def get_file(file_id):
    """
    获取文档详情
    GET /api/file/<file_id>
    """
    file = File.query.get_or_404(file_id)

    # 权限检查
    if not check_file_permission(current_user.id, file_id):
        return error(message='没有权限访问该文档', code=403)

    # 增加查看次数
    file.increment_view()

    return success({
        'file': file.to_dict()
    })


@file_bp.route('/<int:file_id>', methods=['PUT'])
@login_required_json
@active_required
def update_file(file_id):
    """
    修改文档信息
    PUT /api/file/<file_id>

    请求体:
    {
        "original_name": "新文件名",
        "folder_id": "新文件夹ID"
    }
    """
    file = File.query.get_or_404(file_id)

    # 权限检查
    if file.user_id != current_user.id and not current_user.is_admin():
        return error(message='没有权限修改该文档', code=403)

    data = request.get_json()

    if not data:
        return bad_request('请求参数不能为空')

    # 修改文件名（支持 original_name 和 filename 两种字段名）
    if 'original_name' in data:
        original_name = data.get('original_name', '').strip()
        if original_name:
            file.original_name = original_name
            # 同时更新 filename，保持扩展名一致
            if '.' in original_name:
                file.filename = original_name
            else:
                # 保持原有扩展名
                old_ext = file.filename.split('.')[-1] if '.' in file.filename else ''
                file.filename = f"{original_name}.{old_ext}" if old_ext else original_name

    if 'filename' in data:
        filename = data.get('filename', '').strip()
        if filename:
            file.filename = filename

    # 移动文件夹
    if 'folder_id' in data:
        folder_id = data.get('folder_id')

        # 检查文件夹权限
        if folder_id != 0:
            if not check_folder_permission(current_user.id, folder_id):
                return error(message='没有权限访问目标文件夹', code=403)

        file.folder_id = folder_id

    db.session.commit()

    # 记录日志
    Log.create_log(
        user_id=current_user.id,
        action='update',
        module='file',
        description=f'修改文档: {file.original_name}',
        ip_address=request.remote_addr
    )

    return success({
        'file': file.to_dict()
    }, message='文档信息修改成功')


@file_bp.route('/<int:file_id>', methods=['DELETE'])
@login_required_json
@active_required
def delete_file(file_id):
    """
    删除文档（移入回收站）
    DELETE /api/file/<file_id>
    """
    file = File.query.get_or_404(file_id)

    # 权限检查
    if file.user_id != current_user.id and not current_user.is_admin():
        return error(message='没有权限删除该文档', code=403)

    # 软删除
    file.soft_delete()

    # 记录日志
    Log.create_log(
        user_id=current_user.id,
        action='delete',
        module='file',
        description=f'删除文档: {file.original_name}',
        ip_address=request.remote_addr
    )

    return success(message='文档已移入回收站')


@file_bp.route('/move', methods=['POST'])
@login_required_json
@active_required
def move_file():
    """
    移动文档
    POST /api/file/move

    请求体:
    {
        "file_ids": [文档ID列表],
        "target_folder_id": 目标文件夹ID
    }
    """
    data = request.get_json()

    if not data or not data.get('file_ids') or data.get('target_folder_id') is None:
        return bad_request('文档ID列表和目标文件夹ID不能为空')

    file_ids = data.get('file_ids', [])
    target_folder_id = data.get('target_folder_id')

    # 检查目标文件夹权限
    if target_folder_id != 0:
        if not check_folder_permission(current_user.id, target_folder_id):
            return error(message='没有权限访问目标文件夹', code=403)

    # 移动文档
    moved_count = 0
    for file_id in file_ids:
        file = File.query.filter_by(id=file_id).first()
        if file and file.user_id == current_user.id:
            file.folder_id = target_folder_id
            moved_count += 1

    db.session.commit()

    # 记录日志
    Log.create_log(
        user_id=current_user.id,
        action='move',
        module='file',
        description=f'移动{moved_count}个文档',
        ip_address=request.remote_addr
    )

    return success({
        'moved_count': moved_count
    }, message=f'成功移动{moved_count}个文档')


@file_bp.route('/download/<int:file_id>', methods=['GET'])
@login_required
def download_file(file_id):
    """
    下载文档
    GET /api/file/download/<file_id>
    """
    file = File.query.get_or_404(file_id)

    # 权限检查
    if not check_file_permission(current_user.id, file_id):
        return error(message='没有权限下载该文档', code=403)

    # 检查文件是否存在
    if not os.path.exists(file.file_path):
        return not_found('文件不存在')

    # 增加下载次数
    file.increment_download()

    # 记录日志
    Log.create_log(
        user_id=current_user.id,
        action='download',
        module='file',
        description=f'下载文档: {file.original_name}',
        ip_address=request.remote_addr
    )

    # 返回文件
    return send_file(
        file.file_path,
        as_attachment=True,
        download_name=file.original_name
    )


@file_bp.route('/preview/<int:file_id>', methods=['GET'])
@login_required
def preview_file(file_id):
    """
    预览文档
    GET /api/file/preview/<file_id>
    """
    file = File.query.get_or_404(file_id)

    # 权限检查
    if not check_file_permission(current_user.id, file_id):
        return error(message='没有权限预览该文档', code=403)

    # 检查文件是否存在
    if not os.path.exists(file.file_path):
        return not_found('文件不存在')

    # 增加查看次数
    file.increment_view()

    # 根据文件类型返回
    if file.file_type == 'image':
        # 图片直接返回
        return send_file(file.file_path)
    elif file.file_type == 'pdf':
        # PDF文件
        return send_file(file.file_path, mimetype='application/pdf')
    elif file.file_type == 'video':
        # 视频流式播放
        return send_file(file.file_path, mimetype='video/mp4')
    elif file.file_type == 'audio':
        # 音频流式播放
        return send_file(file.file_path, mimetype='audio/mpeg')
    elif file.file_type == 'text':
        # 文本文件以UTF-8返回
        return send_file(file.file_path, mimetype='text/plain; charset=utf-8')
    else:
        # 其他类型：以原始方式返回但不强制下载，让浏览器自行处理
        return send_file(file.file_path)


@file_bp.route('/search', methods=['POST'])
@login_required_json
@active_required
def search_files():
    """
    搜索文档
    POST /api/file/search

    请求体:
    {
        "keyword": "关键词",
        "file_type": "文件类型（可选）"
    }
    """
    data = request.get_json()

    if not data or not data.get('keyword'):
        return bad_request('搜索关键词不能为空')

    keyword = data.get('keyword', '').strip()
    file_type = data.get('file_type', '').strip()

    # 搜索文档
    files = File.search_files(keyword, current_user.id, file_type if file_type else None)

    return success({
        'files': [file.to_dict() for file in files],
        'total': len(files)
    })


@file_bp.route('/batch-delete', methods=['POST'])
@login_required_json
@active_required
def batch_delete_files():
    """
    批量删除文档
    POST /api/file/batch-delete

    请求体:
    {
        "file_ids": [文档ID列表]
    }
    """
    data = request.get_json()

    if not data or not data.get('file_ids'):
        return bad_request('文档ID列表不能为空')

    file_ids = data.get('file_ids', [])

    # 批量删除
    deleted_count = 0
    for file_id in file_ids:
        file = File.query.filter_by(id=file_id).first()
        if file and file.user_id == current_user.id:
            file.soft_delete()
            deleted_count += 1

    db.session.commit()

    # 记录日志
    Log.create_log(
        user_id=current_user.id,
        action='batch_delete',
        module='file',
        description=f'批量删除{deleted_count}个文档',
        ip_address=request.remote_addr
    )

    return success({
        'deleted_count': deleted_count
    }, message=f'成功删除{deleted_count}个文档')


@file_bp.route('/batch-download', methods=['POST'])
@login_required_json
@active_required
def batch_download_files():
    """
    批量下载文档（打包为ZIP）
    POST /api/file/batch-download

    请求体:
    {
        "file_ids": [文档ID列表]
    }
    """
    data = request.get_json() or {}

    if not data.get('file_ids'):
        return bad_request('文档ID列表不能为空')

    file_ids = data.get('file_ids', [])

    # 收集可下载的文件（权限+存在性校验）
    files_to_zip = []
    for file_id in file_ids:
        file = File.query.filter_by(id=file_id, is_deleted=0).first()
        if file and file.user_id == current_user.id and file.file_path and os.path.exists(file.file_path):
            files_to_zip.append(file)
            # 增加下载次数
            file.increment_download()

    if not files_to_zip:
        return error(message='没有可下载的文件', code=404)

    # 在内存中打包ZIP
    memory_zip = io.BytesIO()
    used_names = {}  # 用于处理ZIP内同名文件

    with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in files_to_zip:
            name = file.original_name or file.filename
            # 处理重名：若ZIP内已有同名，追加 (1)、(2)...
            if name in used_names:
                used_names[name] += 1
                base, ext = os.path.splitext(name)
                name = f'{base} ({used_names[name]}){ext}'
            else:
                used_names[name] = 0
            zf.write(file.file_path, arcname=name)

    memory_zip.seek(0)

    # 记录日志
    Log.create_log(
        user_id=current_user.id,
        action='batch_download',
        module='file',
        description=f'批量下载{len(files_to_zip)}个文档',
        ip_address=request.remote_addr
    )

    # 流式返回ZIP（显式提供文件大小，避免浏览器无法触发下载）
    zip_data = memory_zip.getvalue()
    response = send_file(
        io.BytesIO(zip_data),
        mimetype='application/zip',
        as_attachment=True,
        download_name='batch_download.zip'
    )
    response.headers['Content-Length'] = len(zip_data)
    return response


# ==================== 分片上传 ====================

@file_bp.route('/upload/check', methods=['POST'])
@login_required_json
@active_required
def check_chunk_upload():
    """
    分片上传前检查（秒传 + 断点续传）
    POST /api/file/upload/check

    请求体:
    {
        "file_hash": "文件MD5",
        "file_size": 文件大小,
        "filename": "文件名",
        "folder_id": 文件夹ID
    }

    返回:
    - skip: 秒传成功（用户已有同hash文件）
    - resume: 断点续传（返回已上传的分片序号列表）
    - fresh: 全新上传
    """
    data = request.get_json() or {}
    file_hash = data.get('file_hash', '').strip()
    file_size = data.get('file_size', 0)
    filename = data.get('filename', '')
    folder_id = data.get('folder_id', 0) or 0

    if not file_hash or not filename:
        return bad_request('file_hash 和 filename 不能为空')

    # 1. 秒传检测
    dup = UploadService.handle_duplicate_file(file_hash, current_user.id, folder_id)
    if dup['status'] in ('exists', 'created'):
        return success({
            'status': 'skip',
            'file': dup['file'].to_dict(),
            'message': '文件秒传成功'
        })

    # 2. 断点续传检测：检查临时分片目录
    upload_temp = current_app.config['UPLOAD_TEMP']
    chunk_dir = os.path.join(upload_temp, file_hash)
    uploaded_chunks = []
    if os.path.exists(chunk_dir):
        for f_name in os.listdir(chunk_dir):
            if f_name.startswith('chunk_'):
                try:
                    uploaded_chunks.append(int(f_name.split('_')[1]))
                except (ValueError, IndexError):
                    pass
        uploaded_chunks.sort()

    if uploaded_chunks:
        return success({
            'status': 'resume',
            'uploaded_chunks': uploaded_chunks,
            'message': '可断点续传'
        })

    # 3. 全新上传：检查存储空间
    is_enough, storage_info = UploadService.check_storage_limit(current_user.id, file_size)
    if not is_enough:
        return error(message='存储空间不足', code=400)

    return success({
        'status': 'fresh',
        'message': '可以开始上传'
    })


@file_bp.route('/upload/chunk', methods=['POST'])
@login_required_json
@active_required
def upload_chunk():
    """
    上传单个分片
    POST /api/file/upload/chunk

    表单数据:
    - file: 分片二进制数据
    - file_hash: 文件MD5（分片目录标识）
    - chunk_index: 当前分片序号（从0开始）
    - total_chunks: 总分片数
    """
    chunk = request.files.get('file')
    file_hash = request.form.get('file_hash', '').strip()
    chunk_index = request.form.get('chunk_index', type=int)
    total_chunks = request.form.get('total_chunks', type=int)

    if not chunk or not file_hash or chunk_index is None:
        return bad_request('缺少必要参数（file, file_hash, chunk_index）')

    # 存储分片到临时目录 {UPLOAD_TEMP}/{file_hash}/chunk_{index}
    chunk_dir = os.path.join(current_app.config['UPLOAD_TEMP'], file_hash)
    if not os.path.exists(chunk_dir):
        os.makedirs(chunk_dir)

    chunk_path = os.path.join(chunk_dir, f'chunk_{chunk_index}')
    chunk.save(chunk_path)

    return success({
        'chunk_index': chunk_index,
        'total_chunks': total_chunks,
        'message': f'分片 {chunk_index} 上传成功'
    })


@file_bp.route('/upload/merge', methods=['POST'])
@login_required_json
@active_required
def merge_chunks():
    """
    合并分片，完成上传
    POST /api/file/upload/merge

    请求体:
    {
        "file_hash": "文件MD5",
        "filename": "原始文件名",
        "file_size": 文件总大小,
        "folder_id": 文件夹ID
    }
    """
    data = request.get_json() or {}
    file_hash = data.get('file_hash', '').strip()
    filename = data.get('filename', '').strip()
    file_size = data.get('file_size', 0)
    folder_id = data.get('folder_id', 0) or 0

    if not file_hash or not filename:
        return bad_request('file_hash 和 filename 不能为空')

    # 文件夹权限检查
    if folder_id != 0:
        if not check_folder_permission(current_user.id, folder_id):
            return error(message='没有权限访问该文件夹', code=403)

    # 合并分片
    result = UploadService.merge_chunks(
        file_hash=file_hash,
        original_filename=filename,
        total_size=file_size,
        user_id=current_user.id,
        folder_id=folder_id
    )

    status = result.get('status')
    if status == 'error':
        return error(message=result.get('message', '合并失败'), code=400)

    # 记录日志
    Log.create_log(
        user_id=current_user.id,
        action='upload',
        module='file',
        description=f'分片上传文档: {filename}',
        ip_address=request.remote_addr
    )

    return success({
        'file': result['file'].to_dict(),
        'upload_type': status  # success=新上传, exists/created=秒传
    }, message='上传成功')
