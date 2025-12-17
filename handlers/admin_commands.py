"""Trình xử lý lệnh quản trị viên"""
import asyncio
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_USER_ID
from database_mysql import Database
from utils.checks import reject_group_command

logger = logging.getLogger(__name__)


async def addbalance_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /addbalance - Quản trị viên thêm điểm"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Cách sử dụng: /addbalance <ID_Người_Dùng> <Số_Điểm>\n\nVí dụ: /addbalance 123456789 10"
        )
        return

    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])

        if not db.user_exists(target_user_id):
            await update.message.reply_text("Người dùng không tồn tại.")
            return

        if db.add_balance(target_user_id, amount):
            user = db.get_user(target_user_id)
            await update.message.reply_text(
                f"✅ Đã thêm {amount} điểm cho người dùng {target_user_id}.\n"
                f"Điểm hiện tại: {user['balance']}"
            )
        else:
            await update.message.reply_text("Thao tác thất bại, vui lòng thử lại sau.")
    except ValueError:
        await update.message.reply_text("Định dạng tham số sai, vui lòng nhập số hợp lệ.")


async def block_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /block - Quản trị viên chặn người dùng"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if not context.args:
        await update.message.reply_text(
            "Cách sử dụng: /block <ID_Người_Dùng>\n\nVí dụ: /block 123456789"
        )
        return

    try:
        target_user_id = int(context.args[0])

        if not db.user_exists(target_user_id):
            await update.message.reply_text("Người dùng không tồn tại.")
            return

        if db.block_user(target_user_id):
            await update.message.reply_text(f"✅ Đã chặn người dùng {target_user_id}.")
        else:
            await update.message.reply_text("Thao tác thất bại, vui lòng thử lại sau.")
    except ValueError:
        await update.message.reply_text("Định dạng tham số sai, vui lòng nhập ID người dùng hợp lệ.")


async def white_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /white - Quản trị viên bỏ chặn"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if not context.args:
        await update.message.reply_text(
            "Cách sử dụng: /white <ID_Người_Dùng>\n\nVí dụ: /white 123456789"
        )
        return

    try:
        target_user_id = int(context.args[0])

        if not db.user_exists(target_user_id):
            await update.message.reply_text("Người dùng không tồn tại.")
            return

        if db.unblock_user(target_user_id):
            await update.message.reply_text(f"✅ Đã xóa người dùng {target_user_id} khỏi danh sách đen.")
        else:
            await update.message.reply_text("Thao tác thất bại, vui lòng thử lại sau.")
    except ValueError:
        await update.message.reply_text("Định dạng tham số sai, vui lòng nhập ID người dùng hợp lệ.")


async def blacklist_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /blacklist - Xem danh sách đen"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    blacklist = db.get_blacklist()

    if not blacklist:
        await update.message.reply_text("Danh sách đen trống.")
        return

    msg = "📋 Danh sách đen:\n\n"
    for user in blacklist:
        msg += f"ID: {user['user_id']}\n"
        msg += f"Username: @{user['username']}\n"
        msg += f"Họ tên: {user['full_name']}\n"
        msg += "---\n"

    await update.message.reply_text(msg)


async def genkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /genkey - Quản trị viên tạo mã thẻ"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Cách sử dụng: /genkey <Mã_Thẻ> <Điểm> [Số_Lần] [Số_Ngày]\n\n"
            "Ví dụ:\n"
            "/genkey wandouyu 20 - Tạo mã thẻ 20 điểm (dùng 1 lần, vĩnh viễn)\n"
            "/genkey vip100 50 10 - Tạo mã thẻ 50 điểm (dùng 10 lần, vĩnh viễn)\n"
            "/genkey temp 30 1 7 - Tạo mã thẻ 30 điểm (dùng 1 lần, hết hạn sau 7 ngày)"
        )
        return

    try:
        key_code = context.args[0].strip()
        balance = int(context.args[1])
        max_uses = int(context.args[2]) if len(context.args) > 2 else 1
        expire_days = int(context.args[3]) if len(context.args) > 3 else None

        if balance <= 0:
            await update.message.reply_text("Số điểm phải lớn hơn 0.")
            return

        if max_uses <= 0:
            await update.message.reply_text("Số lần sử dụng phải lớn hơn 0.")
            return

        if db.create_card_key(key_code, balance, user_id, max_uses, expire_days):
            msg = (
                "✅ Tạo mã thẻ thành công!\n\n"
                f"Mã thẻ: {key_code}\n"
                f"Điểm: {balance}\n"
                f"Số lần dùng: {max_uses} lần\n"
            )
            if expire_days:
                msg += f"Hạn dùng: {expire_days} ngày\n"
            else:
                msg += "Hạn dùng: Vĩnh viễn\n"
            msg += f"\nCách dùng cho user: /use {key_code}"
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("Mã thẻ đã tồn tại hoặc tạo thất bại, vui lòng đổi tên mã.")
    except ValueError:
        await update.message.reply_text("Định dạng tham số sai, vui lòng nhập số hợp lệ.")


async def listkeys_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /listkeys - Quản trị viên xem danh sách mã thẻ"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    keys = db.get_all_card_keys()

    if not keys:
        await update.message.reply_text("Hiện không có mã thẻ nào.")
        return

    msg = "📋 Danh sách mã thẻ:\n\n"
    for key in keys[:20]:  # Chỉ hiển thị 20 mã đầu
        msg += f"Mã: {key['key_code']}\n"
        msg += f"Điểm: {key['balance']}\n"
        msg += f"Sử dụng: {key['current_uses']}/{key['max_uses']}\n"

        if key["expire_at"]:
            expire_time = datetime.fromisoformat(key["expire_at"])
            if datetime.now() > expire_time:
                msg += "Trạng thái: Đã hết hạn\n"
            else:
                days_left = (expire_time - datetime.now()).days
                msg += f"Trạng thái: Còn hiệu lực ({days_left} ngày còn lại)\n"
        else:
            msg += "Trạng thái: Vĩnh viễn\n"

        msg += "---\n"

    if len(keys) > 20:
        msg += f"\n(Chỉ hiển thị 20 mã đầu, tổng cộng {len(keys)} mã)"

    await update.message.reply_text(msg)


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /broadcast - Quản trị viên gửi thông báo hàng loạt"""
    if await reject_group_command(update):
        return

    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    text = " ".join(context.args).strip() if context.args else ""
    if not text and update.message.reply_to_message:
        text = update.message.reply_to_message.text or ""

    if not text:
        await update.message.reply_text("Cách sử dụng: /broadcast <Văn bản>, hoặc trả lời một tin nhắn rồi gửi /broadcast")
        return

    user_ids = db.get_all_user_ids()
    success, failed = 0, 0

    status_msg = await update.message.reply_text(f"📢 Bắt đầu phát sóng, tổng cộng {len(user_ids)} người dùng...")

    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
            success += 1
            await asyncio.sleep(0.05)  # Giới hạn tốc độ để tránh bị chặn
        except Exception as e:
            logger.warning("Phát sóng thất bại đến %s: %s", uid, e)
            failed += 1

    await status_msg.edit_text(f"✅ Phát sóng hoàn tất!\nThành công: {success}\nThất bại: {failed}")
