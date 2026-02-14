"""Daily job to update Telegram user information"""

import asyncio
import time

import httpx
from aiolimiter import AsyncLimiter
from beanie.odm.operators.update.general import Set

from src.config import settings
from src.logging_ import logger
from src.modules.telegram_update.schemas import TelegramUpdateData
from src.modules.users.repository import user_repository
from src.storages.mongo.models import User


async def update_telegram_info():
    """Update telegram info for all users with telegram_id"""
    if not settings.telegram:
        logger.warning("Telegram settings not configured, skipping telegram info update")
        return

    logger.info("Starting telegram info update job")
    start_time = time.monotonic()
    # Get all users with telegram_id
    users_dict = await user_repository.read_all_users_with_telegram_id()
    total_users = len(users_dict)
    logger.info(f"Found {total_users} users with telegram_id")

    if total_users == 0:
        return

    # Statistics
    errors_count = 0
    changes_count = 0
    same_count = 0

    # Rate limiter: 30 requests per second (Telegram Bot API limit)
    rate_limiter = AsyncLimiter(max_rate=10, time_period=1)
    # Semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(10)

    bot_token = settings.telegram.bot_token.get_secret_value()

    async with httpx.AsyncClient(timeout=60.0) as client:

        async def update_user(user_id, telegram_id):
            nonlocal errors_count, changes_count, same_count

            async with semaphore:
                async with rate_limiter:
                    try:
                        # Get chat info from Telegram
                        retries = 3
                        response: httpx.Response | None = None
                        while retries > 0:
                            response = await client.post(
                                f"https://api.telegram.org/bot{bot_token}/getChat", data={"chat_id": telegram_id}
                            )
                            if response.status_code == 429:
                                await asyncio.sleep(5)
                                retries -= 1
                            else:
                                break

                        assert response

                        if response.status_code == 200:
                            result = response.json().get("result", {})
                            telegram_update_data = TelegramUpdateData(
                                id=result.get("id"),
                                updated_at=int(time.time()),
                                success=True,
                                status_code=response.status_code,
                                error_message=None,
                                username=result.get("username"),
                                first_name=result.get("first_name"),
                                last_name=result.get("last_name"),
                            )
                        else:
                            # User blocked the bot or other error
                            errors_count += 1
                            logger.error(
                                f"Error for user {user_id} (telegram_id={telegram_id}): {response.status_code}, {response.text}"
                            )
                            telegram_update_data = TelegramUpdateData(
                                id=telegram_id,
                                updated_at=int(time.time()),
                                success=False,
                                status_code=response.status_code,
                                error_message=response.text,
                            )

                        user = await User.find_one(User.id == user_id)
                        if user is None:
                            logger.error(f"User {user_id} not found")
                            return None
                        existing_telegram_update_data = user.telegram_update_data
                        if telegram_update_data.success:
                            # check if relevant fields are different
                            changed = False
                            if existing_telegram_update_data:
                                if existing_telegram_update_data.username != telegram_update_data.username:
                                    changed = True
                                if existing_telegram_update_data.first_name != telegram_update_data.first_name:
                                    changed = True
                                if existing_telegram_update_data.last_name != telegram_update_data.last_name:
                                    changed = True
                            else:
                                changed = True
                            if changed:
                                await user.update(Set({User.telegram_update_data: telegram_update_data}))
                                changes_count += 1
                            else:
                                same_count += 1
                        elif (
                            (existing_telegram_update_data and not existing_telegram_update_data.success)
                            or not existing_telegram_update_data
                        ):  # we should save error only if previous update was not successful
                            await user.update(Set({User.telegram_update_data: telegram_update_data}))

                    except Exception as e:
                        errors_count += 1
                        logger.error(f"Error updating user {user_id}: {e}")

        # Create tasks for all users
        tasks = [update_user(user_id, telegram_id) for user_id, telegram_id in users_dict.items()]
        await asyncio.gather(*tasks)

    end_time = time.monotonic()
    duration = end_time - start_time
    logger.info(
        f"Telegram info update completed. Users: {total_users}, Changes: {changes_count}, Errors: {errors_count}, Same: {same_count}"
    )
    logger.info(f"Telegram info update completed in {duration:.2f} seconds")
