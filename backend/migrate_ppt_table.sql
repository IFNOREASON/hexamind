-- PPT Generation Table Migration
-- 用于创建 ppt_generations 表

-- PostgreSQL
CREATE TABLE IF NOT EXISTS ppt_generations (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES learning_tasks(id),
    title VARCHAR(255) NOT NULL DEFAULT 'PPT课件',
    slides JSON,
    status VARCHAR(20) NOT NULL DEFAULT 'generating',
    error VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_ppt_generations_task_id ON ppt_generations(task_id);

-- SQLite 版本（如果使用 SQLite）
-- CREATE TABLE IF NOT EXISTS ppt_generations (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     task_id INTEGER NOT NULL,
--     title TEXT NOT NULL DEFAULT 'PPT课件',
--     slides TEXT,
--     status TEXT NOT NULL DEFAULT 'generating',
--     error TEXT,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (task_id) REFERENCES learning_tasks(id)
-- );
