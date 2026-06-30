"""
认证工具类
用户认证相关工具函数
"""
import hashlib
import secrets
import time
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password):
    """
    密码哈希加密

    Args:
        password: 原始密码

    Returns:
        str: 加密后的密码
    """
    return generate_password_hash(password)


def verify_password(password, hashed_password):
    """
    验证密码

    Args:
        password: 原始密码
        hashed_password: 加密后的密码

    Returns:
        bool: 密码是否正确
    """
    return check_password_hash(hashed_password, password)


def generate_token(user_id, secret_key=None, expires_in=3600):
    """
    生成访问令牌

    Args:
        user_id: 用户ID
        secret_key: 密钥（可选）
        expires_in: 有效期（秒）

    Returns:
        str: 访问令牌
    """
    # 生成随机字符串
    random_string = secrets.token_hex(16)

    # 组合数据
    data = f"{user_id}:{int(time.time())}:{random_string}"

    # 生成哈希
    if secret_key:
        hash_data = hashlib.sha256(f"{data}:{secret_key}".encode()).hexdigest()
    else:
        hash_data = hashlib.sha256(data.encode()).hexdigest()

    # 组合token
    token = f"{data}:{hash_data}"

    return token


def verify_token(token, secret_key=None):
    """
    验证访问令牌

    Args:
        token: 访问令牌
        secret_key: 密钥（可选）

    Returns:
        dict: 用户信息（验证失败返回None）
    """
    try:
        # 分割token
        parts = token.split(':')
        if len(parts) < 4:
            return None

        user_id = parts[0]
        timestamp = parts[1]
        random_string = parts[2]
        hash_value = parts[3]

        # 验证哈希
        data = f"{user_id}:{timestamp}:{random_string}"
        if secret_key:
            expected_hash = hashlib.sha256(f"{data}:{secret_key}".encode()).hexdigest()
        else:
            expected_hash = hashlib.sha256(data.encode()).hexdigest()

        if hash_value != expected_hash:
            return None

        # 返回用户信息
        return {
            'user_id': int(user_id),
            'timestamp': int(timestamp)
        }

    except Exception as e:
        print(f"验证token失败: {e}")
        return None


def is_token_expired(token_timestamp, expires_in=3600):
    """
    检查token是否过期

    Args:
        token_timestamp: token时间戳
        expires_in: 有效期（秒）

    Returns:
        bool: 是否过期
    """
    current_time = int(time.time())
    return (current_time - token_timestamp) > expires_in


def generate_reset_token():
    """
    生成密码重置令牌

    Returns:
        str: 重置令牌
    """
    return secrets.token_urlsafe(32)


def validate_email(email):
    """
    验证邮箱格式

    Args:
        email: 邮箱地址

    Returns:
        bool: 邮箱格式是否正确
    """
    import re

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_username(username):
    """
    验证用户名格式

    Args:
        username: 用户名

    Returns:
        bool: 用户名格式是否正确
    """
    import re

    # 用户名：4-20位，字母、数字、下划线
    pattern = r'^[a-zA-Z0-9_]{4,20}$'
    return re.match(pattern, username) is not None


def validate_password(password):
    """
    验证密码强度

    Args:
        password: 密码

    Returns:
        tuple: (是否有效, 错误消息)
    """
    if len(password) < 6:
        return False, "密码长度至少6位"

    if len(password) > 20:
        return False, "密码长度不能超过20位"

    return True, ""


def get_client_ip(request):
    """
    获取客户端IP地址

    Args:
        request: Flask请求对象

    Returns:
        str: IP地址
    """
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    return request.remote_addr


def mask_email(email):
    """
    隐藏邮箱部分字符

    Args:
        email: 邮箱地址

    Returns:
        str: 隐藏后的邮箱
    """
    if '@' not in email:
        return email

    username, domain = email.split('@')

    if len(username) <= 3:
        masked_username = '*' * len(username)
    else:
        masked_username = username[:2] + '*' * (len(username) - 2)

    return f"{masked_username}@{domain}"


def mask_phone(phone):
    """
    隐藏手机号部分字符

    Args:
        phone: 手机号

    Returns:
        str: 隐藏后的手机号
    """
    if len(phone) != 11:
        return phone

    return f"{phone[:3]}****{phone[7:]}"
