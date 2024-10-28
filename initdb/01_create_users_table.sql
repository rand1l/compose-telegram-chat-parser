CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    first_name VARCHAR(64),
    last_name VARCHAR(64),
    username VARCHAR(32),
    deleted BOOLEAN,
    premium BOOLEAN,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
