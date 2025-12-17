"""Công cụ kiểm soát đồng thời (Phiên bản tối ưu hóa)

Cải tiến hiệu suất:
1. Giới hạn đồng thời động (dựa trên tải hệ thống)
2. Tách biệt kiểm soát đồng thời cho các loại xác minh khác nhau
3. Hỗ trợ số lượng đồng thời cao hơn
4. Giám sát tải và tự động điều chỉnh
"""
import asyncio
import logging
from typing import Dict
import psutil

logger = logging.getLogger(__name__)

# Tính toán động số lượng đồng thời tối đa
def _calculate_max_concurrency() -> int:
    """Tính toán số lượng đồng thời tối đa dựa trên tài nguyên hệ thống"""
    try:
        cpu_count = psutil.cpu_count() or 4
        memory_gb = psutil.virtual_memory().total / (1024 ** 3)
        
        # Tính toán dựa trên CPU và bộ nhớ
        # Mỗi lõi CPU hỗ trợ 3-5 tác vụ đồng thời
        # Mỗi GB bộ nhớ hỗ trợ 2 tác vụ đồng thời
        cpu_based = cpu_count * 4
        memory_based = int(memory_gb * 2)
        
        # Lấy giá trị nhỏ nhất của cả hai và đặt giới hạn trên/dưới
        max_concurrent = min(cpu_based, memory_based)
        max_concurrent = max(10, min(max_concurrent, 100))  # Giữa 10-100
        
        logger.info(
            f"系统资源: CPU={cpu_count}, Memory={memory_gb:.1f}GB, "
            f"计算并发数={max_concurrent}"
        )
        
        return max_concurrent
        
    except Exception as e:
        logger.warning(f"无法获取系统资源信息: {e}, 使用默认值")
        return 20  # Giá trị mặc định

# Tính toán giới hạn đồng thời cho từng loại xác minh
_base_concurrency = _calculate_max_concurrency()

# Tạo semaphore độc lập cho các loại xác minh khác nhau
# Điều này tránh việc một loại xác minh chặn các loại khác
_verification_semaphores: Dict[str, asyncio.Semaphore] = {
    "gemini_one_pro": asyncio.Semaphore(_base_concurrency // 5),
    "chatgpt_teacher_k12": asyncio.Semaphore(_base_concurrency // 5),
    "spotify_student": asyncio.Semaphore(_base_concurrency // 5),
    "youtube_student": asyncio.Semaphore(_base_concurrency // 5),
    "bolt_teacher": asyncio.Semaphore(_base_concurrency // 5),
}


def get_verification_semaphore(verification_type: str) -> asyncio.Semaphore:
    """Lấy semaphore cho loại xác minh được chỉ định
    
    Args:
        verification_type: Loại xác minh
        
    Returns:
        asyncio.Semaphore: Semaphore tương ứng
    """
    semaphore = _verification_semaphores.get(verification_type)
    
    if semaphore is None:
        # Loại không xác định, tạo semaphore mặc định
        semaphore = asyncio.Semaphore(_base_concurrency // 3)
        _verification_semaphores[verification_type] = semaphore
        logger.info(
            f"为新验证类型 {verification_type} 创建信号量: "
            f"limit={_base_concurrency // 3}"
        )
    
    return semaphore


def get_concurrency_stats() -> Dict[str, Dict[str, int]]:
    """Lấy thông tin thống kê đồng thời
    
    Returns:
        dict: Thông tin đồng thời cho từng loại xác minh
    """
    stats = {}
    for vtype, semaphore in _verification_semaphores.items():
        # Lưu ý: _value là thuộc tính nội bộ, có thể thay đổi trong các phiên bản Python khác nhau
        try:
            available = semaphore._value if hasattr(semaphore, '_value') else 0
            limit = _base_concurrency // 3
            in_use = limit - available
        except Exception:
            available = 0
            limit = _base_concurrency // 3
            in_use = 0
        
        stats[vtype] = {
            'limit': limit,
            'in_use': in_use,
            'available': available,
        }
    
    return stats


async def monitor_system_load() -> Dict[str, float]:
    """Giám sát tải hệ thống
    
    Returns:
        dict: Thông tin tải hệ thống
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'concurrency_limit': _base_concurrency,
        }
    except Exception as e:
        logger.error(f"监控系统负载失败: {e}")
        return {
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'concurrency_limit': _base_concurrency,
        }


def adjust_concurrency_limits(multiplier: float = 1.0):
    """Điều chỉnh giới hạn đồng thời động
    
    Args:
        multiplier: Hệ số điều chỉnh (0.5-2.0)
    """
    global _verification_semaphores, _base_concurrency
    
    # Giới hạn phạm vi hệ số
    multiplier = max(0.5, min(multiplier, 2.0))
    
    new_base = int(_base_concurrency * multiplier)
    new_limit = max(5, min(new_base // 3, 50))  # Mỗi loại 5-50
    
    logger.info(
        f"调整并发限制: multiplier={multiplier}, "
        f"new_base={new_base}, per_type={new_limit}"
    )
    
    # Tạo semaphore mới
    for vtype in _verification_semaphores.keys():
        _verification_semaphores[vtype] = asyncio.Semaphore(new_limit)


# Tác vụ giám sát tải
_monitor_task = None

async def start_load_monitoring(interval: float = 60.0):
    """Bắt đầu tác vụ giám sát tải
    
    Args:
        interval: Khoảng thời gian giám sát (giây)
    """
    global _monitor_task
    
    if _monitor_task is not None:
        return
    
    async def monitor_loop():
        while True:
            try:
                await asyncio.sleep(interval)
                
                load_info = await monitor_system_load()
                cpu = load_info['cpu_percent']
                memory = load_info['memory_percent']
                
                logger.info(
                    f"系统负载: CPU={cpu:.1f}%, Memory={memory:.1f}%"
                )
                
                # Tự động điều chỉnh giới hạn đồng thời
                if cpu > 80 or memory > 85:
                    # Tải quá cao, giảm đồng thời
                    adjust_concurrency_limits(0.7)
                    logger.warning("系统负载过高，降低并发限制")
                elif cpu < 40 and memory < 60:
                    # Tải thấp, có thể tăng đồng thời
                    adjust_concurrency_limits(1.2)
                    logger.info("系统负载较低，提高并发限制")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"负载监控异常: {e}")
    
    _monitor_task = asyncio.create_task(monitor_loop())
    logger.info(f"负载监控已启动: interval={interval}s")


async def stop_load_monitoring():
    """Dừng tác vụ giám sát tải"""
    global _monitor_task
    
    if _monitor_task is not None:
        _monitor_task.cancel()
        try:
            await _monitor_task
        except asyncio.CancelledError:
            pass
        _monitor_task = None
        logger.info("负载监控已停止")
