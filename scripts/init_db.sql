-- ========================================
-- 智能文档管理系统 - 数据库初始化脚本
-- ========================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS doc_management DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE doc_management;

-- ========================================
-- 1. 用户表 (sys_user)
-- ========================================
DROP TABLE IF EXISTS sys_user;
CREATE TABLE sys_user (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(128) NOT NULL COMMENT '密码（加密）',
    email VARCHAR(100) UNIQUE COMMENT '邮箱',
    nickname VARCHAR(50) COMMENT '昵称',
    avatar VARCHAR(255) COMMENT '头像路径',
    role VARCHAR(20) DEFAULT 'user' COMMENT '角色：admin/user',
    status TINYINT DEFAULT 1 COMMENT '状态：1启用 0禁用',
    storage_limit BIGINT DEFAULT 1073741824 COMMENT '存储限制（字节）',
    storage_used BIGINT DEFAULT 0 COMMENT '已使用存储（字节）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- ========================================
-- 2. 文件夹表 (doc_folder)
-- ========================================
DROP TABLE IF EXISTS doc_folder;
CREATE TABLE doc_folder (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '文件夹ID',
    name VARCHAR(100) NOT NULL COMMENT '文件夹名称',
    parent_id INT DEFAULT 0 COMMENT '父文件夹ID（0为根目录）',
    user_id INT NOT NULL COMMENT '所属用户',
    path VARCHAR(500) COMMENT '完整路径',
    level INT DEFAULT 1 COMMENT '层级',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES sys_user(id) ON DELETE CASCADE,
    INDEX idx_user_parent (user_id, parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文件夹表';

-- ========================================
-- 3. 文档表 (doc_file)
-- ========================================
DROP TABLE IF EXISTS doc_file;
CREATE TABLE doc_file (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '文档ID',
    filename VARCHAR(255) NOT NULL COMMENT '文件名（含扩展名）',
    original_name VARCHAR(255) NOT NULL COMMENT '原始文件名',
    file_type VARCHAR(20) NOT NULL COMMENT '文件类型',
    file_size BIGINT NOT NULL COMMENT '文件大小（字节）',
    file_path VARCHAR(500) NOT NULL COMMENT '存储路径',
    folder_id INT DEFAULT 0 COMMENT '所属文件夹ID',
    user_id INT NOT NULL COMMENT '上传用户',
    file_hash VARCHAR(64) COMMENT '文件哈希值',
    version INT DEFAULT 1 COMMENT '当前版本号',
    download_count INT DEFAULT 0 COMMENT '下载次数',
    view_count INT DEFAULT 0 COMMENT '查看次数',
    is_deleted TINYINT DEFAULT 0 COMMENT '是否删除：1是 0否',
    deleted_at DATETIME COMMENT '删除时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES sys_user(id) ON DELETE CASCADE,
    FOREIGN KEY (folder_id) REFERENCES doc_folder(id) ON DELETE CASCADE,
    INDEX idx_user_folder (user_id, folder_id),
    INDEX idx_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档表';

-- ========================================
-- 4. 标签表 (doc_tag)
-- ========================================
DROP TABLE IF EXISTS doc_tag;
CREATE TABLE doc_tag (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '标签ID',
    name VARCHAR(50) NOT NULL COMMENT '标签名称',
    color VARCHAR(20) DEFAULT '#409EFF' COMMENT '标签颜色',
    user_id INT NOT NULL COMMENT '所属用户',
    use_count INT DEFAULT 0 COMMENT '使用次数',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (user_id) REFERENCES sys_user(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_name (user_id, name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='标签表';

-- ========================================
-- 5. 文档标签关联表 (doc_file_tag)
-- ========================================
DROP TABLE IF EXISTS doc_file_tag;
CREATE TABLE doc_file_tag (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    file_id INT NOT NULL COMMENT '文档ID',
    tag_id INT NOT NULL COMMENT '标签ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '关联时间',
    FOREIGN KEY (file_id) REFERENCES doc_file(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES doc_tag(id) ON DELETE CASCADE,
    UNIQUE KEY uk_file_tag (file_id, tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档标签关联表';

-- ========================================
-- 6. 版本表 (doc_version)
-- ========================================
DROP TABLE IF EXISTS doc_version;
CREATE TABLE doc_version (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '版本ID',
    file_id INT NOT NULL COMMENT '文档ID',
    version_number INT NOT NULL COMMENT '版本号',
    file_path VARCHAR(500) NOT NULL COMMENT '文件路径',
    file_size BIGINT NOT NULL COMMENT '文件大小',
    remark VARCHAR(255) COMMENT '版本说明',
    created_by INT NOT NULL COMMENT '创建用户',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (file_id) REFERENCES doc_file(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES sys_user(id),
    INDEX idx_file (file_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档版本表';

-- ========================================
-- 7. 分享表 (doc_share)
-- ========================================
DROP TABLE IF EXISTS doc_share;
CREATE TABLE doc_share (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '分享ID',
    share_code VARCHAR(32) NOT NULL UNIQUE COMMENT '分享码',
    file_id INT NOT NULL COMMENT '文档ID',
    share_password VARCHAR(50) COMMENT '分享密码',
    expire_days INT DEFAULT 0 COMMENT '有效天数（0为永久）',
    expire_time DATETIME COMMENT '过期时间',
    view_count INT DEFAULT 0 COMMENT '查看次数',
    download_count INT DEFAULT 0 COMMENT '下载次数',
    created_by INT NOT NULL COMMENT '创建用户',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (file_id) REFERENCES doc_file(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES sys_user(id),
    INDEX idx_code (share_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档分享表';

-- ========================================
-- 8. 权限表 (doc_permission)
-- ========================================
DROP TABLE IF EXISTS doc_permission;
CREATE TABLE doc_permission (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '权限ID',
    file_id INT NOT NULL COMMENT '文档ID',
    user_id INT COMMENT '用户ID（NULL表示公开）',
    permission_type VARCHAR(20) NOT NULL COMMENT '权限类型：read/write/admin',
    created_by INT NOT NULL COMMENT '授权用户',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (file_id) REFERENCES doc_file(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES sys_user(id),
    FOREIGN KEY (created_by) REFERENCES sys_user(id),
    INDEX idx_file_user (file_id, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档权限表';

-- ========================================
-- 9. 操作日志表 (sys_log)
-- ========================================
DROP TABLE IF EXISTS sys_log;
CREATE TABLE sys_log (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    user_id INT NOT NULL COMMENT '用户ID',
    action VARCHAR(50) NOT NULL COMMENT '操作类型',
    module VARCHAR(50) NOT NULL COMMENT '模块名称',
    description VARCHAR(255) COMMENT '操作描述',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (user_id) REFERENCES sys_user(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';

-- ========================================
-- 插入默认管理员账号
-- ========================================
-- 密码: admin123 (加密后的值)
INSERT INTO sys_user (username, password, email, nickname, role, storage_limit, storage_used)
VALUES ('admin',
        'pbkdf2:sha256:260000$salt$password_hash',
        'admin@docman.com',
        '系统管理员',
        'admin',
        10737418240,
        0)
ON DUPLICATE KEY UPDATE id=id;

-- ========================================
-- 完成
-- ========================================
SELECT '数据库初始化完成！' AS message;
