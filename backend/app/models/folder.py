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

    # ========== 删除标记（软删除/回收站）==========
    is_deleted = db.Column(db.Integer, nullable=False, default=0, index=True, comment='是否删除：1是 0否')
    deleted_at = db.Column(db.DateTime, nullable=True, comment='删除时间')

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
        # 按记录数统计当前文件夹下的文件数量（不去重，排除已删除）
        file_count = File.query.filter(
            File.folder_id == self.id,
            File.is_deleted == 0
        ).count()

        data = {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'user_id': self.user_id,
            'path': self.path,
            'level': self.level,
            'sort_order': self.sort_order,
            'file_count': file_count,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

        # 已删除文件夹附加：删除时间、剩余保留天数
        if self.is_deleted == 1:
            from config import Config
            retention_days = Config.TRASH_RETENTION_DAYS
            data['deleted_at'] = self.deleted_at.strftime('%Y-%m-%d %H:%M:%S') if self.deleted_at else None
            if self.deleted_at:
                from datetime import datetime as _dt
                elapsed = (_dt.now() - self.deleted_at).total_seconds() / 86400
                remaining = int(retention_days - elapsed)
                data['expire_days'] = max(remaining, 0)
            else:
                data['expire_days'] = retention_days

        if include_children:
            # 只包含未删除的子文件夹
            data['children'] = [child.to_dict() for child in self.children.filter(Folder.is_deleted == 0).all()]

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

    def get_descendant_folder_ids(self):
        """
        递归收集当前文件夹的所有子孙文件夹ID（不含自身），BFS 实现。

        Returns:
            list: 子孙文件夹ID列表
        """
        ids = []
        queue = [self.id]
        while queue:
            current_id = queue.pop(0)
            child_ids = [f.id for f in Folder.query.filter_by(parent_id=current_id).all()]
            ids.extend(child_ids)
            queue.extend(child_ids)
        return ids

    def soft_delete(self):
        """
        级联软删除（移入回收站）。
        标记当前文件夹 + 所有子孙文件夹 + 其中的未删除文件为 is_deleted=1。
        """
        from app.models.file import File
        from datetime import datetime as _dt

        now = _dt.now()
        # 收集自身 + 所有子孙文件夹
        all_folder_ids = [self.id] + self.get_descendant_folder_ids()

        # 软删除这些文件夹
        Folder.query.filter(Folder.id.in_(all_folder_ids)).update(
            {Folder.is_deleted: 1, Folder.deleted_at: now}, synchronize_session=False
        )
        # 软删除这些文件夹下的未删除文件
        File.query.filter(
            File.folder_id.in_(all_folder_ids),
            File.is_deleted == 0
        ).update(
            {File.is_deleted: 1, File.deleted_at: now}, synchronize_session=False
        )
        db.session.commit()

    def restore_cascade(self):
        """
        级联恢复（从回收站恢复）。
        恢复当前文件夹 + 所有子孙文件夹 + 其中的已删除文件。
        若父文件夹也处于软删除状态，则顺带恢复父级链（整体恢复）。
        """
        from app.models.file import File

        # 若父文件夹也被软删除，先恢复父级链
        if self.parent_id and self.parent_id != 0:
            parent = Folder.query.get(self.parent_id)
            if parent and parent.is_deleted == 1:
                parent.restore_cascade()

        # 收集自身 + 所有子孙文件夹
        all_folder_ids = [self.id] + self.get_descendant_folder_ids()

        Folder.query.filter(Folder.id.in_(all_folder_ids)).update(
            {Folder.is_deleted: 0, Folder.deleted_at: None}, synchronize_session=False
        )
        File.query.filter(
            File.folder_id.in_(all_folder_ids),
            File.is_deleted == 1
        ).update(
            {File.is_deleted: 0, File.deleted_at: None}, synchronize_session=False
        )
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
        获取未删除的子文件夹

        Returns:
            list: 子文件夹列表
        """
        return Folder.query.filter_by(parent_id=self.id, is_deleted=0).order_by(Folder.sort_order).all()

    def get_file_count(self):
        """
        获取文件夹下的文档数量（包括未删除的子文件夹，按记录数统计，不去重）

        Returns:
            int: 文档数量
        """
        from app.models.file import File
        # 当前文件夹下的文档数量（按记录数）
        direct_count = File.query.filter(
            File.folder_id == self.id,
            File.is_deleted == 0
        ).count()

        # 未删除子文件夹的文档数量
        indirect_count = 0
        for child in self.children.filter(Folder.is_deleted == 0).all():
            indirect_count += child.get_file_count()

        return direct_count + indirect_count

    def can_delete(self):
        """
        是否可以删除（软删除总是允许，包括非空文件夹——会级联软删除内部内容）

        Returns:
            bool: 是否可以删除
        """
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
        获取用户的未删除根文件夹

        Args:
            user_id: 用户ID

        Returns:
            list: 根文件夹列表
        """
        return Folder.query.filter_by(user_id=user_id, parent_id=0, is_deleted=0).order_by(Folder.sort_order).all()

    @staticmethod
    def get_folder_tree(user_id):
        """
        获取用户的文件夹树（仅未删除）

        Args:
            user_id: 用户ID

        Returns:
            list: 文件夹树列表
        """
        def build_tree(parent_id=0):
            folders = Folder.query.filter_by(user_id=user_id, parent_id=parent_id, is_deleted=0).order_by(Folder.sort_order).all()
            tree = []
            for folder in folders:
                folder_dict = folder.to_dict()
                folder_dict['children'] = build_tree(folder.id)
                tree.append(folder_dict)
            return tree

        return build_tree()
