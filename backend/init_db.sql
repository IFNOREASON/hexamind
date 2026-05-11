-- HexaMind PostgreSQL DDL
-- 创建数据库: CREATE DATABASE hexamind;

-- 1. 文档来源表
CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(20) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_size INTEGER,
    file_path TEXT,
    url TEXT,
    content_text TEXT,
    content_hash VARCHAR(64),
    status VARCHAR(20) NOT NULL DEFAULT 'uploaded',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. 知识图谱节点表
CREATE TABLE IF NOT EXISTS graph_nodes (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    category VARCHAR(50) NOT NULL,
    color VARCHAR(10) DEFAULT '#60a5fa',
    size FLOAT DEFAULT 1.0,
    source_id INTEGER NOT NULL,
    source_type VARCHAR(20) DEFAULT 'document',
    community_id INTEGER,
    mastery FLOAT DEFAULT 0.0
);

-- 3. 知识图谱边表
CREATE TABLE IF NOT EXISTS graph_edges (
    id SERIAL PRIMARY KEY,
    source_node_id VARCHAR(64) NOT NULL,
    target_node_id VARCHAR(64) NOT NULL,
    relationship VARCHAR(100) NOT NULL,
    confidence VARCHAR(20) DEFAULT 'EXTRACTED',
    confidence_score FLOAT DEFAULT 1.0,
    weight FLOAT DEFAULT 1.0
);

-- 4. 超边表
CREATE TABLE IF NOT EXISTS hyperedges (
    id SERIAL PRIMARY KEY,
    label VARCHAR(255) NOT NULL,
    relation VARCHAR(100) NOT NULL,
    confidence VARCHAR(20) DEFAULT 'EXTRACTED',
    confidence_score FLOAT DEFAULT 1.0,
    node_ids JSON NOT NULL
);

-- 5. 学习任务表
CREATE TABLE IF NOT EXISTS learning_tasks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    node_id VARCHAR(64) NOT NULL REFERENCES graph_nodes(id),
    difficulty VARCHAR(10) NOT NULL DEFAULT 'medium',
    current_stage INTEGER NOT NULL DEFAULT 0,
    progress FLOAT NOT NULL DEFAULT 0.0,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- 6. 测验记录表
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES learning_tasks(id),
    stage_at_attempt INTEGER NOT NULL,
    questions JSON,
    answers JSON,
    score FLOAT,
    passed BOOLEAN,
    status VARCHAR(20) NOT NULL DEFAULT 'generating',
    error VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_learning_tasks_node_id ON learning_tasks(node_id);
CREATE INDEX IF NOT EXISTS idx_learning_tasks_status ON learning_tasks(status);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_task_id ON quiz_attempts(task_id);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_source_id ON graph_nodes(source_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_source ON graph_edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_target ON graph_edges(target_node_id);
