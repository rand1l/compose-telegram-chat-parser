import random
import asyncio
from modules.telegram_client import gather_all_users
from modules.db_operations import store_data_in_db
from modules.logging_setup import logger
from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from modules.config import Config

client = TelegramClient(Config.SESSION_NAME, Config.API_ID, Config.API_HASH)


async def main():
    try:
        await client.start()
    except FloodWaitError as e:
        logger.warning(f"Request limit exceeded, waiting {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)
        await client.start()

    async with client:
        me = await client.get_me()
        worker_id = me.id

        while True:
            try:
                user_chat_map, chat_details_map = await gather_all_users(client, worker_id, batch_size=500)
                break
            except FloodWaitError as e:
                logger.warning(f"Request limit exceeded, waiting {e.seconds} seconds...")
                await asyncio.sleep(e.seconds)
            except SessionPasswordNeededError:
                logger.error("Password required for two-factor authentication.")
                break
            except Exception as e:
                logger.error(f"Error collecting data: {e}. Trying again in 10 seconds...")
                await asyncio.sleep(10)

            await asyncio.sleep(random.uniform(1, 3))

        await store_data_in_db(user_chat_map, chat_details_map)

if __name__ == '__main__':
    asyncio.run(main())
