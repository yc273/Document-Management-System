"""
Flask应用启动文件
支持局域网访问配置
"""
import os
from app import create_app

# 创建Flask应用
# development: 开发环境
# production: 生产环境
# testing: 测试环境
app = create_app('development')


def get_local_ip():
    """
    获取本机局域网IP地址

    Returns:
        str: 本机IP地址
    """
    import socket

    try:
        # 获取本机主机名
        hostname = socket.gethostname()

        # 获取本机IP
        local_ip = socket.gethostbyname(hostname)

        return local_ip
    except Exception as e:
        print(f"获取本机IP失败: {e}")
        return "127.0.0.1"


if __name__ == '__main__':
    # 配置参数
    host = '0.0.0.0'  # 允许外部访问（关键配置）
    port = 5000       # 端口号
    debug = True       # 调试模式

    # 获取本机IP
    local_ip = get_local_ip()

    print('=' * 60)
    print('🚀 智能文档管理系统 - 启动成功！')
    print('=' * 60)
    print(f'📱 本地访问:     http://localhost:{port}')
    print(f'📱 本机访问:     http://127.0.0.1:{port}')
    print(f'🌐 局域网访问:   http://{local_ip}:{port}')
    print('=' * 60)
    print('💡 提示:')
    print('  - 确保手机和电脑连接同一个WiFi')
    print('  - 首次运行请允许防火墙访问')
    print('  - 按 Ctrl+C 停止服务')
    print('=' * 60)
    print()

    # 启动应用
    app.run(
        host=host,
        port=port,
        debug=debug
    )
