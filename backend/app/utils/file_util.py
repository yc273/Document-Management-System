"""
文件工具类
文件处理相关工具函数
"""
import os
import hashlib
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename


def allowed_file(filename, allowed_extensions=None):
    """
    检查文件类型是否允许

    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名集合

    Returns:
        bool: 是否允许
    """
    if not filename:
        return False

    if '.' not in filename:
        return False

    extension = filename.rsplit('.', 1)[1].lower()

    if allowed_extensions is None:
        # 默认允许的文件类型
        from app.config import Config
        allowed_extensions = Config.ALLOWED_EXTENSIONS

    return extension in allowed_extensions


def get_file_size(size_bytes):
    """
    转换文件大小为可读格式

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        str: 可读的文件大小
    """
    if size_bytes is None or size_bytes < 0:
        return '0 B'

    size = float(size_bytes)
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

    for unit in units:
        if size < 1024.0:
            return f'{round(size, 2)} {unit}'
        size /= 1024.0

    return f'{round(size, 2)} EB'


def generate_filename(original_filename, user_id=None):
    """
    生成唯一文件名

    Args:
        original_filename: 原始文件名
        user_id: 用户ID（可选）

    Returns:
        str: 唯一文件名
    """
    # 获取文件扩展名
    if '.' in original_filename:
        extension = original_filename.rsplit('.', 1)[1].lower()
    else:
        extension = ''

    # 生成唯一标识
    unique_id = str(uuid.uuid4())

    # 如果有用户ID，加入文件名
    if user_id:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{user_id}_{timestamp}_{unique_id}"
    else:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{unique_id}"

    # 添加扩展名
    if extension:
        filename = f"{filename}.{extension}"

    return filename


def secure_file_path(upload_folder, filename):
    """
    生成安全的文件路径

    Args:
        upload_folder: 上传文件夹
        filename: 文件名

    Returns:
        str: 安全的文件路径
    """
    # 确保上传文件夹存在
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # 生成安全的文件名
    secure_name = secure_filename(filename)

    # 组合完整路径
    file_path = os.path.join(upload_folder, secure_name)

    return file_path


def get_file_hash(file_path):
    """
    计算文件的MD5哈希值

    Args:
        file_path: 文件路径

    Returns:
        str: 文件哈希值（None表示文件不存在）
    """
    if not os.path.exists(file_path):
        return None

    md5 = hashlib.md5()

    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5.update(chunk)
        return md5.hexdigest()
    except Exception as e:
        print(f"计算文件哈希失败: {e}")
        return None


def get_file_type(filename):
    """
    获取文件类型

    Args:
        filename: 文件名

    Returns:
        str: 文件类型
    """
    if '.' not in filename:
        return 'unknown'

    extension = filename.rsplit('.', 1)[1].lower()

    # 文件类型分类
    type_mapping = {
        # 文档类
        'pdf': 'pdf',
        'doc': 'word',
        'docx': 'word',
        'xls': 'excel',
        'xlsx': 'excel',
        'ppt': 'powerpoint',
        'pptx': 'powerpoint',
        'txt': 'text',
        'md': 'text',
        # 图片类
        'png': 'image',
        'jpg': 'image',
        'jpeg': 'image',
        'gif': 'image',
        'bmp': 'image',
        'svg': 'image',
        'webp': 'image',
        # 视频类
        'mp4': 'video',
        'avi': 'video',
        'mov': 'video',
        'wmv': 'video',
        'flv': 'video',
        # 音频类
        'mp3': 'audio',
        'wav': 'audio',
        'flac': 'audio',
        # 压缩包
        'zip': 'archive',
        'rar': 'archive',
        '7z': 'archive',
        'tar': 'archive',
        'gz': 'archive',
    }

    return type_mapping.get(extension, extension)


def ensure_directory(directory):
    """
    确保目录存在，不存在则创建

    Args:
        directory: 目录路径

    Returns:
        bool: 是否成功
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        return True
    except Exception as e:
        print(f"创建目录失败: {e}")
        return False


def delete_file(file_path):
    """
    删除文件

    Args:
        file_path: 文件路径

    Returns:
        bool: 是否成功
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as e:
        print(f"删除文件失败: {e}")
        return False


def copy_file(src, dst):
    """
    复制文件

    Args:
        src: 源文件路径
        dst: 目标文件路径

    Returns:
        bool: 是否成功
    """
    try:
        import shutil
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        print(f"复制文件失败: {e}")
        return False


def get_file_icon(file_type):
    """
    根据文件类型获取图标

    Args:
        file_type: 文件类型

    Returns:
        str: 图标名称
    """
    icon_mapping = {
        'pdf': 'el-icon-document',
        'word': 'el-icon-document',
        'excel': 'el-icon-s-grid',
        'powerpoint': 'el-icon-document',
        'text': 'el-icon-document',
        'image': 'el-icon-picture',
        'video': 'el-icon-video-play',
        'audio': 'el-icon-microphone',
        'archive': 'el-icon-folder',
        'unknown': 'el-icon-document'
    }

    return icon_mapping.get(file_type, 'el-icon-document')


def format_file_date(timestamp):
    """
    格式化文件日期

    Args:
        timestamp: 时间戳

    Returns:
        str: 格式化的日期字符串
    """
    if timestamp is None:
        return ''

    date = datetime.fromtimestamp(timestamp)

    now = datetime.now()
    delta = now - date

    if delta.days < 1:
        if delta.seconds < 60:
            return '刚刚'
        elif delta.seconds < 3600:
            return f'{delta.seconds // 60}分钟前'
        else:
            return f'{delta.seconds // 3600}小时前'
    elif delta.days < 7:
        return f'{delta.days}天前'
    else:
        return date.strftime('%Y-%m-%d')
