"""Trình xử lý lệnh xác thực"""
import asyncio
import logging
import httpx
import time
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from config import VERIFY_COST
from database_mysql import Database
from one.sheerid_verifier import SheerIDVerifier as OneVerifier
from k12.sheerid_verifier import SheerIDVerifier as K12Verifier
from spotify.sheerid_verifier import SheerIDVerifier as SpotifyVerifier
from youtube.sheerid_verifier import SheerIDVerifier as YouTubeVerifier
from Boltnew.sheerid_verifier import SheerIDVerifier as BoltnewVerifier
from utils.messages import get_insufficient_balance_message, get_verify_usage_message

# Thử import kiểm soát đồng thời, nếu thất bại thì dùng cài đặt rỗng
try:
    from utils.concurrency import get_verification_semaphore
except ImportError:
    # Nếu import thất bại, tạo một cài đặt đơn giản
    def get_verification_semaphore(verification_type: str):
        return asyncio.Semaphore(3)

logger = logging.getLogger(__name__)


async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /verify - Gemini One Pro"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("Bạn đã bị chặn, không thể sử dụng tính năng này.")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("Vui lòng sử dụng /start để đăng ký trước.")
        return

    if not context.args:
        await update.message.reply_text(
            get_verify_usage_message("/verify", "Gemini One Pro")
        )
        return

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(
            get_insufficient_balance_message(user["balance"])
        )
        return

    verification_id = OneVerifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("Liên kết SheerID không hợp lệ, vui lòng kiểm tra lại.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Trừ điểm thất bại, vui lòng thử lại sau.")
        return

    processing_msg = await update.message.reply_text(
        f"Đang bắt đầu xử lý xác thực Gemini One Pro...\n"
        f"ID xác thực: {verification_id}\n"
        f"Đã trừ {VERIFY_COST} điểm\n\n"
        "Vui lòng đợi, quá trình này có thể mất 1-2 phút..."
    )

    try:
        verifier = OneVerifier(verification_id)
        result = await asyncio.to_thread(verifier.verify)

        db.add_verification(
            user_id,
            "gemini_one_pro",
            url,
            "success" if result["success"] else "failed",
            str(result),
        )

        if result["success"]:
            result_msg = "✅ Xác thực thành công!\n\n"
            if result.get("pending"):
                result_msg += "Tài liệu đã được gửi, đang chờ duyệt thủ công.\n"
            if result.get("redirect_url"):
                result_msg += f"Liên kết chuyển hướng:\n{result['redirect_url']}"
            await processing_msg.edit_text(result_msg)
        else:
            db.add_balance(user_id, VERIFY_COST)
            await processing_msg.edit_text(
                f"❌ Xác thực thất bại: {result.get('message', 'Lỗi không xác định')}\n\n"
                f"Đã hoàn lại {VERIFY_COST} điểm"
            )
    except Exception as e:
        logger.error("Lỗi quá trình xác thực: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        await processing_msg.edit_text(
            f"❌ Có lỗi xảy ra trong quá trình xử lý: {str(e)}\n\n"
            f"Đã hoàn lại {VERIFY_COST} điểm"
        )


async def verify2_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /verify2 - ChatGPT Teacher K12"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("Bạn đã bị chặn, không thể sử dụng tính năng này.")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("Vui lòng sử dụng /start để đăng ký trước.")
        return

    if not context.args:
        await update.message.reply_text(
            get_verify_usage_message("/verify2", "ChatGPT Teacher K12")
        )
        return

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(
            get_insufficient_balance_message(user["balance"])
        )
        return

    verification_id = K12Verifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("Liên kết SheerID không hợp lệ, vui lòng kiểm tra lại.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Trừ điểm thất bại, vui lòng thử lại sau.")
        return

    processing_msg = await update.message.reply_text(
        f"Đang bắt đầu xử lý xác thực ChatGPT Teacher K12...\n"
        f"ID xác thực: {verification_id}\n"
        f"Đã trừ {VERIFY_COST} điểm\n\n"
        "Vui lòng đợi, quá trình này có thể mất 1-2 phút..."
    )

    try:
        verifier = K12Verifier(verification_id)
        result = await asyncio.to_thread(verifier.verify)

        db.add_verification(
            user_id,
            "chatgpt_teacher_k12",
            url,
            "success" if result["success"] else "failed",
            str(result),
        )

        if result["success"]:
            result_msg = "✅ Xác thực thành công!\n\n"
            if result.get("pending"):
                result_msg += "Tài liệu đã được gửi, đang chờ duyệt thủ công.\n"
            if result.get("redirect_url"):
                result_msg += f"Liên kết chuyển hướng:\n{result['redirect_url']}"
            await processing_msg.edit_text(result_msg)
        else:
            db.add_balance(user_id, VERIFY_COST)
            await processing_msg.edit_text(
                f"❌ Xác thực thất bại: {result.get('message', 'Lỗi không xác định')}\n\n"
                f"Đã hoàn lại {VERIFY_COST} điểm"
            )
    except Exception as e:
        logger.error("Lỗi quá trình xác thực: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        await processing_msg.edit_text(
            f"❌ Có lỗi xảy ra trong quá trình xử lý: {str(e)}\n\n"
            f"Đã hoàn lại {VERIFY_COST} điểm"
        )


async def verify3_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /verify3 - Spotify Student"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("Bạn đã bị chặn, không thể sử dụng tính năng này.")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("Vui lòng sử dụng /start để đăng ký trước.")
        return

    if not context.args:
        await update.message.reply_text(
            get_verify_usage_message("/verify3", "Spotify Student")
        )
        return

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(
            get_insufficient_balance_message(user["balance"])
        )
        return

    # Phân tích verificationId
    verification_id = SpotifyVerifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("Liên kết SheerID không hợp lệ, vui lòng kiểm tra lại.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Trừ điểm thất bại, vui lòng thử lại sau.")
        return

    processing_msg = await update.message.reply_text(
        f"🎵 Đang bắt đầu xử lý xác thực Spotify Student...\n"
        f"Đã trừ {VERIFY_COST} điểm\n\n"
        "📝 Đang tạo thông tin sinh viên...\n"
        "🎨 Đang tạo ảnh thẻ sinh viên PNG...\n"
        "📤 Đang gửi tài liệu..."
    )

    # Sử dụng semaphore để kiểm soát đồng thời
    semaphore = get_verification_semaphore("spotify_student")

    try:
        async with semaphore:
            verifier = SpotifyVerifier(verification_id)
            result = await asyncio.to_thread(verifier.verify)

        db.add_verification(
            user_id,
            "spotify_student",
            url,
            "success" if result["success"] else "failed",
            str(result),
        )

        if result["success"]:
            result_msg = "✅ Xác thực Spotify Student thành công!\n\n"
            if result.get("pending"):
                result_msg += "✨ Tài liệu đã được gửi, đang chờ SheerID duyệt\n"
                result_msg += "⏱️ Thời gian duyệt dự kiến: trong vài phút\n\n"
            if result.get("redirect_url"):
                result_msg += f"🔗 Liên kết chuyển hướng:\n{result['redirect_url']}"
            await processing_msg.edit_text(result_msg)
        else:
            db.add_balance(user_id, VERIFY_COST)
            await processing_msg.edit_text(
                f"❌ Xác thực thất bại: {result.get('message', 'Lỗi không xác định')}\n\n"
                f"Đã hoàn lại {VERIFY_COST} điểm"
            )
    except Exception as e:
        logger.error("Lỗi quá trình xác thực Spotify: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        await processing_msg.edit_text(
            f"❌ Có lỗi xảy ra trong quá trình xử lý: {str(e)}\n\n"
            f"Đã hoàn lại {VERIFY_COST} điểm"
        )


async def verify4_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /verify4 - Bolt.new Teacher (Phiên bản tự động lấy mã)"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("Bạn đã bị chặn, không thể sử dụng tính năng này.")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("Vui lòng sử dụng /start để đăng ký trước.")
        return

    if not context.args:
        await update.message.reply_text(
            get_verify_usage_message("/verify4", "Bolt.new Teacher")
        )
        return

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(
            get_insufficient_balance_message(user["balance"])
        )
        return

    # Phân tích externalUserId hoặc verificationId
    external_user_id = BoltnewVerifier.parse_external_user_id(url)
    verification_id = BoltnewVerifier.parse_verification_id(url)

    if not external_user_id and not verification_id:
        await update.message.reply_text("Liên kết SheerID không hợp lệ, vui lòng kiểm tra lại.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Trừ điểm thất bại, vui lòng thử lại sau.")
        return

    processing_msg = await update.message.reply_text(
        f"🚀 Đang bắt đầu xử lý xác thực Bolt.new Teacher...\n"
        f"Đã trừ {VERIFY_COST} điểm\n\n"
        "📤 Đang gửi tài liệu..."
    )

    # Sử dụng semaphore để kiểm soát đồng thời
    semaphore = get_verification_semaphore("bolt_teacher")

    try:
        async with semaphore:
            # Bước 1: Gửi tài liệu
            verifier = BoltnewVerifier(url, verification_id=verification_id)
            result = await asyncio.to_thread(verifier.verify)

        if not result.get("success"):
            # Gửi thất bại, hoàn tiền
            db.add_balance(user_id, VERIFY_COST)
            await processing_msg.edit_text(
                f"❌ Gửi tài liệu thất bại: {result.get('message', 'Lỗi không xác định')}\n\n"
                f"Đã hoàn lại {VERIFY_COST} điểm"
            )
            return
        
        vid = result.get("verification_id", "")
        if not vid:
            db.add_balance(user_id, VERIFY_COST)
            await processing_msg.edit_text(
                f"❌ Không lấy được ID xác thực\n\n"
                f"Đã hoàn lại {VERIFY_COST} điểm"
            )
            return
        
        # Cập nhật tin nhắn
        await processing_msg.edit_text(
            f"✅ Tài liệu đã được gửi!\n"
            f"📋 ID xác thực: `{vid}`\n\n"
            f"🔍 Đang tự động lấy mã xác thực...\n"
            f"(Chờ tối đa 20 giây)"
        )
        
        # Bước 2: Tự động lấy mã xác thực (tối đa 20 giây)
        code = await _auto_get_reward_code(vid, max_wait=20, interval=5)
        
        if code:
            # Lấy thành công
            result_msg = (
                f"🎉 Xác thực thành công!\n\n"
                f"✅ Tài liệu đã gửi\n"
                f"✅ Đã qua kiểm duyệt\n"
                f"✅ Đã lấy được mã\n\n"
                f"🎁 Mã xác thực: `{code}`\n"
            )
            if result.get("redirect_url"):
                result_msg += f"\n🔗 Liên kết chuyển hướng:\n{result['redirect_url']}"
            
            await processing_msg.edit_text(result_msg)
            
            # Lưu bản ghi thành công
            db.add_verification(
                user_id,
                "bolt_teacher",
                url,
                "success",
                f"Code: {code}",
                vid
            )
        else:
            # Không lấy được trong 20s, bảo người dùng tra cứu sau
            await processing_msg.edit_text(
                f"✅ Tài liệu gửi thành công!\n\n"
                f"⏳ Mã chưa được tạo (có thể cần 1-5 phút duyệt)\n\n"
                f"📋 ID xác thực: `{vid}`\n\n"
                f"💡 Vui lòng dùng lệnh sau để tra cứu:\n"
                f"`/getV4Code {vid}`\n\n"
                f"Lưu ý: Điểm đã trừ, tra cứu lại không mất phí"
            )
            
            # Lưu bản ghi chờ xử lý
            db.add_verification(
                user_id,
                "bolt_teacher",
                url,
                "pending",
                "Waiting for review",
                vid
            )
            
    except Exception as e:
        logger.error("Lỗi quá trình xác thực Bolt.new: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        await processing_msg.edit_text(
            f"❌ Có lỗi xảy ra trong quá trình xử lý: {str(e)}\n\n"
            f"Đã hoàn lại {VERIFY_COST} điểm"
        )


async def _auto_get_reward_code(
    verification_id: str,
    max_wait: int = 20,
    interval: int = 5
) -> Optional[str]:
    """Tự động lấy mã thưởng (polling nhẹ, không ảnh hưởng đồng thời)
    
    Args:
        verification_id: ID xác thực
        max_wait: Thời gian chờ tối đa (giây)
        interval: Khoảng thời gian polling (giây)
        
    Returns:
        str: Mã thưởng, trả về None nếu thất bại
    """
    import time
    start_time = time.time()
    attempts = 0
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            elapsed = int(time.time() - start_time)
            attempts += 1
            
            # Kiểm tra xem đã hết giờ chưa
            if elapsed >= max_wait:
                logger.info(f"Tự động lấy code hết giờ ({elapsed}s), để người dùng tra cứu thủ công")
                return None
            
            try:
                # Truy vấn trạng thái xác thực
                response = await client.get(
                    f"https://my.sheerid.com/rest/v2/verification/{verification_id}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    current_step = data.get("currentStep")
                    
                    if current_step == "success":
                        # Lấy mã thưởng
                        code = data.get("rewardCode") or data.get("rewardData", {}).get("rewardCode")
                        if code:
                            logger.info(f"✅ Tự động lấy code thành công: {code} (mất {elapsed}s)")
                            return code
                    elif current_step == "error":
                        # Duyệt thất bại
                        logger.warning(f"Duyệt thất bại: {data.get('errorIds', [])}")
                        return None
                    # else: pending, tiếp tục chờ
                
                # Chờ lần polling tiếp theo
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.warning(f"Lỗi khi tra cứu mã: {e}")
                await asyncio.sleep(interval)
    
    return None


async def verify5_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /verify5 - YouTube Student Premium"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("Bạn đã bị chặn, không thể sử dụng tính năng này.")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("Vui lòng sử dụng /start để đăng ký trước.")
        return

    if not context.args:
        await update.message.reply_text(
            get_verify_usage_message("/verify5", "YouTube Student Premium")
        )
        return

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(
            get_insufficient_balance_message(user["balance"])
        )
        return

    # Phân tích verificationId
    verification_id = YouTubeVerifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("Liên kết SheerID không hợp lệ, vui lòng kiểm tra lại.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Trừ điểm thất bại, vui lòng thử lại sau.")
        return

    processing_msg = await update.message.reply_text(
        f"📺 Đang bắt đầu xử lý xác thực YouTube Student Premium...\n"
        f"Đã trừ {VERIFY_COST} điểm\n\n"
        "📝 Đang tạo thông tin sinh viên...\n"
        "🎨 Đang tạo ảnh thẻ sinh viên PNG...\n"
        "📤 Đang gửi tài liệu..."
    )

    # Sử dụng semaphore để kiểm soát đồng thời
    semaphore = get_verification_semaphore("youtube_student")

    try:
        async with semaphore:
            verifier = YouTubeVerifier(verification_id)
            result = await asyncio.to_thread(verifier.verify)

        db.add_verification(
            user_id,
            "youtube_student",
            url,
            "success" if result["success"] else "failed",
            str(result),
        )

        if result["success"]:
            result_msg = "✅ Xác thực YouTube Student Premium thành công!\n\n"
            if result.get("pending"):
                result_msg += "✨ Tài liệu đã được gửi, đang chờ SheerID duyệt\n"
                result_msg += "⏱️ Thời gian duyệt dự kiến: trong vài phút\n\n"
            if result.get("redirect_url"):
                result_msg += f"🔗 Liên kết chuyển hướng:\n{result['redirect_url']}"
            await processing_msg.edit_text(result_msg)
        else:
            db.add_balance(user_id, VERIFY_COST)
            await processing_msg.edit_text(
                f"❌ Xác thực thất bại: {result.get('message', 'Lỗi không xác định')}\n\n"
                f"Đã hoàn lại {VERIFY_COST} điểm"
            )
    except Exception as e:
        logger.error("Lỗi quá trình xác thực YouTube: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        await processing_msg.edit_text(
            f"❌ Có lỗi xảy ra trong quá trình xử lý: {str(e)}\n\n"
            f"Đã hoàn lại {VERIFY_COST} điểm"
        )


async def getV4Code_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Xử lý lệnh /getV4Code - Lấy mã xác thực Bolt.new Teacher"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("Bạn đã bị chặn, không thể sử dụng tính năng này.")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("Vui lòng sử dụng /start để đăng ký trước.")
        return

    # Kiểm tra xem có cung cấp verification_id không
    if not context.args:
        await update.message.reply_text(
            "Cách sử dụng: /getV4Code <verification_id>\n\n"
            "Ví dụ: /getV4Code 6929436b50d7dc18638890d0\n\n"
            "verification_id sẽ được trả về sau khi sử dụng lệnh /verify4."
        )
        return

    verification_id = context.args[0].strip()

    processing_msg = await update.message.reply_text(
        "🔍 Đang tra cứu mã xác thực, vui lòng đợi..."
    )

    try:
        # Truy vấn API SheerID để lấy mã
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://my.sheerid.com/rest/v2/verification/{verification_id}"
            )

            if response.status_code != 200:
                await processing_msg.edit_text(
                    f"❌ Tra cứu thất bại, mã trạng thái: {response.status_code}\n\n"
                    "Vui lòng thử lại sau hoặc liên hệ quản trị viên."
                )
                return

            data = response.json()
            current_step = data.get("currentStep")
            reward_code = data.get("rewardCode") or data.get("rewardData", {}).get("rewardCode")
            redirect_url = data.get("redirectUrl")

            if current_step == "success" and reward_code:
                result_msg = "✅ Xác thực thành công!\n\n"
                result_msg += f"🎉 Mã xác thực: `{reward_code}`\n\n"
                if redirect_url:
                    result_msg += f"Liên kết chuyển hướng:\n{redirect_url}"
                await processing_msg.edit_text(result_msg)
            elif current_step == "pending":
                await processing_msg.edit_text(
                    "⏳ Xác thực vẫn đang chờ duyệt, vui lòng thử lại sau.\n\n"
                    "Thường mất 1-5 phút, xin hãy kiên nhẫn."
                )
            elif current_step == "error":
                error_ids = data.get("errorIds", [])
                await processing_msg.edit_text(
                    f"❌ Xác thực thất bại\n\n"
                    f"Thông tin lỗi: {', '.join(error_ids) if error_ids else 'Lỗi không xác định'}"
                )
            else:
                await processing_msg.edit_text(
                    f"⚠️ Trạng thái hiện tại: {current_step}\n\n"
                    "Mã xác thực chưa được tạo, vui lòng thử lại sau."
                )

    except Exception as e:
        logger.error("Lỗi khi lấy mã Bolt.new: %s", e)
        await processing_msg.edit_text(
            f"❌ Có lỗi xảy ra trong quá trình tra cứu: {str(e)}\n\n"
            "Vui lòng thử lại sau hoặc liên hệ quản trị viên."
        )
