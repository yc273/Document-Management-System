"""
Flask应用工厂
创建并配置Flask应用
"""
import os
import sys
from flask import Flask, render_template, jsonify
from flask_cors import CORS

# 添加父目录到Python路径，以便导入config模块
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import config
from app.extensions import db, init_extensions


def create_app(config_name='development'):
    """
    应用工厂函数

    Args:
        config_name: 配置名称 ('development', 'production', 'testing')

    Returns:
        Flask应用实例
    """

    # 创建Flask应用
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(config[config_name])

    # 初始化扩展插件
    init_extensions(app)

    # 配置CORS（跨域资源共享）- 支持局域网访问和凭证
    # 在开发环境中，为了方便测试，我们允许特定的本地和局域网地址
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://localhost:5174",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:5174",
                # 支持两个网络接口的所有端口
                "http://192.168.1.102:5173",
                "http://192.168.1.102:5174",
                "http://192.168.50.236:5173",
                "http://192.168.50.236:5174"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    # 创建必要的目录
    create_upload_folders(app)

    # 注册蓝图
    register_blueprints(app)

    # 注册错误处理器
    register_error_handlers(app)

    # 注册根路由
    @app.route('/')
    def index():
        """根路由 - 返回API信息"""
        return jsonify({
            'code': 200,
            'message': '智能文档管理系统 API',
            'version': '1.0.0',
            'docs': '/api/docs'
        })

    @app.route('/health')
    def health():
        """健康检查接口"""
        return jsonify({
            'code': 200,
            'status': 'healthy',
            'message': '服务运行正常'
        })

    return app


def create_upload_folders(app):
    """创建上传文件夹"""
    folders = [
        app.config['UPLOAD_FOLDER'],
        app.config['UPLOAD_DOCUMENTS'],
        app.config['UPLOAD_AVATARS'],
        app.config['UPLOAD_TEMP'],
        os.path.join(app.config['BASE_DIR'], 'logs')
    ]

    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f'创建目录: {folder}')


def register_blueprints(app):
    """注册蓝图"""

    # 导入蓝图
    from app.controllers.auth_controller import auth_bp
    from app.controllers.folder_controller import folder_bp
    from app.controllers.file_controller import file_bp
    from app.controllers.tag_controller import tag_bp
    from app.controllers.share_controller import share_bp
    from app.controllers.trash_controller import trash_bp
    from app.controllers.stat_controller import stat_bp

    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(folder_bp, url_prefix='/api/folder')
    app.register_blueprint(file_bp, url_prefix='/api/file')
    app.register_blueprint(tag_bp, url_prefix='/api/tag')
    app.register_blueprint(share_bp, url_prefix='/api/share')
    app.register_blueprint(trash_bp, url_prefix='/api/trash')
    app.register_blueprint(stat_bp, url_prefix='/api/stat')

    print('蓝图注册完成')


def register_error_handlers(app):
    """注册错误处理器"""

    @app.errorhandler(400)
    def bad_request(e):
        """400错误"""
        return jsonify({
            'code': 400,
            'message': '请求参数错误',
            'data': None
        }), 400

    @app.errorhandler(401)
    def unauthorized(e):
        """401错误"""
        return jsonify({
            'code': 401,
            'message': '未授权，请先登录',
            'data': None
        }), 401

    @app.errorhandler(403)
    def forbidden(e):
        """403错误"""
        return jsonify({
            'code': 403,
            'message': '禁止访问',
            'data': None
        }), 403

    @app.errorhandler(404)
    def not_found(e):
        """404错误"""
        return jsonify({
            'code': 404,
            'message': '资源不存在',
            'data': None
        }), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        """500错误"""
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
