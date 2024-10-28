-- Таблица для связывания пользователей и чатов
CREATE TABLE IF NOT EXISTS user_chat (
    user_id BIGINT REFERENCES users(id),
    chat_id BIGINT REFERENCES chats(id),
    PRIMARY KEY (user_id, chat_id)
);
