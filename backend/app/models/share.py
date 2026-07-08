"""
分享模型
"""
from datetime import datetime, timedelta
import string
import random

from app.extensions import db


class Share(db.Model):
    """
    文档分享表模型
    """
    __tablename__ = 'doc_share'

    # ========== 基础字段 ==========
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='分享ID')
    share_code = db.Column(db.String(32), unique=True, nullable=False, index=True, comment='分享码')
    file_id = db.Column(db.Integer, db.ForeignKey('doc_file.id', ondelete='CASCADE'), nullable=False, comment='文档ID')

    # ========== 安全字段 ==========
    share_password = db.Column(db.String(50), nullable=True, comment='分享密码')

    # ========== 有效期字段 ==========
    expire_days = db.Column(db.Integer, nullable=False, default=0, comment='有效天数（0为永久）')
    expire_time = db.Column(db.DateTime, nullable=True, comment='过期时间')

    # ========== 统计字段 ==========
    view_count = db.Column(db.Integer, nullable=False, default=0, comment='查看次数')
    download_count = db.Column(db.Integer, nullable=False, default=0, comment='下载次数')

    # ========== 创建信息 ==========
    created_by = db.Column(db.Integer, db.ForeignKey('sys_user.id'), nullable=False, comment='创建用户')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')

    # ========== 关系字段 ==========
    # 创建者关系
    creator = db.relationship('User', backref='shares', lazy='select')
    # 文件关系
    file = db.relationship('File', backref='shares', lazy='select')

    def __repr__(self):
        return f'<Share {self.share_code}>'

    def to_dict(self, include_file=False):
        """
        序列化为字典

        Args:
            include_file: 是否包含文件信息

        Returns:
            dict: 分享信息
        """
        data = {
            'id': self.id,
            'share_code': self.share_code,
            'file_id': self.file_id,
            'has_password': self.share_password is not None,
            'expire_days': self.expire_days,
            'expire_time': self.expire_time.strftime('%Y-%m-%d %H:%M:%S') if self.expire_time else None,
            'view_count': self.view_count,
            'download_count': self.download_count,
            'created_by': self.created_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'is_expired': self.is_expired()
        }

        # 如果需要文件信息且文件存在
        if include_file and self.file:
            data['file_name'] = self.file.original_name
            data['file_size'] = self.file.file_size
            data['file_size_readable'] = f"{self.file.file_size / 1024 / 1024:.2f}MB"
            data['file_type'] = self.file.file_type
            data['nickname'] = self.creator.nickname if self.creator else '用户'

        return data

    def is_expired(self):
        """
        是否已过期

        Returns:
            bool: 是否已过期
        """
        if self.expire_time is None:
            return False

        return datetime.now() > self.expire_time

    def verify_password(self, password):
        """
        验证密码

        Args:
            password: 密码

        Returns:
            bool: 密码是否正确
        """
        if self.share_password is None:
            return True

        return self.share_password == password

    def increment_view(self):
        """
        增加查看次数
        """
        self.view_count += 1
        db.session.commit()

    def increment_download(self):
        """
        增加下载次数
        """
        self.download_count += 1
        db.session.commit()

    @staticmethod
    def generate_share_code(length=8):
        """
        生成分享码

        Args:
            length: 分享码长度

        Returns:
            str: 分享码
        """
        chars = string.ascii_letters + string.digits
        code = ''.join(random.choice(chars) for _ in range(length))

        # 检查是否已存在
        while Share.query.filter_by(share_code=code).first():
            code = ''.join(random.choice(chars) for _ in range(length))

        return code

    @staticmethod
    def create_share(file_id, created_by, password=None, expire_days=7):
        """
        创建分享

        Args:
            file_id: 文档ID
            created_by: 创建用户ID
            password: 分享密码（可选）
            expire_days: 有效天数

        Returns:
            Share: 分享实例
        """
        # 生成分享码
        share_code = Share.generate_share_code()

        # 计算过期时间
        expire_time = None
        if expire_days > 0:
            expire_time = datetime.now() + timedelta(days=expire_days)

        share = Share(
            share_code=share_code,
            file_id=file_id,
            share_password=password,
            expire_days=expire_days,
            expire_time=expire_time,
            created_by=created_by
        )

        db.session.add(share)
        db.session.commit()

        return share

    @staticmethod
    def get_share_by_code(share_code):
        """
        根据分享码获取分享

        Args:
            share_code: 分享码

        Returns:
            Share: 分享实例
        """
        return Share.query.filter_by(share_code=share_code).first()

    @staticmethod
    def get_user_shares(user_id):
        """
        获取用户的分享列表

        Args:
            user_id: 用户ID

        Returns:
            list: 分享列表
        """
        return Share.query.filter_by(created_by=user_id).order_by(Share.created_at.desc()).all()

    @staticmethod
    def clean_expired_shares():
        """
        清理过期的分享

        Returns:
            int: 清理的数量
        """
        expired_shares = Share.query.filter(
            Share.expire_time.isnot(None),
            Share.expire_time < datetime.now()
        ).all()

        count = len(expired_shares)

        for share in expired_shares:
            db.session.delete(share)

        db.session.commit()

        return count
