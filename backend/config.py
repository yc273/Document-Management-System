"""
应用配置文件
包含数据库配置、上传配置、安全配置等
"""
import os
from datetime import timedelta


class Config:
    """基础配置类"""

    # 密钥配置（生产环境需要修改为随机字符串）
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'doc-management-system-secret-key-2024'

    # ========== 基础路径配置 ==========
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # ========== 数据库配置 ==========
    # SQLite数据库（无需安装MySQL，自动创建db文件）
    db_path = os.path.join(BASE_DIR, 'doc_management.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # 开发环境可设置为True查看SQL语句

    # ========== 文件上传配置 ==========
    # 上传文件夹路径
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    UPLOAD_DOCUMENTS = os.path.join(UPLOAD_FOLDER, 'documents')  # 文档存储
    UPLOAD_AVATARS = os.path.join(UPLOAD_FOLDER, 'avatars')      # 头像存储
    UPLOAD_TEMP = os.path.join(UPLOAD_FOLDER, 'temp')           # 临时文件

    # 文件大小限制（5GB）
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024 * 1024

    # 允许上传的文件类型
    ALLOWED_EXTENSIONS = {
        # 文档类
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv',
        # 图片类
        'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg', 'webp',
        # 视频类
        'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv',
        # 音频类
        'mp3', 'wav', 'flac',
        # 压缩包
        'zip', 'rar', '7z',
        # 其他
        'md', 'json', 'xml'
    }

    # ========== 用户存储配置 ==========
    # 默认存储空间限制（10GB）
    DEFAULT_STORAGE_LIMIT = 10 * 1024 * 1024 * 1024

    # 管理员存储空间限制（20GB）
    ADMIN_STORAGE_LIMIT = 20 * 1024 * 1024 * 1024

    # ========== Session配置 ==========
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Session有效期7天
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ========== 分页配置 ==========
    ITEMS_PER_PAGE = 20  # 每页显示条数

    # ========== 文件分享配置 ==========
    SHARE_DEFAULT_EXPIRE_DAYS = 7  # 默认分享有效期（天）
    SHARE_MAX_EXPIRE_DAYS = 30     # 最大分享有效期（天）

    # ========== 回收站配置 ==========
    TRASH_RETENTION_DAYS = 30  # 回收站文件保留天数，超过则自动永久删除

    # ========== 日志配置 ==========
    LOG_LEVEL = 'INFO'
    LOG_FILE = os.path.join(BASE_DIR, 'logs', 'app.log')

    # ========== CORS配置 ==========
    CORS_ORIGINS = '*'  # 允许所有来源（局域网访问需要）


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # 显示SQL语句


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

    # 生产环境必须设置环境变量
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-this-in-production'


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # 使用内存数据库


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
