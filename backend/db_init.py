"""
数据库初始化脚本
创建数据表和默认管理员账号
"""
from app import create_app, db
from app.models import User, Folder, File, Tag, FileTag, Version, Share, Log


def init_database():
    """
    初始化数据库
    """
    app = create_app('development')

    with app.app_context():
        print('=' * 60)
        print('🗄️  开始初始化数据库...')
        print('=' * 60)

        # 删除所有表（慎用！仅开发环境使用）
        # db.drop_all()
        # print('⚠️  已删除所有数据表')

        # 创建所有表
        print('📊 创建数据表...')
        db.create_all()
        print('✅ 数据表创建完成')

        # 检查是否已存在管理员
        admin = User.query.filter_by(username='admin').first()

        if admin:
            print(f'⚠️  管理员账号已存在: {admin.username}')
        else:
            # 创建默认管理员账号
            print('👤 创建默认管理员账号...')
            admin = User(
                username='admin',
                email='admin@docman.com',
                nickname='系统管理员',
                role='admin'
            )
            admin.set_password('admin123')

            # 设置管理员存储限制为10GB
            from config import Config
            admin.storage_limit = Config.ADMIN_STORAGE_LIMIT

            db.session.add(admin)
            db.session.commit()
            print('✅ 管理员账号创建完成')

        # 创建根文件夹
        print('📁 创建根文件夹...')
        root_folder = Folder.query.filter_by(user_id=admin.id, parent_id=0, name='根目录').first()

        if not root_folder:
            root_folder = Folder(
                name='根目录',
                user_id=admin.id,
                parent_id=0
            )
            root_folder.path = '/根目录'
            db.session.add(root_folder)
            db.session.commit()
            print('✅ 根文件夹创建完成')
        else:
            print('⚠️  根文件夹已存在')

        print('=' * 60)
        print('✅ 数据库初始化完成！')
        print('=' * 60)
        print()
        print('📋 默认账号信息:')
        print(f'   用户名: {admin.username}')
        print(f'   密码:   admin123')
        print(f'   邮箱:   {admin.email}')
        print()
        print('🔗 访问地址:')
        print(f'   本地:   http://localhost:5000')
        print(f'   局域网: http://<本机IP>:5000')
        print()
        print('⚠️  重要提示:')
        print('   1. 首次使用请立即修改管理员密码')
        print('   2. 生产环境请修改SECRET_KEY配置')
        print('   3. 请确保MySQL数据库已启动')
        print('=' * 60)


def reset_database():
    """
    重置数据库（删除所有数据）
    ⚠️  危险操作！仅用于开发环境
    """
    app = create_app('development')

    with app.app_context():
        print('=' * 60)
        print('⚠️  警告：即将删除所有数据！')
        print('=' * 60)

        confirm = input('确认删除所有数据？(yes/no): ')

        if confirm.lower() == 'yes':
            print('🗑️  删除所有数据表...')
            db.drop_all()
            print('✅ 数据表已删除')

            print('📊 重新创建数据表...')
            db.create_all()
            print('✅ 数据表创建完成')

            print('👤 重新创建管理员账号...')
            admin = User(
                username='admin',
                email='admin@docman.com',
                nickname='系统管理员',
                role='admin'
            )
            admin.set_password('admin123')
            from config import Config
            admin.storage_limit = Config.ADMIN_STORAGE_LIMIT

            db.session.add(admin)
            db.session.commit()
            print('✅ 管理员账号创建完成')

            print('=' * 60)
            print('✅ 数据库重置完成！')
            print('=' * 60)
        else:
            print('❌ 已取消操作')


def show_status():
    """
    显示数据库状态
    """
    app = create_app('development')

    with app.app_context():
        print('=' * 60)
        print('📊 数据库状态')
        print('=' * 60)

        # 统计用户数
        user_count = User.query.count()
        print(f'👤 用户数量: {user_count}')

        # 统计文件夹数
        folder_count = Folder.query.count()
        print(f'📁 文件夹数量: {folder_count}')

        # 统计文档数
        file_count = File.query.count()
        print(f'📄 文档数量: {file_count}')

        # 统计标签数
        tag_count = Tag.query.count()
        print(f'🏷️  标签数量: {tag_count}')

        # 统计分享数
        share_count = Share.query.count()
        print(f'🔗 分享数量: {share_count}')

        # 统计日志数
        log_count = Log.query.count()
        print(f'📝 日志数量: {log_count}')

        print('=' * 60)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'init':
            init_database()
        elif command == 'reset':
            reset_database()
        elif command == 'status':
            show_status()
        else:
            print('用法:')
            print('  python db_init.py init    # 初始化数据库')
            print('  python db_init.py reset   # 重置数据库（删除所有数据）')
            print('  python db_init.py status  # 查看数据库状态')
    else:
        # 默认执行初始化
        init_database()
