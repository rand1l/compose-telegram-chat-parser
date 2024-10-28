from .logging_setup import logger
import time


def log_execution(func):
    async def wrapper(*args, **kwargs):
        logger.info(f"Execution of {func.__name__} has begun.")
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"Execution of {func.__name__} completed in {end_time - start_time:.2f} seconds.")
        return result

    return wrapper
