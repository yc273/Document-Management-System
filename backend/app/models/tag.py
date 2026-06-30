"""
标签模型
"""
from datetime import datetime

from app.extensions import db


class Tag(db.Model):
    """
    标签表模型
    """
    __tablename__ = 'doc_tag'

    # ========== 基础字段 ==========
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='标签ID')
    name = db.Column(db.String(50), nullable=False, comment='标签名称')
    color = db.Column(db.String(20), nullable=False, default='#409EFF', comment='标签颜色')
    user_id = db.Column(db.Integer, db.ForeignKey('sys_user.id'), nullable=False, comment='所属用户')

    # ========== 统计字段 ==========
    use_count = db.Column(db.Integer, nullable=False, default=0, comment='使用次数')

    # ========== 时间字段 ==========
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')

    # ========== 关系字段 ==========
    # 文档关系（多对多，通过doc_file_tag表）

    def __repr__(self):
        return f'<Tag {self.name}>'

    def to_dict(self):
        """
        序列化为字典

        Returns:
            dict: 标签信息
        """
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'user_id': self.user_id,
            'use_count': self.use_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def increment_use_count(self):
        """
        增加使用次数
        """
        self.use_count += 1
        db.session.commit()

    def decrement_use_count(self):
        """
        减少使用次数
        """
        if self.use_count > 0:
            self.use_count -= 1
            db.session.commit()

    def get_files(self):
        """
        获取使用该标签的文档

        Returns:
            list: 文档列表
        """
        return self.files.all()

    @staticmethod
    def create_tag(name, user_id, color='#409EFF'):
        """
        创建标签

        Args:
            name: 标签名称
            user_id: 用户ID
            color: 标签颜色

        Returns:
            Tag: 标签实例
        """
        # 检查是否已存在同名标签
        existing_tag = Tag.query.filter_by(name=name, user_id=user_id).first()
        if existing_tag:
            return existing_tag

        tag = Tag(
            name=name,
            user_id=user_id,
            color=color
        )

        db.session.add(tag)
        db.session.commit()

        return tag

    @staticmethod
    def get_tags_by_user(user_id):
        """
        获取用户的标签列表

        Args:
            user_id: 用户ID

        Returns:
            list: 标签列表
        """
        return Tag.query.filter_by(user_id=user_id).order_by(Tag.use_count.desc()).all()

    @staticmethod
    def get_popular_tags(user_id, limit=10):
        """
        获取热门标签

        Args:
            user_id: 用户ID
            limit: 数量限制

        Returns:
            list: 热门标签列表
        """
        return Tag.query.filter_by(user_id=user_id).order_by(Tag.use_count.desc()).limit(limit).all()
