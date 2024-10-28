from .minio_client import upload_file
from .db import AsyncSessionLocal
from .models import User, UserChat, Chat, UserHistory, Message
from sqlalchemy.future import select
from .logging_setup import logger
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone
import telethon
import asyncio


async def get_chats_for_worker(worker_id):
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Chat).where(Chat.worker == worker_id)
            )
            chats = result.scalars().all()

            await session.commit()
            return chats
        except Exception as e:
            logger.error(f"Ошибка при получении чатов для воркера {worker_id}: {e}")
            return []


async def get_last_message_id_for_chat(chat_id):
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Message.message_id).where(Message.chat_id == chat_id).order_by(Message.timestamp.desc()).limit(1)
            )
            last_message_id = result.scalar()
            if last_message_id:
                logger.info(f"last message for chat {chat_id} have ID {last_message_id}.")
            else:
                logger.info(f"В чате {chat_id} нет сообщений в базе данных.")
            return last_message_id
        except Exception as e:
            logger.error(f"Ошибка при получении последнего сообщения для чата {chat_id}: {e}")
            return None


async def update_chat_data(chat_id):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(select(Chat).where(Chat.id == chat_id))
            chat = result.scalar()

            if chat:
                session.add(chat)
                await session.commit()


async def store_data_in_db(user_chat_map, chat_details_map):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for user_id, chats in user_chat_map.items():
                result = await session.execute(select(User).where(User.id == user_id))
                user = result.scalar()

                if not user:
                    user = User(id=user_id)
                    session.add(user)

                for chat in chats:
                    result = await session.execute(select(Chat).where(Chat.id == chat.id))
                    db_chat = result.scalar()
                    if not db_chat:
                        chat_details = chat_details_map.get(chat.id)
                        if chat_details:
                            db_chat = Chat(
                                id=chat_details["id"],
                                title=chat_details["title"],
                                invite_link_id=chat_details["invite_link"]
                            )
                            session.add(db_chat)

                    result = await session.execute(
                        select(UserChat).where(UserChat.user_id == user_id, UserChat.chat_id == chat.id)
                    )
                    user_chat = result.scalar()
                    if not user_chat:
                        user_chat = UserChat(user_id=user_id, chat_id=chat.id)
                        session.add(user_chat)

            await session.commit()


async def update_user_data(user_id, first_name, last_name, username, deleted, premium):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(select(User).where(User.id == user_id).options(joinedload(User.history)))
            user = result.scalar()

            if not user:
                user = User(id=user_id, first_name=first_name, last_name=last_name,
                            username=username, deleted=deleted, premium=premium)
                session.add(user)
            else:
                new_history = UserHistory(user_id=user_id)

                data_changed = False

                if user.first_name != first_name:
                    new_history.first_name = user.first_name
                    user.first_name = first_name
                    data_changed = True

                if user.last_name != last_name:
                    new_history.last_name = user.last_name
                    user.last_name = last_name
                    data_changed = True

                if user.username != username:
                    new_history.username = user.username
                    user.username = username
                    data_changed = True

                if user.deleted != deleted:
                    new_history.deleted = user.deleted
                    user.deleted = deleted
                    data_changed = True

                if user.premium != premium:
                    new_history.premium = user.premium
                    user.premium = premium
                    data_changed = True

                if data_changed:
                    new_history.timestamp = datetime.utcnow()
                    session.add(new_history)

            await session.commit()


async def store_message_in_db(
        user_id, chat_id, message_id, message_text, timestamp, chat_title=None, user_data=None,
        reply_to_message_id=None, forwarded_from_user_id=None, forwarded_from_user_data=None, media=None, client=None
):
    """save only voice messages and circles to the database."""
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                if not message_text:
                    message_text = "[no text in message]"

                if timestamp.tzinfo is not None:
                    naive_timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)
                else:
                    naive_timestamp = timestamp

                result = await session.execute(select(User).where(User.id == user_id))
                user = result.scalar()

                if not user:
                    username = user_data.get("username") if user_data else None
                    first_name = user_data.get("first_name") if user_data else None
                    last_name = user_data.get("last_name") if user_data else None
                    new_user = User(
                        id=user_id,
                        username=username,
                        first_name=first_name,
                        last_name=last_name,
                        deleted=user_data.get("deleted", False) if user_data else False,
                        premium=user_data.get("premium", False) if user_data else False
                    )
                    session.add(new_user)
                    logger.info(f"Пользователь {user_id} добавлен в базу данных.")

                if forwarded_from_user_id:
                    result = await session.execute(select(User).where(User.id == forwarded_from_user_id))
                    forwarded_user = result.scalar()

                    if not forwarded_user:
                        forwarded_username = forwarded_from_user_data.get(
                            "username") if forwarded_from_user_data else None
                        forwarded_first_name = forwarded_from_user_data.get(
                            "first_name") if forwarded_from_user_data else None
                        forwarded_last_name = forwarded_from_user_data.get(
                            "last_name") if forwarded_from_user_data else None
                        new_forwarded_user = User(
                            id=forwarded_from_user_id,
                            username=forwarded_username,
                            first_name=forwarded_first_name,
                            last_name=forwarded_last_name,
                            deleted=forwarded_from_user_data.get("deleted",
                                                                 False) if forwarded_from_user_data else False,
                            premium=forwarded_from_user_data.get("premium",
                                                                 False) if forwarded_from_user_data else False
                        )
                        session.add(new_forwarded_user)

                result = await session.execute(select(Chat).where(Chat.id == chat_id))
                chat = result.scalar()

                if not chat:
                    if not chat_title:
                        chat_title = "[no title]"
                    new_chat = Chat(id=chat_id, title=chat_title)
                    session.add(new_chat)

                message_type = "text"
                file_url = None

                if media:
                    if isinstance(media, telethon.tl.types.MessageMediaDocument):
                        file_extension = None

                        for attribute in media.document.attributes:
                            if isinstance(attribute, telethon.tl.types.DocumentAttributeAudio) and attribute.voice:
                                message_type = "voice"
                                file_extension = 'ogg'
                                break
                            elif isinstance(attribute,
                                            telethon.tl.types.DocumentAttributeVideo) and attribute.round_message:
                                message_type = "round_video"
                                file_extension = 'mp4'
                                break

                        if message_type in ["voice", "round_video"]:
                            await asyncio.create_task(
                                download_and_store_media(client, media, chat_id, message_id, file_extension))
                        else:
                            return

                    else:
                        return

                new_message = Message(
                    user_id=user_id,
                    chat_id=chat_id,
                    message_id=message_id,
                    message_text=message_text,
                    timestamp=naive_timestamp,
                    file_url=file_url,
                    reply_to_message_id=reply_to_message_id,
                    forwarded_from_user_id=forwarded_from_user_id
                )
                session.add(new_message)

            await session.commit()

        except Exception as e:
            await session.rollback()
            logger.error(f"Error inserting message: {e}")


async def download_and_store_media(client, media, chat_id, message_id, extension):
    try:
        file_path = await client.download_media(media)
        file_url = upload_file(file_path, f"{chat_id}/{message_id}.{extension}")
        await update_message_with_file_url(message_id, file_url)
    except Exception as e:
        logger.error(f"Error loading media file for message {message_id}: {e}")


async def update_message_with_file_url(message_id, file_url):
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                result = await session.execute(select(Message).where(Message.message_id == message_id))
                message = result.scalar()

                if message:
                    message.file_url = file_url
                    session.add(message)

            await session.commit()

        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating file link for message {message_id}: {e}")
