CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    message_id BIGINT NOT NULL,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    chat_id BIGINT REFERENCES chats(id) ON DELETE CASCADE,
    message_text TEXT NOT NULL,
    timestamp TIMESTAMP,
    file_url TEXT,
    reply_to_message_id BIGINT,
    forwarded_from_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL
);

