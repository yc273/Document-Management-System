"""
操作日志模型
"""
from datetime import datetime

from app.extensions import db


class Log(db.Model):
    """
    操作日志表模型
    """
    __tablename__ = 'sys_log'

    # ========== 基础字段 ==========
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='日志ID')
    user_id = db.Column(db.Integer, db.ForeignKey('sys_user.id'), nullable=False, index=True, comment='用户ID')
    action = db.Column(db.String(50), nullable=False, comment='操作类型')
    module = db.Column(db.String(50), nullable=False, comment='模块名称')
    description = db.Column(db.String(255), nullable=True, comment='操作描述')
    ip_address = db.Column(db.String(50), nullable=True, comment='IP地址')

    # ========== 时间字段 ==========
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True, comment='创建时间')

    # 注意：用户关系由User.logs通过backref自动创建，无需在此定义

    def __repr__(self):
        return f'<Log {self.action} - {self.module}>'

    def to_dict(self):
        """
        序列化为字典

        Returns:
            dict: 日志信息
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'action': self.action,
            'module': self.module,
            'description': self.description,
            'ip_address': self.ip_address,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    @staticmethod
    def create_log(user_id, action, module, description=None, ip_address=None):
        """
        创建日志

        Args:
            user_id: 用户ID
            action: 操作类型
            module: 模块名称
            description: 操作描述
            ip_address: IP地址

        Returns:
            Log: 日志实例
        """
        log = Log(
            user_id=user_id,
            action=action,
            module=module,
            description=description,
            ip_address=ip_address
        )

        db.session.add(log)
        db.session.commit()

        return log

    @staticmethod
    def get_user_logs(user_id, limit=100):
        """
        获取用户日志

        Args:
            user_id: 用户ID
            limit: 数量限制

        Returns:
            list: 日志列表
        """
        return Log.query.filter_by(user_id=user_id).order_by(Log.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_logs_by_module(module, limit=100):
        """
        获取模块日志

        Args:
            module: 模块名称
            limit: 数量限制

        Returns:
            list: 日志列表
        """
        return Log.query.filter_by(module=module).order_by(Log.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_logs_by_date(start_date, end_date=None):
        """
        获取日期范围内的日志

        Args:
            start_date: 开始日期
            end_date: 结束日期（可选）

        Returns:
            list: 日志列表
        """
        query = Log.query.filter(Log.created_at >= start_date)

        if end_date:
            query = query.filter(Log.created_at <= end_date)

        return query.order_by(Log.created_at.desc()).all()

    @staticmethod
    def get_logs_by_action(action, limit=100):
        """
        获取操作类型的日志

        Args:
            action: 操作类型
            limit: 数量限制

        Returns:
            list: 日志列表
        """
        return Log.query.filter_by(action=action).order_by(Log.created_at.desc()).limit(limit).all()

    @staticmethod
    def clean_old_logs(days=30):
        """
        清理旧日志

        Args:
            days: 保留天数

        Returns:
            int: 清理的数量
        """
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)

        old_logs = Log.query.filter(Log.created_at < cutoff_date).all()
        count = len(old_logs)

        for log in old_logs:
            db.session.delete(log)

        db.session.commit()

        return count

    @staticmethod
    def get_statistics(days=7):
        """
        获取日志统计信息

        Args:
            days: 统计天数

        Returns:
            dict: 统计信息
        """
        from datetime import timedelta
        from sqlalchemy import func

        start_date = datetime.now() - timedelta(days=days)

        # 总操作次数
        total_count = Log.query.filter(Log.created_at >= start_date).count()

        # 按模块统计
        module_stats = db.session.query(
            Log.module,
            func.count(Log.id).label('count')
        ).filter(
            Log.created_at >= start_date
        ).group_by(Log.module).all()

        # 按操作类型统计
        action_stats = db.session.query(
            Log.action,
            func.count(Log.id).label('count')
        ).filter(
            Log.created_at >= start_date
        ).group_by(Log.action).all()

        return {
            'total_count': total_count,
            'module_stats': [{'module': m, 'count': c} for m, c in module_stats],
            'action_stats': [{'action': a, 'count': c} for a, c in action_stats]
        }
