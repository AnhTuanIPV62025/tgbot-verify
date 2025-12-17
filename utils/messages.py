"""Mẫu tin nhắn"""
from config import CHANNEL_URL, VERIFY_COST, HELP_NOTION_URL


def get_welcome_message(full_name: str, invited_by: bool = False) -> str:
    """Lấy tin nhắn chào mừng"""
    msg = (
        f"🎉 Chào mừng, {full_name}!\n"
        "Bạn đã đăng ký thành công và nhận được 1 điểm.\n"
    )
    if invited_by:
        msg += "Cảm ơn bạn đã tham gia qua liên kết mời, người mời đã nhận được 2 điểm.\n"

    msg += (
        "\nBot này có thể tự động hoàn tất xác thực SheerID.\n"
        "Bắt đầu nhanh:\n"
        "/about - Tìm hiểu chức năng của bot\n"
        "/balance - Kiểm tra số dư điểm\n"
        "/help - Xem danh sách lệnh đầy đủ\n\n"
        "Nhận thêm điểm:\n"
        "/qd - Điểm danh hàng ngày\n"
        "/invite - Mời bạn bè\n"
        f"Tham gia kênh: {CHANNEL_URL}"
    )
    return msg


def get_about_message() -> str:
    """Lấy tin nhắn giới thiệu"""
    return (
        "🤖 Bot xác thực tự động SheerID\n"
        "\n"
        "Giới thiệu chức năng:\n"
        "- Tự động hoàn tất xác thực Sinh viên/Giáo viên SheerID\n"
        "- Hỗ trợ xác thực Gemini One Pro, ChatGPT Teacher K12, Spotify Student, YouTube Student, Bolt.new Teacher\n"
        "\n"
        "Cách nhận điểm:\n"
        "- Đăng ký tặng 1 điểm\n"
        "- Điểm danh hàng ngày +1 điểm\n"
        "- Mời bạn bè +2 điểm/người\n"
        "- Sử dụng mã thẻ (theo quy tắc mã thẻ)\n"
        f"- Tham gia kênh: {CHANNEL_URL}\n"
        "\n"
        "Hướng dẫn sử dụng:\n"
        "1. Bắt đầu xác thực trên trang web và sao chép liên kết xác thực đầy đủ\n"
        "2. Gửi lệnh /verify, /verify2, /verify3, /verify4 hoặc /verify5 kèm theo liên kết đó\n"
        "3. Chờ xử lý và xem kết quả\n"
        "4. Xác thực Bolt.new sẽ tự động lấy mã xác thực, nếu cần tra cứu thủ công hãy dùng /getV4Code <verification_id>\n"
        "\n"
        "Để biết thêm lệnh vui lòng gửi /help"
    )


def get_help_message(is_admin: bool = False) -> str:
    """Lấy tin nhắn trợ giúp"""
    msg = (
        "📖 Bot xác thực tự động SheerID - Trợ giúp\n"
        "\n"
        "Lệnh người dùng:\n"
        "/start - Bắt đầu sử dụng (Đăng ký)\n"
        "/about - Tìm hiểu chức năng của bot\n"
        "/balance - Kiểm tra số dư điểm\n"
        "/qd - Điểm danh hàng ngày (+1 điểm)\n"
        "/invite - Tạo liên kết mời (+2 điểm/người)\n"
        "/use <mã_thẻ> - Sử dụng mã thẻ để đổi điểm\n"
        f"/verify <liên_kết> - Xác thực Gemini One Pro (-{VERIFY_COST} điểm)\n"
        f"/verify2 <liên_kết> - Xác thực ChatGPT Teacher K12 (-{VERIFY_COST} điểm)\n"
        f"/verify3 <liên_kết> - Xác thực Spotify Student (-{VERIFY_COST} điểm)\n"
        f"/verify4 <liên_kết> - Xác thực Bolt.new Teacher (-{VERIFY_COST} điểm)\n"
        f"/verify5 <liên_kết> - Xác thực YouTube Student Premium (-{VERIFY_COST} điểm)\n"
        "/getV4Code <verification_id> - Lấy mã xác thực Bolt.new\n"
        "/help - Xem thông tin trợ giúp này\n"
        f"Xem lỗi xác thực tại: {HELP_NOTION_URL}\n"
    )

    if is_admin:
        msg += (
            "\nLệnh quản trị viên:\n"
            "/addbalance <ID_người_dùng> <điểm> - Cộng điểm cho người dùng\n"
            "/block <ID_người_dùng> - Chặn người dùng\n"
            "/white <ID_người_dùng> - Bỏ chặn người dùng\n"
            "/blacklist - Xem danh sách đen\n"
            "/genkey <mã_thẻ> <điểm> [số_lần] [số_ngày] - Tạo mã thẻ\n"
            "/listkeys - Xem danh sách mã thẻ\n"
            "/broadcast <văn_bản> - Gửi thông báo đến tất cả người dùng\n"
        )

    return msg


def get_insufficient_balance_message(current_balance: int) -> str:
    """Lấy tin nhắn không đủ điểm"""
    return (
        f"Không đủ điểm! Cần {VERIFY_COST} điểm, hiện có {current_balance} điểm.\n\n"
        "Cách nhận điểm:\n"
        "- Điểm danh hàng ngày /qd\n"
        "- Mời bạn bè /invite\n"
        "- Sử dụng mã thẻ /use <mã_thẻ>"
    )


def get_verify_usage_message(command: str, service_name: str) -> str:
    """Lấy hướng dẫn sử dụng lệnh xác thực"""
    return (
        f"Cách sử dụng: {command} <Liên kết SheerID>\n\n"
        "Ví dụ:\n"
        f"{command} https://services.sheerid.com/verify/xxx/?verificationId=xxx\n\n"
        "Cách lấy liên kết xác thực:\n"
        f"1. Truy cập trang xác thực {service_name}\n"
        "2. Bắt đầu quy trình xác thực\n"
        "3. Sao chép URL đầy đủ trên thanh địa chỉ trình duyệt\n"
        f"4. Sử dụng lệnh {command} để gửi"
    )
