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
            File or None: 如果存在重复文件则返回，否则返回None
        """
        from app.models.file import File

        # 查找用户已有的相同文件
        existing_file = File.query.filter_by(
            user_id=user_id,
            file_hash=file_hash,
            is_deleted=0
        ).first()

        if existing_file:
            # 复制文件记录（不同文件夹）
            from app.models import db
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

            return new_file

        return None
