"""
文档标签关联表模型
"""
from datetime import datetime

from app.extensions import db


class FileTag(db.Model):
    """
    文档标签关联表模型（多对多关系）
    """
    __tablename__ = 'doc_file_tag'

    # ========== 基础字段 ==========
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='ID')
    file_id = db.Column(db.Integer, db.ForeignKey('doc_file.id', ondelete='CASCADE'), nullable=False, comment='文档ID')
    tag_id = db.Column(db.Integer, db.ForeignKey('doc_tag.id', ondelete='CASCADE'), nullable=False, comment='标签ID')

    # ========== 时间字段 ==========
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='关联时间')

    # ========== 唯一约束 ==========
    __table_args__ = (
        db.UniqueConstraint('file_id', 'tag_id', name='uk_file_tag'),
    )

    def __repr__(self):
        return f'<FileTag file:{self.file_id} tag:{self.tag_id}>'

    def to_dict(self):
        """
        序列化为字典

        Returns:
            dict: 关联信息
        """
        return {
            'id': self.id,
            'file_id': self.file_id,
            'tag_id': self.tag_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    @staticmethod
    def add_file_tag(file_id, tag_id):
        """
        添加文档标签关联

        Args:
            file_id: 文档ID
            tag_id: 标签ID

        Returns:
            FileTag: 关联实例
        """
        # 检查是否已存在
        existing = FileTag.query.filter_by(file_id=file_id, tag_id=tag_id).first()
        if existing:
            return existing

        file_tag = FileTag(
            file_id=file_id,
            tag_id=tag_id
        )

        db.session.add(file_tag)

        # 增加标签使用次数
        from app.models.tag import Tag
        tag = Tag.query.get(tag_id)
        if tag:
            tag.increment_use_count()

        db.session.commit()

        return file_tag

    @staticmethod
    def remove_file_tag(file_id, tag_id):
        """
        移除文档标签关联

        Args:
            file_id: 文档ID
            tag_id: 标签ID
        """
        file_tag = FileTag.query.filter_by(file_id=file_id, tag_id=tag_id).first()
        if file_tag:
            # 减少标签使用次数
            from app.models.tag import Tag
            tag = Tag.query.get(tag_id)
            if tag:
                tag.decrement_use_count()

            db.session.delete(file_tag)
            db.session.commit()

    @staticmethod
    def get_file_tags(file_id):
        """
        获取文档的所有标签

        Args:
            file_id: 文档ID

        Returns:
            list: 标签列表
        """
        from app.models.tag import Tag
        file_tags = FileTag.query.filter_by(file_id=file_id).all()
        return [Tag.query.get(ft.tag_id) for ft in file_tags]

    @staticmethod
    def get_tag_files(tag_id):
        """
        获取使用某标签的所有文档

        Args:
            tag_id: 标签ID

        Returns:
            list: 文档列表
        """
        from app.models.file import File
        file_tags = FileTag.query.filter_by(tag_id=tag_id).all()
        return [File.query.get(ft.file_id) for ft in file_tags]

    @staticmethod
    def batch_add_file_tags(file_id, tag_ids):
        """
        批量添加文档标签关联

        Args:
            file_id: 文档ID
            tag_ids: 标签ID列表
        """
        for tag_id in tag_ids:
            FileTag.add_file_tag(file_id, tag_id)

    @staticmethod
    def clear_file_tags(file_id):
        """
        清除文档的所有标签

        Args:
            file_id: 文档ID
        """
        file_tags = FileTag.query.filter_by(file_id=file_id).all()

        for ft in file_tags:
            # 减少标签使用次数
            from app.models.tag import Tag
            tag = Tag.query.get(ft.tag_id)
            if tag:
                tag.decrement_use_count()

            db.session.delete(ft)

        db.session.commit()
