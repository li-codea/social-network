-- ============================================================
-- 社交网络好友推荐系统 — 数据库初始化脚本
-- 容器首次启动时由 /docker-entrypoint-initdb.d/ 自动执行
-- ============================================================

-- 关键：设置客户端连接字符集为 utf8mb4，防止中文乱码
SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS social_network
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE social_network;

-- -----------------------------------------------------------
-- 用户表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id          INT           AUTO_INCREMENT PRIMARY KEY  COMMENT '用户主键ID',
    username    VARCHAR(50)   NOT NULL UNIQUE              COMMENT '唯一用户名，用于登录',
    nickname    VARCHAR(100)  DEFAULT NULL                 COMMENT '显示昵称',
    avatar_url  VARCHAR(500)  DEFAULT NULL                 COMMENT '头像图片URL',
    bio         TEXT          DEFAULT NULL                 COMMENT '个人简介',
    tags        JSON          DEFAULT (JSON_ARRAY())       COMMENT '兴趣标签 JSON 数组',
    created_at  DATETIME      DEFAULT CURRENT_TIMESTAMP    COMMENT '注册时间',
    updated_at  DATETIME      DEFAULT CURRENT_TIMESTAMP
                              ON UPDATE CURRENT_TIMESTAMP  COMMENT '最后更新时间',

    INDEX idx_users_nickname    (nickname),
    INDEX idx_users_created_at  (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- -----------------------------------------------------------
-- 无向好友关系表
-- user_id < friend_id 由 CHECK 约束强制执行，保证每对只有一条记录
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS friendships (
    id          INT       AUTO_INCREMENT PRIMARY KEY  COMMENT '关系主键ID',
    user_id     INT       NOT NULL                    COMMENT '较小ID的用户',
    friend_id   INT       NOT NULL                    COMMENT '较大ID的用户',
    created_at  DATETIME  DEFAULT CURRENT_TIMESTAMP   COMMENT '好友关系建立时间',

    -- 外键：删除用户时级联删除其好友关系
    CONSTRAINT fk_friendship_user
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_friendship_friend
        FOREIGN KEY (friend_id) REFERENCES users (id) ON DELETE CASCADE,

    -- 保证每对用户只有一条好友记录
    CONSTRAINT uq_friendship_pair UNIQUE (user_id, friend_id),
    -- 保证 user_id 始终小于 friend_id（无向约束）
    CONSTRAINT ck_user_lt_friend CHECK (user_id < friend_id),

    INDEX idx_friendship_user_id   (user_id),
    INDEX idx_friendship_friend_id (friend_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='无向好友关系表';

-- -----------------------------------------------------------
-- 示例数据（可选，方便测试）
-- -----------------------------------------------------------
INSERT INTO users (username, nickname, bio, tags) VALUES
('alice',  'Alice',  '喜欢摄影和旅行',   '["摄影", "旅行", "Python"]'),
('bob',    'Bob',    '后端开发工程师',    '["Python", "机器学习", "游戏"]'),
('charlie','Charlie','全栈开发者',        '["JavaScript", "Python", "摄影"]'),
('diana',  'Diana',  '数据科学爱好者',   '["机器学习", "Python", "数学"]'),
('eve',    'Eve',    'UI/UX 设计师',     '["设计", "摄影", "旅行"]');

-- Alice & Bob 互为好友；Alice & Charlie 互为好友；Bob & Diana 互为好友
INSERT INTO friendships (user_id, friend_id) VALUES
(1, 2),   -- Alice ↔ Bob
(1, 3),   -- Alice ↔ Charlie
(2, 4);   -- Bob ↔ Diana
