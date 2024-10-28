CREATE TABLE IF NOT EXISTS user_history (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(128),
    last_name VARCHAR(128),
    username VARCHAR(64),
    deleted BOOLEAN,
    premium BOOLEAN,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
