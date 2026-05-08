"""
历史记录管理器
管理用户的历史生成记录
"""

import json
import time
from pathlib import Path
from typing import Optional
from astrbot.api import logger


class HistoryManager:
    """历史记录管理器"""
    
    def __init__(self, data_dir: Path, max_history_per_user: int = 10):
        self._data_dir = data_dir
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._max_history = max_history_per_user
        self._history_file = self._data_dir / "history.json"
        self._history: dict[str, list[dict]] = {}
        self._load_history()
    
    def _load_history(self):
        """加载历史记录"""
        try:
            if self._history_file.exists():
                with open(self._history_file, 'r', encoding='utf-8') as f:
                    self._history = json.load(f)
            else:
                self._history = {}
        except Exception as e:
            logger.warning(f"加载历史记录失败: {e}")
            self._history = {}
    
    def _save_history(self):
        """保存历史记录"""
        try:
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存历史记录失败: {e}")
    
    def add_record(
        self,
        user_id: str,
        game_name: str,
        event_desc: str,
        style: str,
        article: str,
    ):
        """
        添加历史记录
        
        Args:
            user_id: 用户ID
            game_name: 游戏名称
            event_desc: 事件描述
            style: 风格
            article: 生成的文章
        """
        if user_id not in self._history:
            self._history[user_id] = []
        
        record = {
            "timestamp": time.time(),
            "game_name": game_name,
            "event_desc": event_desc,
            "style": style,
            "article": article,
        }
        
        self._history[user_id].insert(0, record)
        
        # 限制历史记录数量
        if len(self._history[user_id]) > self._max_history:
            self._history[user_id] = self._history[user_id][:self._max_history]
        
        self._save_history()
    
    def get_history(self, user_id: str, limit: Optional[int] = None) -> list[dict]:
        """
        获取用户历史记录
        
        Args:
            user_id: 用户ID
            limit: 限制数量
        
        Returns:
            历史记录列表
        """
        records = self._history.get(user_id, [])
        if limit:
            records = records[:limit]
        return records
    
    def get_last_record(self, user_id: str) -> Optional[dict]:
        """获取用户最后一条记录"""
        records = self._history.get(user_id, [])
        return records[0] if records else None
    
    def clear_history(self, user_id: str) -> bool:
        """清除用户历史记录"""
        if user_id in self._history:
            del self._history[user_id]
            self._save_history()
            return True
        return False
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        total_users = len(self._history)
        total_records = sum(len(records) for records in self._history.values())
        
        return {
            "total_users": total_users,
            "total_records": total_records,
            "max_history_per_user": self._max_history,
        }
