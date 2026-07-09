"""
文件夹模型
"""
from datetime import datetime

from app.extensions import db


class Folder(db.Model):
    """
    文件夹表模型
    """
    __tablename__ = 'doc_folder'

    # ========== 基础字段 ==========
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='文件夹ID')
    name = db.Column(db.String(100), nullable=False, comment='文件夹名称')
    parent_id = db.Column(db.Integer, db.ForeignKey('doc_folder.id'), nullable=True, default=None, index=True, comment='父文件夹ID（NULL为根目录）')
    user_id = db.Column(db.Integer, db.ForeignKey('sys_user.id'), nullable=False, index=True, comment='所属用户')

    # ========== 路径字段 ==========
    path = db.Column(db.String(500), nullable=True, comment='完整路径')
    level = db.Column(db.Integer, nullable=False, default=1, comment='层级')
    sort_order = db.Column(db.Integer, nullable=False, default=0, comment='排序')

    # ========== 时间字段 ==========
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # ========== 关系字段 ==========
    # 子文件夹关系（自关联）
    children = db.relationship(
        'Folder',
        primaryjoin='Folder.parent_id == Folder.id',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic'
    )
    # 文档关系
    files = db.relationship('File', backref='folder', lazy='dynamic')

    def __repr__(self):
        return f'<Folder {self.name}>'

    def to_dict(self, include_children=False):
        """
        序列化为字典

        Args:
            include_children: 是否包含子文件夹

        Returns:
            dict: 文件夹信息
        """
        from app.models.file import File
        from app.extensions import db
        # 按文件哈希去重统计，同一文件夹内相同哈希的文件只算1个
        distinct_hashes = db.session.query(File.file_hash).filter(
            File.folder_id == self.id,
            File.is_deleted == 0,
            File.file_hash.isnot(None)
        ).distinct().count()
        # 无哈希值的文件单独计数（每个算1个）
        null_hash_count = File.query.filter(
            File.folder_id == self.id,
            File.is_deleted == 0,
            File.file_hash.is_(None)
        ).count()
        file_count = distinct_hashes + null_hash_count

        data = {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'user_id': self.user_id,
            'path': self.path,
            'level': self.level,
            'sort_order': self.sort_order,
            'file_count': file_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

        if include_children:
            data['children'] = [child.to_dict() for child in self.children]

        return data

    def update_path(self):
        """
        更新路径
        """
        if self.parent_id == 0:
            self.path = f'/{self.name}'
            self.level = 1
        else:
            parent = Folder.query.get(self.parent_id)
            if parent:
                self.path = f'{parent.path}/{self.name}'
                self.level = parent.level + 1
            else:
                self.path = f'/{self.name}'
                self.level = 1

        db.session.commit()

    def get_full_path(self):
        """
        获取完整路径

        Returns:
            str: 完整路径
        """
        return self.path if self.path else f'/{self.name}'

    def get_ancestors(self):
        """
        获取所有祖先文件夹

        Returns:
            list: 祖先文件夹列表
        """
        ancestors = []
        current = self

        while current.parent_id != 0:
            parent = Folder.query.get(current.parent_id)
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break

        ancestors.reverse()
        return ancestors

    def get_children(self):
        """
        获取子文件夹

        Returns:
            list: 子文件夹列表
        """
        return Folder.query.filter_by(parent_id=self.id).order_by(Folder.sort_order).all()

    def get_file_count(self):
        """
        获取文件夹下的文档数量（包括子文件夹，按哈希去重）

        Returns:
            int: 文档数量
        """
        from app.models.file import File
        from app.extensions import db
        # 按文件哈希去重统计
        distinct_hashes = db.session.query(File.file_hash).filter(
            File.folder_id == self.id,
            File.is_deleted == 0,
            File.file_hash.isnot(None)
        ).distinct().count()
        null_hash_count = File.query.filter(
            File.folder_id == self.id,
            File.is_deleted == 0,
            File.file_hash.is_(None)
        ).count()
        direct_count = distinct_hashes + null_hash_count

        # 子文件夹文档数量
        indirect_count = 0
        for child in self.children:
            indirect_count += child.get_file_count()

        return direct_count + indirect_count

    def can_delete(self):
        """
        是否可以删除

        Returns:
            bool: 是否可以删除
        """
        # 有子文件夹不能删除
        if self.children.count() > 0:
            return False

        from app.models.file import File
        # 有未删除的文档不能删除
        if self.files.filter(File.is_deleted == 0).count() > 0:
            return False

        return True

    @staticmethod
    def create_folder(name, user_id, parent_id=0):
        """
        创建文件夹

        Args:
            name: 文件夹名称
            user_id: 用户ID
            parent_id: 父文件夹ID

        Returns:
            Folder: 文件夹实例
        """
        folder = Folder(
            name=name,
            user_id=user_id,
            parent_id=parent_id
        )

        # 计算路径和层级
        if parent_id == 0:
            folder.path = f'/{name}'
            folder.level = 1
        else:
            parent = Folder.query.get(parent_id)
            if parent:
                folder.path = f'{parent.path}/{name}'
                folder.level = parent.level + 1
            else:
                folder.path = f'/{name}'
                folder.level = 1

        db.session.add(folder)
        db.session.commit()

        return folder

    @staticmethod
    def get_root_folders(user_id):
        """
        获取用户的根文件夹

        Args:
            user_id: 用户ID

        Returns:
            list: 根文件夹列表
        """
        return Folder.query.filter_by(user_id=user_id, parent_id=0).order_by(Folder.sort_order).all()

    @staticmethod
    def get_folder_tree(user_id):
        """
        获取文件夹树

        Args:
            user_id: 用户ID

        Returns:
            list: 文件夹树列表
        """
        def build_tree(parent_id=0):
            folders = Folder.query.filter_by(user_id=user_id, parent_id=parent_id).order_by(Folder.sort_order).all()
            tree = []
            for folder in folders:
                folder_dict = folder.to_dict()
                folder_dict['children'] = build_tree(folder.id)
                tree.append(folder_dict)
            return tree

        return build_tree()
