"""
用户模型
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class User(db.Model, UserMixin):
    """
    用户表模型
    """
    __tablename__ = 'sys_user'

    # ========== 基础字段 ==========
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='用户ID')
    username = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='用户名')
    password = db.Column(db.String(128), nullable=False, comment='密码（加密）')
    email = db.Column(db.String(100), unique=True, nullable=True, index=True, comment='邮箱')
    nickname = db.Column(db.String(50), nullable=True, comment='昵称')
    avatar = db.Column(db.String(255), nullable=True, comment='头像路径')

    # ========== 权限字段 ==========
    role = db.Column(db.String(20), nullable=False, default='user', comment='角色：admin/user')
    status = db.Column(db.Integer, nullable=False, default=1, comment='状态：1启用 0禁用')

    # ========== 存储字段 ==========
    storage_limit = db.Column(db.Integer, nullable=False, default=1073741824, comment='存储限制（字节）1GB')
    storage_used = db.Column(db.Integer, nullable=False, default=0, comment='已使用存储（字节）')

    # ========== 时间字段 ==========
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # ========== 关系字段 ==========
    # 文件夹关系
    folders = db.relationship('Folder', backref='owner', lazy='dynamic')
    # 文档关系
    files = db.relationship('File', backref='owner', lazy='dynamic')
    # 标签关系
    tags = db.relationship('Tag', backref='owner', lazy='dynamic')
    # 操作日志关系
    logs = db.relationship('Log', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        """
        序列化为字典
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nickname': self.nickname,
            'avatar': self.avatar,
            'role': self.role,
            'status': self.status,
            'storage_limit': self.storage_limit,
            'storage_used': self.storage_used,
            'storage_percent': round(self.storage_used / self.storage_limit * 100, 2) if self.storage_limit > 0 else 0,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def set_password(self, password):
        """
        设置密码（加密）

        Args:
            password: 原始密码
        """
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """
        验证密码

        Args:
            password: 原始密码

        Returns:
            bool: 密码是否正确
        """
        return check_password_hash(self.password, password)

    def is_admin(self):
        """
        是否是管理员

        Returns:
            bool: 是否是管理员
        """
        return self.role == 'admin'

    def is_active(self):
        """
        账户是否激活

        Returns:
            bool: 账户是否激活
        """
        return self.status == 1

    def update_storage(self, size):
        """
        更新存储使用量

        Args:
            size: 文件大小（字节）
        """
        self.storage_used += size
        db.session.commit()

    def get_storage_info(self):
        """
        获取存储信息

        Returns:
            dict: 存储信息
        """
        return {
            'total': self.storage_limit,
            'used': self.storage_used,
            'available': self.storage_limit - self.storage_used,
            'percent': round(self.storage_used / self.storage_limit * 100, 2) if self.storage_limit > 0 else 0
        }

    @staticmethod
    def create_user(username, password, email=None, role='user'):
        """
        创建用户

        Args:
            username: 用户名
            password: 密码
            email: 邮箱
            role: 角色

        Returns:
            User: 用户实例
        """
        user = User(
            username=username,
            email=email,
            role=role
        )
        user.set_password(password)

        # 设置默认存储限制
        if role == 'admin':
            from config import Config
            user.storage_limit = Config.ADMIN_STORAGE_LIMIT
        else:
            from config import Config
            user.storage_limit = Config.DEFAULT_STORAGE_LIMIT

        db.session.add(user)
        db.session.commit()

        return user
