"""
扩展插件初始化
初始化数据库、登录管理器等扩展
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# 初始化数据库实例
db = SQLAlchemy()

# 初始化登录管理器
login_manager = LoginManager()
login_manager.session_protection = 'strong'
# 注意：auth蓝图将在后续实现，暂时设置为通用值
# login_manager.login_view = 'auth.login'  # 待实现auth模块后启用
login_manager.login_message = '请先登录'


def init_extensions(app):
    """初始化所有扩展插件"""

    # 初始化数据库
    db.init_app(app)

    # 初始化登录管理器
    login_manager.init_app(app)

    # 用户加载回调函数
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        """加载用户"""
        return User.query.get(int(user_id))
