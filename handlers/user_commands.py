"""Trình xử lý lệnh người dùng"""
import logging
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_USER_ID
from database_mysql import Database
from utils.checks import reject_group_command
from utils.messages import (
    get_welcome_message,
    get_about_message,
    get_help_message,
)

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /start"""
    if await reject_group_command(update):
        return

    user = update.effective_user
    user_id = user.id
    username = user.username or ""
    full_name = user.full_name or ""

    # Nếu đã khởi tạo thì trả về
    if db.user_exists(user_id):
        await update.message.reply_text(
            f"Chào mừng trở lại, {full_name}!\n"
            "Bạn đã khởi tạo rồi.\n"
            "Gửi /help để xem các lệnh khả dụng."
        )
        return

    # Mời tham gia
    invited_by: Optional[int] = None
    if context.args:
        try:
            invited_by = int(context.args[0])
            if not db.user_exists(invited_by):
                invited_by = None
        except Exception:
            invited_by = None

    # Tạo người dùng
    if db.create_user(user_id, username, full_name, invited_by):
        welcome_msg = get_welcome_message(full_name, bool(invited_by))
        await update.message.reply_text(welcome_msg)
    else:
        await update.message.reply_text("Đăng ký thất bại, vui lòng thử lại sau.")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /about"""
    if await reject_group_command(update):
        return

    await update.message.reply_text(get_about_message())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /help"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id
    is_admin = user_id == ADMIN_USER_ID
    await update.message.reply_text(get_help_message(is_admin))


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /balance"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("Bạn đã bị chặn, không thể sử dụng tính năng này.")
        return

    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("Vui lòng sử dụng /start để đăng ký trước.")
        return

    await update.message.reply_text(
        f"💰 Số dư điểm\n\nĐiểm hiện tại: {user['balance']} điểm"
    )


async def checkin_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /qd điểm danh - Tạm thời vô hiệu hóa"""
    user_id = update.effective_user.id

    # Tạm thời vô hiệu hóa chức năng điểm danh (đang sửa lỗi)
    # await update.message.reply_text(
    #     "⚠️ Chức năng điểm danh đang bảo trì\n\n"
    #     "Do phát hiện lỗi, chức năng điểm danh tạm thời đóng để sửa chữa.\n"
    #     "Dự kiến sẽ sớm hoạt động lại, mong bạn thông cảm.\n\n"
    #     "💡 Bạn có thể nhận điểm qua:\n"
    #     "• Mời bạn bè /invite (+2 điểm)\n"
    #     "• Sử dụng mã thẻ /use <mã_thẻ>"
    # )
    # return
    
    # ===== Code dưới đây đã bị vô hiệu hóa (trong phiên bản gốc) =====
    if db.is_user_blocked(user_id):
        await update.message.reply_text("Bạn đã bị chặn, không thể sử dụng tính năng này.")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("Vui lòng sử dụng /start để đăng ký trước.")
        return

    # Kiểm tra lớp 1: Kiểm tra ở tầng xử lý lệnh
    if not db.can_checkin(user_id):
        await update.message.reply_text("❌ Hôm nay bạn đã điểm danh rồi, mai quay lại nhé.")
        return

    # Kiểm tra lớp 2: Thực thi ở tầng cơ sở dữ liệu (thao tác nguyên tử SQL)
    if db.checkin(user_id):
        user = db.get_user(user_id)
        await update.message.reply_text(
            f"✅ Điểm danh thành công!\nNhận được: +1 điểm\nĐiểm hiện tại: {user['balance']} điểm"
        )
    else:
        # Nếu tầng DB trả về False, nghĩa là hôm nay đã điểm danh (bảo hiểm kép)
        await update.message.reply_text("❌ Hôm nay bạn đã điểm danh rồi, mai quay lại nhé.")


async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /invite mời bạn bè"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("Bạn đã bị chặn, không thể sử dụng tính năng này.")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("Vui lòng sử dụng /start để đăng ký trước.")
        return

    bot_username = context.bot.username
    invite_link = f"https://t.me/{bot_username}?start={user_id}"

    await update.message.reply_text(
        f"🎁 Liên kết mời riêng của bạn:\n{invite_link}\n\n"
        "Mỗi khi mời 1 người đăng ký thành công, bạn sẽ nhận được 2 điểm."
    )


async def use_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /use - Sử dụng mã thẻ"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("Bạn đã bị chặn, không thể sử dụng tính năng này.")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("Vui lòng sử dụng /start để đăng ký trước.")
        return

    if not context.args:
        await update.message.reply_text(
            "Cách sử dụng: /use <Mã_Thẻ>\n\nVí dụ: /use wandouyu"
        )
        return

    key_code = context.args[0].strip()
    result = db.use_card_key(key_code, user_id)

    if result is None:
        await update.message.reply_text("Mã thẻ không tồn tại, vui lòng kiểm tra lại.")
    elif result == -1:
        await update.message.reply_text("Mã thẻ này đã đạt giới hạn số lần sử dụng.")
    elif result == -2:
        await update.message.reply_text("Mã thẻ này đã hết hạn.")
    elif result == -3:
        await update.message.reply_text("Bạn đã sử dụng mã thẻ này rồi.")
    else:
        user = db.get_user(user_id)
        await update.message.reply_text(
            f"Sử dụng mã thẻ thành công!\nNhận được: {result} điểm\nĐiểm hiện tại: {user['balance']} điểm"
        )
