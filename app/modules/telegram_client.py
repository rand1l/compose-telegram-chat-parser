import asyncio

import telethon
from telethon.errors import ChannelPrivateError, ChatAdminRequiredError, InviteHashExpiredError, PeerIdInvalidError, \
    FloodWaitError
from telethon.tl.functions.channels import GetForumTopicsRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import Channel

from .db_operations import update_user_data, store_message_in_db, get_last_message_id_for_chat, get_chats_for_worker
from .logging_setup import logger


async def get_chat_details(client, chat_id):
    """Get detailed information about a chat"""
    try:
        chat = await client.get_entity(chat_id)

        if chat.username is not None:
            print("Dialog is public")
            is_private = False
        else:
            print("Dialog is private")
            is_private = True

        is_forum = getattr(chat, 'forum', False)

        if isinstance(chat, telethon.tl.types.Channel):
            details = {
                "id": chat.id,
                "title": chat.title,
                "is_closed": chat.restricted,
                "invite_link_id": None,
                "is_private": is_private,
                "is_forum": is_forum
            }
        elif isinstance(chat, telethon.tl.types.Chat):
            details = {
                "id": chat.id,
                "title": chat.title,
                "is_closed": False,
                "invite_link_id": None,
                "is_private": is_private,
                "is_forum": is_forum
            }
        else:
            details = None
        return details
    except Exception as e:
        logger.error(f"Error getting chat information {chat_id}: {e}")
        return None


async def gather_all_users(client, worker_id, batch_size=100):
    """get information about users from all chats and collect information about chats in the form of a dictionary."""
    chat_details_map = {}
    
    chats = await get_chats_for_worker(worker_id)
    
    user_chat_map = {}

    for chat in chats:
        try:
            if chat.id not in chat_details_map:
                chat_details = await get_chat_details(client, chat.id)
                if chat_details:
                    chat_details_map[chat.id] = chat_details

            if chat_details_map[chat.id]["is_forum"]:
                topics = await get_forum_topics(client, chat.id)
                for topic in topics:
                    users = await get_chat_users(client, topic, batch_size, chat.invite_link_id)
                    for user_id in users:
                        await update_user_info_in_map(client, user_id, user_chat_map, chat)
            else:
                users = await get_chat_users(client, chat, batch_size, chat.invite_link_id)
                for user_id in users:
                    await update_user_info_in_map(client, user_id, user_chat_map, chat)

        except Exception as e:
            logger.error(f"Error processing the chat {chat.title}: {e}")
            continue
        except FloodWaitError as e:
            logger.warning(f"Telegram request limit exceeded, waiting {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)  

    return user_chat_map, chat_details_map


async def get_forum_topics(client, chat_id):
    topics = []
    try:
        result = await client(GetForumTopicsRequest(
            channel=chat_id,
            offset_date=None,
            offset_id=0,
            offset_topic=0,
            limit=100,
            q=''
        ))
        topics = result.topics
    except Exception as e:
        logger.error(f"Error getting topics for forum {chat_id}: {e}")
    return topics


async def update_user_info_in_map(client, user_id, user_chat_map, chat):
    try:
        user_info = await client.get_entity(user_id)
        if isinstance(user_info, telethon.tl.types.User):
            await update_user_data(
                user_info.id,
                user_info.first_name,
                user_info.last_name,
                user_info.username,
                user_info.deleted,
                user_info.premium
            )
            if user_info.id not in user_chat_map:
                user_chat_map[user_info.id] = []
            user_chat_map[user_info.id].append(chat)
    except Exception as user_exc:
        logger.error(f"Error getting user information {user_id}: {user_exc}")


async def join_closed_chat_if_needed(client, chat):
    try:
        async for dialog in client.iter_dialogs():
            if dialog.id == chat.id:
                return

        if chat.access_hash:
            invite_hash = chat.access_hash
            await client(ImportChatInviteRequest(invite_hash))
        else:
            logger.warning(f"There is no invite link for chat {chat.title}.")
    except Exception as e:
        logger.error(f"Error joining private chat {chat.title}: {e}")


async def get_chat_users(client, chat, batch_size=500, invite_link_id=None):
    """Get users from messages in chat or forum topic."""
    user_ids = set()

    last_message_id = await get_last_message_id_for_chat(chat.id)
    offset_id = last_message_id if last_message_id else 0
    total_messages = 0

    if invite_link_id:
        try:
            peer = await client.get_entity(invite_link_id)
        except Exception as e:
            logger.error(f"Error when receiving public chat {chat.title} by invite_link_id: {e}")
            return user_ids
    else: 
        await join_closed_chat_if_needed(client, chat)
        peer = telethon.tl.types.PeerChannel(channel_id=chat.id)
        try:
            await client.get_input_entity(peer)
        except Exception as e:
            logger.error(f"Error receiving private chat entity {chat.title}: {e}")
            return user_ids

    while True:
        messages = []
        try:
            async for message in client.iter_messages(peer, limit=batch_size, offset_id=offset_id, reverse=True):
                messages.append(message)
        except ChannelPrivateError:
            try:
                await join_closed_chat_if_needed(client, chat)
                return await get_chat_users(client, chat, batch_size)
            except Exception as join_error:
                logger.error(f"Error trying to join private chat {chat.title}: {join_error}")
                break
        except ChatAdminRequiredError:
            logger.error(f"Administrator rights are required to access messages in chat {chat.title}")
            break
        except InviteHashExpiredError:
            logger.error(f"The invitation link for chat {chat.title} is invalid")
            break
        except PeerIdInvalidError:
            logger.error(f"Invalid chat id {chat.title}")
            break
        except Exception as e:
            logger.error(f"Error receiving messages from chat {chat.title}: {e}")
            break

        if not messages:
            break

        for message in messages:
            if message.sender_id:
                user_ids.add(message.sender_id)

                sender = message.sender
                user_data = {
                    "username": sender.username if isinstance(sender, telethon.tl.types.User) else None,
                    "first_name": sender.first_name if isinstance(sender, telethon.tl.types.User) else None,
                    "last_name": sender.last_name if isinstance(sender, telethon.tl.types.User) else None,
                    "deleted": sender.deleted if isinstance(sender, telethon.tl.types.User) else False,
                    "premium": sender.premium if isinstance(sender, telethon.tl.types.User) else False
                }

                await store_message_in_db(
                    user_id=message.sender_id,
                    chat_id=chat.id,
                    message_id=message.id,
                    message_text=message.message,
                    timestamp=message.date,
                    chat_title=chat.title,
                    user_data=user_data,
                    reply_to_message_id=message.reply_to_msg_id if message.is_reply else None,
                    forwarded_from_user_id=message.forward.sender_id if message.forward else None,
                    media=message.media,
                    client=client
                )

            offset_id = message.id

        total_messages += len(messages)

        await asyncio.sleep(1)

    return user_ids
