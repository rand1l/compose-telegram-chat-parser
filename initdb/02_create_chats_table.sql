CREATE TABLE IF NOT EXISTS chats (
    id BIGINT PRIMARY KEY,
    title VARCHAR(128) NOT NULL,
    worker BIGINT,
    invite_link_id VARCHAR(64),
    access_hash VARCHAR(64)
);  
