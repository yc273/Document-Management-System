# 智能文档管理系统 - 后端

Flask后端API服务，支持局域网访问。

## 📁 项目结构

```
backend/
├── app/                        # 应用主目录
│   ├── __init__.py           # 应用工厂
│   ├── config.py             # 配置文件
│   ├── extensions.py         # 扩展插件
│   ├── models/               # 数据模型
│   │   ├── user.py          # 用户模型
│   │   ├── folder.py        # 文件夹模型
│   │   ├── file.py          # 文档模型
│   │   ├── tag.py           # 标签模型
│   │   ├── file_tag.py      # 文档标签关联模型
│   │   ├── version.py       # 版本模型
│   │   ├── share.py         # 分享模型
│   │   └── log.py           # 日志模型
│   └── utils/                # 工具类
│       ├── response.py      # 响应封装
│       ├── file_util.py     # 文件工具
│       └── auth_util.py     # 认证工具
├── uploads/                   # 文件上传目录
│   ├── documents/           # 文档文件
│   ├── avatars/             # 用户头像
│   └── temp/                # 临时文件
├── requirements.txt          # Python依赖
├── run.py                   # 启动文件
├── db_init.py               # 数据库初始化
└── README.md                # 本文件
```

## 🛠️ 技术栈

- **Python 3.8+**
- **Flask 2.3** - Web框架
- **Flask-SQLAlchemy** - ORM
- **Flask-Login** - 用户认证
- **Flask-CORS** - 跨域支持
- **PyMySQL** - MySQL驱动
- **MySQL 5.7+** - 数据库

## 📦 安装步骤

### 1. 安装Python依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置MySQL数据库

创建数据库：

```sql
CREATE DATABASE doc_management DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

修改 `app/config.py` 中的数据库配置：

```python
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'your_password'
MYSQL_DB = 'doc_management'
```

### 3. 初始化数据库

```bash
python db_init.py init
```

或使用SQL脚本：

```bash
mysql -u root -p doc_management < ../scripts/init_db.sql
```

### 4. 启动应用

```bash
python run.py
```

## 🚀 访问地址

启动成功后，可通过以下地址访问：

- **本地访问**: http://localhost:5000
- **本机访问**: http://127.0.0.1:5000
- **局域网访问**: http://<本机IP>:5000

### 查看本机IP

运行启动文件时，会自动显示本机局域网IP。

或手动查看：

**Windows:**
```bash
ipconfig
```

**Mac/Linux:**
```bash
ifconfig 或 ip addr
```

## 📋 默认账号

```
用户名: admin
密码: admin123
```

**⚠️ 重要提示：首次使用请立即修改管理员密码！**

## 🔌 API接口

### 健康检查
- `GET /` - API信息
- `GET /health` - 健康检查

### 响应格式

```json
{
    "code": 200,
    "message": "success",
    "data": {},
    "timestamp": 1234567890
}
```

## 📂 上传目录

应用会自动创建以下目录：

- `uploads/documents/` - 文档存储
- `uploads/avatars/` - 用户头像
- `uploads/temp/` - 临时文件
- `logs/` - 日志文件

## 🔧 配置说明

### 开发环境

默认使用开发环境配置，可在 `run.py` 中修改：

```python
app = create_app('development')
```

### 生产环境

修改为：

```python
app = create_app('production')
```

并设置环境变量：

```bash
export SECRET_KEY='your-secret-key'
export MYSQL_PASSWORD='your-password'
```

## 🔐 局域网访问配置

### 关键配置

在 `run.py` 中已配置：

```python
host = '0.0.0.0'  # 允许外部访问（关键配置）
port = 5000       # 端口号
```

### 防火墙设置

**Windows:**

首次运行会弹出防火墙提示，选择"允许访问"。

**Mac/Linux:**

```bash
sudo ufw allow 5000
```

### 测试局域网访问

1. 查看本机IP（如：192.168.1.100）
2. 手机连接同一WiFi
3. 浏览器访问：http://192.168.1.100:5000

## 📝 数据库管理

### 查看数据库状态

```bash
python db_init.py status
```

### 重置数据库（开发环境）

```bash
python db_init.py reset
```

**⚠️ 危险操作：会删除所有数据！**

## 🛡️ 安全建议

1. **修改默认密码**
   - 首次登录后立即修改admin密码

2. **设置SECRET_KEY**
   - 生产环境必须设置随机的SECRET_KEY

3. **数据库密码**
   - 使用强密码
   - 不要在代码中硬编码

4. **文件上传限制**
   - 已在config.py中配置文件大小限制（100MB）
   - 可根据需要调整

## 📊 代码统计

- 配置文件: ~100行
- 数据模型: ~800行
- 工具类: ~200行
- 启动文件: ~50行

**总计：约1350行代码**

## 🔍 调试模式

开发环境默认开启调试模式：

```python
debug = True  # 显示详细错误信息
```

生产环境请设置为 `False`。

## 📞 常见问题

### 1. 数据库连接失败

检查MySQL是否启动：

```bash
# Windows
net start mysql

# Mac/Linux
sudo service mysql start
```

### 2. 端口被占用

修改 `run.py` 中的端口号：

```python
port = 5001  # 改为其他端口
```

### 3. 局域网无法访问

- 确认设备连接同一WiFi
- 检查防火墙设置
- 确认host='0.0.0.0'配置

### 4. 文件上传失败

检查uploads目录权限：

```bash
chmod -R 755 uploads/
```

## 📄 许可证

MIT License

---

**开发时间**: 2024年
**版本**: v1.0.0
