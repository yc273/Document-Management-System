"""
统计管理控制器
处理数据统计、日志查询等操作
"""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from sqlalchemy import func

from app.extensions import db
from app.models.file import File
from app.models.folder import Folder
from app.models.tag import Tag
from app.models.share import Share
from app.models.log import Log
from app.models.user import User
from app.utils.decorators import login_required_json, active_required, admin_required
from app.utils.response import success

# 创建蓝图
stat_bp = Blueprint('stat', __name__)


@stat_bp.route('/dashboard', methods=['GET'])
@login_required_json
@active_required
def get_dashboard():
    """
    获取仪表板数据
    GET /api/stat/dashboard
    """
    # 文档统计（按哈希去重）
    distinct_hashes = db.session.query(File.file_hash).filter(
        File.user_id == current_user.id,
        File.is_deleted == 0,
        File.file_hash.isnot(None)
    ).distinct().count()
    null_hash_count = File.query.filter(
        File.user_id == current_user.id,
        File.is_deleted == 0,
        File.file_hash.is_(None)
    ).count()
    total_files = distinct_hashes + null_hash_count
    total_folders = Folder.query.filter_by(user_id=current_user.id).count()
    total_tags = Tag.query.filter_by(user_id=current_user.id).count()
    total_shares = Share.query.filter_by(created_by=current_user.id).count()

    # 最近上传
    recent_files = File.query.filter_by(
        user_id=current_user.id,
        is_deleted=0
    ).order_by(File.created_at.desc()).limit(5).all()

    # 存储信息
    user = User.query.filter_by(id=current_user.id).first()
    storage_info = user.get_storage_info() if user else {}

    return success({
        'total_files': total_files,
        'total_folders': total_folders,
        'total_tags': total_tags,
        'total_shares': total_shares,
        'storage': storage_info,
        'recent_files': [file.to_dict() for file in recent_files]
    })


@stat_bp.route('/storage', methods=['GET'])
@login_required_json
@active_required
def get_storage_stats():
    """
    获取存储空间统计
    GET /api/stat/storage
    """
    user = User.query.filter_by(id=current_user.id).first()
    if not user:
        return success({'storage': {}})

    storage_info = user.get_storage_info()

    # 按文件类型统计
    file_type_stats = db.session.query(
        File.file_type,
        func.count(File.id).label('count'),
        func.sum(File.file_size).label('total_size')
    ).filter(
        File.user_id == current_user.id,
        File.is_deleted == 0
    ).group_by(File.file_type).all()

    type_stats = []
    for file_type, count, total_size in file_type_stats:
        type_stats.append({
            'type': file_type,
            'count': count,
            'total_size': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2)
        })

    return success({
        'storage': storage_info,
        'file_types': type_stats
    })


@stat_bp.route('/upload', methods=['GET'])
@login_required_json
@active_required
def get_upload_stats():
    """
    获取上传统计
    GET /api/stat/upload

    参数:
    - days: 统计天数（默认7天）
    """
    from datetime import timedelta

    days = request.args.get('days', 7, type=int)
    start_date = datetime.now() - timedelta(days=days)

    # 每日上传统计
    upload_stats = db.session.query(
        func.date(File.created_at).label('date'),
        func.count(File.id).label('count')
    ).filter(
        File.user_id == current_user.id,
        File.created_at >= start_date,
        File.is_deleted == 0
    ).group_by(func.date(File.created_at)).all()

    daily_stats = []
    for date, count in upload_stats:
        daily_stats.append({
            'date': date,
            'count': count
        })

    return success({
        'daily': daily_stats,
        'days': days
    })


@stat_bp.route('/log', methods=['GET'])
@login_required_json
@active_required
def get_log_stats():
    """
    获取操作日志
    GET /api/stat/log

    参数:
    - page: 页码
    - per_page: 每页数量
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 获取日志
    query = Log.query.filter_by(user_id=current_user.id)

    # 分页
    pagination = query.order_by(Log.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return success({
        'logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@stat_bp.route('/system', methods=['GET'])
@login_required_json
@admin_required
def get_system_stats():
    """
    获取系统统计（管理员）
    GET /api/stat/system
    """
    # 用户统计
    total_users = User.query.count()
    active_users = User.query.filter_by(status=1).count()

    # 文档统计
    total_files = File.query.filter_by(is_deleted=0).count()

    # 存储统计
    total_storage = db.session.query(
        func.sum(User.storage_used)
    ).scalar() or 0

    # 今日新增
    from datetime import date
    today = date.today()
    today_users = db.session.query(
        func.count(User.id)
    ).filter(
        func.date(User.created_at) == today
    ).scalar() or 0

    today_files = db.session.query(
        func.count(File.id)
    ).filter(
        func.date(File.created_at) == today,
        File.is_deleted == 0
    ).scalar() or 0

    return success({
        'total_users': total_users,
        'active_users': active_users,
        'total_files': total_files,
        'total_storage': total_storage,
        'total_storage_gb': round(total_storage / 1024 / 1024 / 1024, 2),
        'today_users': today_users,
        'today_files': today_files
    })
