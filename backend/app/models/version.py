"""
版本模型
"""
from datetime import datetime

from app.extensions import db


class Version(db.Model):
    """
    文档版本表模型
    """
    __tablename__ = 'doc_version'

    # ========== 基础字段 ==========
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='版本ID')
    file_id = db.Column(db.Integer, db.ForeignKey('doc_file.id', ondelete='CASCADE'), nullable=False, index=True, comment='文档ID')
    version_number = db.Column(db.Integer, nullable=False, comment='版本号')
    file_path = db.Column(db.String(500), nullable=False, comment='文件路径')
    file_size = db.Column(db.Integer, nullable=False, comment='文件大小')

    # ========== 备注字段 ==========
    remark = db.Column(db.String(255), nullable=True, comment='版本说明')

    # ========== 创建信息 ==========
    created_by = db.Column(db.Integer, db.ForeignKey('sys_user.id'), nullable=False, comment='创建用户')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')

    # ========== 关系字段 ==========
    # 创建者关系
    creator = db.relationship('User', backref='versions', lazy='select')

    def __repr__(self):
        return f'<Version file:{self.file_id} v:{self.version_number}>'

    def to_dict(self):
        """
        序列化为字典

        Returns:
            dict: 版本信息
        """
        return {
            'id': self.id,
            'file_id': self.file_id,
            'version_number': self.version_number,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_size_readable': self.get_readable_size(),
            'remark': self.remark,
            'created_by': self.created_by,
            'created_by_name': self.creator.username if self.creator else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

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

    @staticmethod
    def create_version(file_id, file_path, file_size, created_by, remark=None):
        """
        创建新版本

        Args:
            file_id: 文档ID
            file_path: 文件路径
            file_size: 文件大小
            created_by: 创建用户ID
            remark: 版本说明

        Returns:
            Version: 版本实例
        """
        # 获取当前最大版本号
        max_version = db.session.query(db.func.max(Version.version_number)).filter_by(file_id=file_id).scalar()
        next_version = (max_version or 0) + 1

        version = Version(
            file_id=file_id,
            version_number=next_version,
            file_path=file_path,
            file_size=file_size,
            created_by=created_by,
            remark=remark
        )

        db.session.add(version)

        # 更新文档的当前版本号
        from app.models.file import File
        file = File.query.get(file_id)
        if file:
            file.version = next_version

        db.session.commit()

        return version

    @staticmethod
    def get_file_versions(file_id):
        """
        获取文档的所有版本

        Args:
            file_id: 文档ID

        Returns:
            list: 版本列表
        """
        return Version.query.filter_by(file_id=file_id).order_by(Version.version_number.desc()).all()

    @staticmethod
    def restore_version(file_id, version_number):
        """
        恢复到指定版本

        Args:
            file_id: 文档ID
            version_number: 版本号

        Returns:
            bool: 是否成功
        """
        import shutil
        import os

        # 获取指定版本
        version = Version.query.filter_by(file_id=file_id, version_number=version_number).first()
        if not version:
            return False

        # 获取当前文档
        from app.models.file import File
        file = File.query.get(file_id)
        if not file:
            return False

        # 备份当前版本
        backup_path = file.file_path + '.backup'
        if os.path.exists(file.file_path):
            shutil.copy2(file.file_path, backup_path)

        # 恢复文件
        if os.path.exists(version.file_path):
            shutil.copy2(version.file_path, file.file_path)

            # 更新文档信息
            file.file_size = version.file_size
            db.session.commit()

            return True

        return False

    @staticmethod
    def delete_old_versions(file_id, keep_count=5):
        """
        删除旧版本（保留最近N个版本）

        Args:
            file_id: 文档ID
            keep_count: 保留版本数量

        Returns:
            int: 删除的版本数量
        """
        import os

        # 获取所有版本，按版本号降序
        versions = Version.query.filter_by(file_id=file_id).order_by(Version.version_number.desc()).all()

        # 保留最近N个版本
        if len(versions) <= keep_count:
            return 0

        # 删除旧版本
        delete_count = 0
        for version in versions[keep_count:]:
            # 删除文件
            if os.path.exists(version.file_path):
                try:
                    os.remove(version.file_path)
                except:
                    pass

            # 删除数据库记录
            db.session.delete(version)
            delete_count += 1

        db.session.commit()

        return delete_count
