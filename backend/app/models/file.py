"""
文档模型
"""
import os
from datetime import datetime
import hashlib

from app.extensions import db


class File(db.Model):
    """
    文档表模型
    """
    __tablename__ = 'doc_file'

    # ========== 基础字段 ==========
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='文档ID')
    filename = db.Column(db.String(255), nullable=False, comment='文件名（含扩展名）')
    original_name = db.Column(db.String(255), nullable=False, comment='原始文件名')
    file_type = db.Column(db.String(20), nullable=False, index=True, comment='文件类型')
    file_size = db.Column(db.Integer, nullable=False, comment='文件大小（字节）')
    file_path = db.Column(db.String(500), nullable=False, comment='存储路径')
    file_hash = db.Column(db.String(64), nullable=True, index=True, comment='文件哈希值')

    # ========== 归属字段 ==========
    folder_id = db.Column(db.Integer, db.ForeignKey('doc_folder.id'), nullable=False, default=0, index=True, comment='所属文件夹ID（0为根目录）')
    user_id = db.Column(db.Integer, db.ForeignKey('sys_user.id'), nullable=False, index=True, comment='上传用户')

    # ========== 版本字段 ==========
    version = db.Column(db.Integer, nullable=False, default=1, comment='当前版本号')

    # ========== 统计字段 ==========
    download_count = db.Column(db.Integer, nullable=False, default=0, comment='下载次数')
    view_count = db.Column(db.Integer, nullable=False, default=0, comment='查看次数')

    # ========== 删除标记 ==========
    is_deleted = db.Column(db.Integer, nullable=False, default=0, index=True, comment='是否删除：1是 0否')
    deleted_at = db.Column(db.DateTime, nullable=True, comment='删除时间')

    # ========== 时间字段 ==========
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # ========== 关系字段 ==========
    # 标签关系
    tags = db.relationship('Tag', secondary='doc_file_tag', backref=db.backref('files', lazy='dynamic'), lazy='dynamic')
    # 版本关系
    versions = db.relationship('Version', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    # 分享关系
    shares = db.relationship('Share', back_populates='file', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<File {self.filename}>'

    def to_dict(self):
        """
        序列化为字典

        Returns:
            dict: 文档信息
        """
        data = {
            'id': self.id,
            'filename': self.filename,
            'original_name': self.original_name,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'file_size_readable': self.get_readable_size(),
            'file_path': self.file_path,
            'folder_id': self.folder_id,
            'user_id': self.user_id,
            'version': self.version,
            'download_count': self.download_count,
            'view_count': self.view_count,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'tags': [tag.to_dict() for tag in self.tags]
        }

        # 已删除文件附加：删除时间、剩余保留天数
        if self.is_deleted == 1:
            from config import Config
            retention_days = Config.TRASH_RETENTION_DAYS
            data['deleted_at'] = self.deleted_at.strftime('%Y-%m-%d %H:%M:%S') if self.deleted_at else None
            if self.deleted_at:
                # 剩余保留天数（不足1天按1天算，已过期为0）
                elapsed = (datetime.now() - self.deleted_at).total_seconds() / 86400
                remaining = int(retention_days - elapsed)
                data['expire_days'] = max(remaining, 0)
            else:
                data['expire_days'] = retention_days

        return data

    def get_readable_size(self):
        """
        获取可读的文件大小

        Returns:
            str: 可读的文件大小
        """
        size = self.file_size
        units = ['B', 'KB', 'MB', 'GB', 'TB']

        for unit in units:
            if size < 1024.0:
                return f'{round(size, 2)} {unit}'
            size /= 1024.0

        return f'{round(size, 2)} PB'

    def calculate_hash(self):
        """
        计算文件哈希值

        Returns:
            str: 文件哈希值
        """
        import os

        if not os.path.exists(self.file_path):
            return None

        md5 = hashlib.md5()
        with open(self.file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5.update(chunk)

        self.file_hash = md5.hexdigest()
        db.session.commit()

        return self.file_hash

    def increment_download(self):
        """
        增加下载次数
        """
        self.download_count += 1
        db.session.commit()

    def increment_view(self):
        """
        增加查看次数
        """
        self.view_count += 1
        db.session.commit()

    def soft_delete(self):
        """
        软删除（移入回收站）
        仅标记数据库记录为已删除，保留物理文件，以便恢复。
        物理文件在永久删除（permanently_delete）时才真正清除。
        """
        self.is_deleted = 1
        self.deleted_at = datetime.now()
        db.session.commit()

    def restore(self):
        """
        恢复文档
        """
        self.is_deleted = 0
        self.deleted_at = None
        db.session.commit()

    def add_tag(self, tag_id):
        """
        添加标签

        Args:
            tag_id: 标签ID
        """
        if tag_id not in [tag.id for tag in self.tags]:
            from app.models.file_tag import FileTag
            file_tag = FileTag(file_id=self.id, tag_id=tag_id)
            db.session.add(file_tag)
            db.session.commit()

    def remove_tag(self, tag_id):
        """
        移除标签

        Args:
            tag_id: 标签ID
        """
        from app.models.file_tag import FileTag
        file_tag = FileTag.query.filter_by(file_id=self.id, tag_id=tag_id).first()
        if file_tag:
            db.session.delete(file_tag)
            db.session.commit()

    @staticmethod
    def create_file(filename, original_name, file_type, file_size, file_path, user_id, folder_id=0, file_hash=None):
        """
        创建文档

        Args:
            filename: 文件名
            original_name: 原始文件名
            file_type: 文件类型
            file_size: 文件大小
            file_path: 文件路径
            user_id: 用户ID
            folder_id: 文件夹ID
            file_hash: 文件哈希值（可选，不传则自动计算）

        Returns:
            File: 文档实例
        """
        file = File(
            filename=filename,
            original_name=original_name,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            user_id=user_id,
            folder_id=folder_id,
            file_hash=file_hash
        )

        db.session.add(file)
        db.session.commit()

        # 若未传入 hash 则计算
        if not file_hash:
            file.calculate_hash()

        # 更新用户存储使用量
        from app.models.user import User
        user = User.query.get(user_id)
        if user:
            user.update_storage(file_size)

        return file

    @staticmethod
    def get_files_by_folder(folder_id, user_id=None, include_deleted=False):
        """
        获取文件夹下的文档

        Args:
            folder_id: 文件夹ID
            user_id: 用户ID（可选，用于权限检查）
            include_deleted: 是否包含已删除文档

        Returns:
            list: 文档列表
        """
        query = File.query.filter_by(folder_id=folder_id)

        if user_id:
            query = query.filter_by(user_id=user_id)

        if not include_deleted:
            query = query.filter_by(is_deleted=0)

        return query.order_by(File.created_at.desc()).all()

    @staticmethod
    def search_files(keyword, user_id=None, file_type=None):
        """
        搜索文档

        Args:
            keyword: 关键词
            user_id: 用户ID（可选）
            file_type: 文件类型（可选）

        Returns:
            list: 文档列表
        """
        query = File.query.filter(File.filename.like(f'%{keyword}%'))

        if user_id:
            query = query.filter_by(user_id=user_id)

        if file_type:
            query = query.filter_by(file_type=file_type)

        query = query.filter_by(is_deleted=0)

        return query.order_by(File.created_at.desc()).all()
