import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

logging.getLogger('telethon.client.downloads').setLevel(logging.WARNING)
logging.getLogger('telethon').setLevel(logging.WARNING) 