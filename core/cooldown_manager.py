"""
冷却管理器
处理用户请求的冷却控制和限流
"""

import asyncio
import time
from typing import Optional
from collections import defaultdict
from astrbot.api import logger


class CooldownManager:
    """用户冷却和限流管理器"""
    
    def __init__(
        self,
        cooldown_seconds: int = 30,
        cleanup_interval: int = 3600,
        enable_cooldown: bool = True,
        enable_rate_limit: bool = True,
        rate_limit_count: int = 10,
        rate_limit_window: int = 3600,
    ):
        self._cooldown_seconds = cooldown_seconds
        self._cleanup_interval = cleanup_interval
        self._enable_cooldown = enable_cooldown
        self._enable_rate_limit = enable_rate_limit
        self._rate_limit_count = rate_limit_count
        self._rate_limit_window = rate_limit_window
        
        # 用户最后请求时间: {user_id: timestamp}
        self._user_cooldown: dict[str, float] = {}
        
        # 用户请求计数: {user_id: [(timestamp, count)]}
        self._user_requests: dict[str, list[float]] = defaultdict(list)
        
        # 锁
        self._lock = asyncio.Lock()
        
        # 上次清理时间
        self._last_cleanup = time.time()
    
    def update_settings(
        self,
        cooldown_seconds: Optional[int] = None,
        cleanup_interval: Optional[int] = None,
        enable_cooldown: Optional[bool] = None,
        enable_rate_limit: Optional[bool] = None,
        rate_limit_count: Optional[int] = None,
        rate_limit_window: Optional[int] = None,
    ):
        """更新设置"""
        if cooldown_seconds is not None:
            self._cooldown_seconds = cooldown_seconds
        if cleanup_interval is not None:
            self._cleanup_interval = cleanup_interval
        if enable_cooldown is not None:
            self._enable_cooldown = enable_cooldown
        if enable_rate_limit is not None:
            self._enable_rate_limit = enable_rate_limit
        if rate_limit_count is not None:
            self._rate_limit_count = rate_limit_count
        if rate_limit_window is not None:
            self._rate_limit_window = rate_limit_window
    
    async def _cleanup_expired(self):
        """清理过期记录"""
        current_time = time.time()
        
        # 检查是否需要清理
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        async with self._lock:
            # 清理冷却记录（超过2倍冷却时间的视为过期）
            expired_threshold = self._cooldown_seconds * 2
            expired_users = [
                uid for uid, ts in self._user_cooldown.items()
                if current_time - ts > expired_threshold
            ]
            for uid in expired_users:
                del self._user_cooldown[uid]
            
            # 清理请求记录（超过限流窗口的视为过期）
            expired_requests = []
            for user_id, requests in self._user_requests.items():
                valid_requests = [
                    ts for ts in requests
                    if current_time - ts <= self._rate_limit_window
                ]
                if valid_requests:
                    self._user_requests[user_id] = valid_requests
                else:
                    expired_requests.append(user_id)
            
            for user_id in expired_requests:
                del self._user_requests[user_id]
            
            if expired_users or expired_requests:
                logger.debug(
                    f"清理了 {len(expired_users)} 条冷却记录, "
                    f"{len(expired_requests)} 条限流记录"
                )
            
            self._last_cleanup = current_time
    
    async def check_cooldown(self, user_id: str) -> tuple[bool, int]:
        """
        检查用户是否处于冷却状态
        
        Returns:
            (是否可用, 剩余秒数)
        """
        if not self._enable_cooldown:
            return True, 0
        
        await self._cleanup_expired()
        
        async with self._lock:
            last_request = self._user_cooldown.get(user_id, 0)
            elapsed = time.time() - last_request
            
            if elapsed < self._cooldown_seconds:
                remaining = int(self._cooldown_seconds - elapsed)
                return False, remaining
        
        return True, 0
    
    async def check_rate_limit(self, user_id: str) -> tuple[bool, int, int]:
        """
        检查用户是否触发限流
        
        Returns:
            (是否可用, 当前请求数, 剩余次数)
        """
        if not self._enable_rate_limit:
            return True, 0, self._rate_limit_count
        
        await self._cleanup_expired()
        
        async with self._lock:
            current_time = time.time()
            requests = self._user_requests[user_id]
            
            # 统计当前窗口内的请求数
            window_requests = [
                ts for ts in requests
                if current_time - ts <= self._rate_limit_window
            ]
            
            current_count = len(window_requests)
            remaining = max(0, self._rate_limit_count - current_count)
            
            if current_count >= self._rate_limit_count:
                # 计算下次可用时间
                oldest_request = min(window_requests)
                wait_time = int(self._rate_limit_window - (current_time - oldest_request))
                return False, current_count, wait_time
            
            return True, current_count, remaining
    
    async def record_request(self, user_id: str):
        """记录用户请求"""
        current_time = time.time()
        
        async with self._lock:
            # 更新冷却时间
            self._user_cooldown[user_id] = current_time
            
            # 记录请求
            self._user_requests[user_id].append(current_time)
    
    async def get_user_stats(self, user_id: str) -> dict:
        """获取用户统计信息"""
        async with self._lock:
            cooldown_remaining = 0
            if user_id in self._user_cooldown:
                elapsed = time.time() - self._user_cooldown[user_id]
                if elapsed < self._cooldown_seconds:
                    cooldown_remaining = int(self._cooldown_seconds - elapsed)
            
            requests = self._user_requests.get(user_id, [])
            current_time = time.time()
            window_requests = [
                ts for ts in requests
                if current_time - ts <= self._rate_limit_window
            ]
            
            return {
                "cooldown_remaining": cooldown_remaining,
                "requests_in_window": len(window_requests),
                "rate_limit_remaining": max(0, self._rate_limit_count - len(window_requests)),
                "total_requests": len(requests),
                "is_cooldown_active": cooldown_remaining > 0,
            }
    
    def get_global_stats(self) -> dict:
        """获取全局统计信息"""
        return {
            "active_cooldowns": len(self._user_cooldown),
            "tracked_users": len(self._user_requests),
            "cooldown_seconds": self._cooldown_seconds,
            "rate_limit_count": self._rate_limit_count,
            "rate_limit_window": self._rate_limit_window,
        }
