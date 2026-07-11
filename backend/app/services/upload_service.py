"""
文档上传服务
处理文档上传、验证、存储等逻辑
"""
import os
from werkzeug.utils import secure_filename
from flask import current_app

from app.utils.file_util import allowed_file, generate_filename, get_file_type, get_file_hash


class UploadService:
    """文档上传服务类"""

    @staticmethod
    def validate_file(file):
        """
        验证上传的文件

        Args:
            file: 上传的文件对象

        Returns:
            tuple: (is_valid, error_message)
        """
        # 检查文件是否存在
        if not file:
            return False, '未选择文件'

        # 检查文件名
        if file.filename == '':
            return False, '文件名为空'

        # 检查文件类型
        if not allowed_file(file.filename):
            return False, '不支持的文件类型'

        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # 重置指针

        max_size = current_app.config['MAX_CONTENT_LENGTH']
        if file_size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            return False, f'文件大小超过限制（最大{max_size_mb:.0f}MB）'

        return True, None

    @staticmethod
    def save_file(file, user_id, folder_id=0):
        """
        保存上传的文件

        Args:
            file: 上传的文件对象
            user_id: 用户ID
            folder_id: 文件夹ID

        Returns:
            dict: 文件信息字典
        """
        # 获取原始文件名
        original_filename = file.filename

        # 生成唯一文件名
        filename = generate_filename(original_filename, user_id)

        # 确定存储路径
        upload_folder = current_app.config['UPLOAD_DOCUMENTS']
        filepath = os.path.join(upload_folder, filename)

        # 保存文件
        file.save(filepath)

        # 获取文件信息
        file_size = os.path.getsize(filepath)
        file_type = get_file_type(original_filename)

        # 计算文件哈希
        file_hash = get_file_hash(filepath)

        return {
            'filename': filename,
            'original_name': original_filename,
            'file_type': file_type,
            'file_size': file_size,
            'file_path': filepath,
            'file_hash': file_hash
        }

    @staticmethod
    def delete_file(filepath):
        """
        删除文件

        Args:
            filepath: 文件路径

        Returns:
            bool: 是否成功
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f"删除文件失败: {e}")
            return False

    @staticmethod
    def copy_file(src_path, dst_path):
        """
        复制文件

        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径

        Returns:
            bool: 是否成功
        """
        try:
            import shutil
            shutil.copy2(src_path, dst_path)
            return True
        except Exception as e:
            print(f"复制文件失败: {e}")
            return False

    @staticmethod
    def check_storage_limit(user_id, file_size):
        """
        检查用户存储空间是否足够

        Args:
            user_id: 用户ID
            file_size: 文件大小

        Returns:
            tuple: (is_enough, storage_info)
        """
        from app.models.user import User

        user = User.query.get(user_id)
        if not user:
            return False, None

        # 检查存储空间
        available_space = user.storage_limit - user.storage_used

        if available_space < file_size:
            storage_info = user.get_storage_info()
            return False, storage_info

        return True, None

    @staticmethod
    def handle_duplicate_file(file_hash, user_id, folder_id=0):
        """
        处理重复文件（秒传）

        Args:
            file_hash: 文件哈希值
            user_id: 用户ID
            folder_id: 文件夹ID

        Returns:
            dict: 包含处理结果的字典
                {'status': 'exists', 'file': File}  —— 同一文件夹内已存在
                {'status': 'created', 'file': File} —— 秒传成功，跨文件夹复制
                {'status': 'none'}                   —— 无重复文件
        """
        from app.models.file import File

        # 查找用户已有的相同文件
        existing_file = File.query.filter_by(
            user_id=user_id,
            file_hash=file_hash,
            is_deleted=0
        ).first()

        if not existing_file:
            return {'status': 'none'}

        # 同一文件夹内已存在相同文件，不再重复上传
        same_folder = File.query.filter_by(
            user_id=user_id,
            file_hash=file_hash,
            folder_id=folder_id,
            is_deleted=0
        ).first()

        if same_folder:
            return {'status': 'exists', 'file': same_folder}

        # 不同文件夹：秒传，复制文件记录
        from app.extensions import db
        new_file = File(
            filename=existing_file.filename,
            original_name=existing_file.original_name,
            file_type=existing_file.file_type,
            file_size=existing_file.file_size,
            file_path=existing_file.file_path,
            folder_id=folder_id,
            user_id=user_id,
            file_hash=existing_file.file_hash,
            version=existing_file.version
        )
        db.session.add(new_file)
        db.session.commit()

        return {'status': 'created', 'file': new_file}

    @staticmethod
    def merge_chunks(file_hash, original_filename, total_size, user_id, folder_id=0):
        """
        合并分片上传的文件，完成最终存储和数据库记录创建。

        Args:
            file_hash: 文件唯一标识（分片目录名）
            original_filename: 原始文件名
            total_size: 文件总大小（字节）
            user_id: 用户ID
            folder_id: 目标文件夹ID

        Returns:
            dict: {'status': 'success'|'exists'|'created', 'file': File}
        """
        upload_temp = current_app.config['UPLOAD_TEMP']
        chunk_dir = os.path.join(upload_temp, file_hash)

        if not os.path.exists(chunk_dir):
            return {'status': 'error', 'message': '分片数据不存在'}

        # 检查存储空间
        is_enough, storage_info = UploadService.check_storage_limit(user_id, total_size)
        if not is_enough:
            return {'status': 'error', 'message': '存储空间不足'}

        # 1. 秒传检测：若用户已有同 hash 文件
        dup = UploadService.handle_duplicate_file(file_hash, user_id, folder_id)
        if dup['status'] in ('exists', 'created'):
            # 清理临时分片
            UploadService.cleanup_chunks(file_hash)
            return {'status': dup['status'], 'file': dup['file']}

        # 2. 合并分片到最终文件
        filename = generate_filename(original_filename, user_id)
        upload_folder = current_app.config['UPLOAD_DOCUMENTS']
        final_path = os.path.join(upload_folder, filename)

        # 按分片序号顺序合并
        chunk_files = [f for f in os.listdir(chunk_dir) if f.startswith('chunk_')]
        # 提取序号排序
        chunk_files.sort(key=lambda x: int(x.split('_')[1]))

        with open(final_path, 'wb') as fout:
            for chunk_name in chunk_files:
                chunk_path = os.path.join(chunk_dir, chunk_name)
                with open(chunk_path, 'rb') as fin:
                    while True:
                        data = fin.read(1024 * 1024)  # 1MB 缓冲
                        if not data:
                            break
                        fout.write(data)

        # 3. 校验合并后大小
        actual_size = os.path.getsize(final_path)
        if actual_size != total_size:
            # 大小不符，删除合并文件
            os.remove(final_path)
            UploadService.cleanup_chunks(file_hash)
            return {'status': 'error', 'message': f'文件大小校验失败（期望{total_size}，实际{actual_size}）'}

        # 4. 创建数据库记录（传入已知的 hash，避免重算）
        file_type = get_file_type(original_filename)
        from app.models.file import File
        file = File.create_file(
            filename=filename,
            original_name=original_filename,
            file_type=file_type,
            file_size=actual_size,
            file_path=final_path,
            user_id=user_id,
            folder_id=folder_id,
            file_hash=file_hash
        )

        # 5. 清理临时分片
        UploadService.cleanup_chunks(file_hash)

        return {'status': 'success', 'file': file}

    @staticmethod
    def cleanup_chunks(file_hash):
        """
        清理指定文件的临时分片目录。
        """
        import shutil
        upload_temp = current_app.config['UPLOAD_TEMP']
        chunk_dir = os.path.join(upload_temp, file_hash)
        try:
            if os.path.exists(chunk_dir):
                shutil.rmtree(chunk_dir)
        except Exception as e:
            print(f"清理分片失败: {e}")
