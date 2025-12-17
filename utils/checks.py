"""Công cụ kiểm tra quyền và xác thực"""
import logging
from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from config import CHANNEL_USERNAME

logger = logging.getLogger(__name__)


def is_group_chat(update: Update) -> bool:
    """Xác định xem có phải là trò chuyện nhóm không"""
    chat = update.effective_chat
    return chat and chat.type in ("group", "supergroup")


async def reject_group_command(update: Update) -> bool:
    """Hạn chế trò chuyện nhóm: Chỉ cho phép /verify /verify2 /verify3 /verify4 /verify5 /qd"""
    if is_group_chat(update):
        await update.message.reply_text("Trò chuyện nhóm chỉ hỗ trợ /verify /verify2 /verify3 /verify4 /verify5 /qd, vui lòng nhắn tin riêng để sử dụng các lệnh khác.")
        return True
    return False


async def check_channel_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Kiểm tra xem người dùng đã tham gia kênh chưa"""
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ["member", "administrator", "creator"]
    except TelegramError as e:
        logger.error("检查频道成员失败: %s", e)
        return False
