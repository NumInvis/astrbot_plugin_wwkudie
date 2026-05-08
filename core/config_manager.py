"""
配置管理器
处理 AstrBot 配置系统的读取和缓存
"""

import json
from pathlib import Path
from typing import Any, Optional
from astrbot.api import logger


class ConfigManager:
    """AstrBot 配置管理器"""
    
    # 默认配置
    DEFAULTS = {
        "cooldown_seconds": 30,
        "max_game_name_length": 50,
        "max_event_length": 500,
        "max_custom_style_length": 200,
        "cleanup_interval": 3600,
        "enable_cooldown": True,
        "default_style": "默认",
        "system_prompt": None,
        "enable_history": True,
        "max_history_per_user": 10,
        "enable_stats": True,
        "max_article_length": 2000,
        "enable_rate_limit": True,
        "rate_limit_count": 10,
        "rate_limit_window": 3600,
    }
    
    def __init__(self, context: Any):
        self._context = context
        self._cache: dict[str, Any] = {}
        self._cache_valid = False
        self._plugin_name = "astrbot_plugin_wwkudie"
    
    def _load_config(self) -> dict[str, Any]:
        """从 AstrBot 配置系统加载配置"""
        try:
            # 尝试多种方式获取配置
            config = {}
            
            # 方式1: 通过 context.config 获取（AstrBot v4.0+）
            if hasattr(self._context, 'config') and isinstance(self._context.config, dict):
                plugin_config = self._context.config.get(self._plugin_name, {})
                if plugin_config:
                    config.update(plugin_config)
            
            # 方式2: 通过 get_using_config 获取
            if hasattr(self._context, 'get_using_config'):
                try:
                    plugin_config = self._context.get_using_config(self._plugin_name)
                    if plugin_config and isinstance(plugin_config, dict):
                        config.update(plugin_config)
                except Exception:
                    pass
            
            # 方式3: 通过 get_config 获取（兼容性）
            if hasattr(self._context, 'get_config'):
                try:
                    global_config = self._context.get_config()
                    if isinstance(global_config, dict):
                        plugin_config = global_config.get(self._plugin_name, {})
                        if plugin_config:
                            config.update(plugin_config)
                except Exception:
                    pass
            
            return config
            
        except Exception as e:
            logger.warning(f"加载配置失败: {e}")
            return {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键名
            default: 默认值
        
        Returns:
            配置值
        """
        # 如果缓存有效，从缓存读取
        if self._cache_valid and key in self._cache:
            return self._cache[key]
        
        # 从 AstrBot 配置系统读取
        config = self._load_config()
        
        if key in config:
            value = config[key]
            self._cache[key] = value
            return value
        
        # 使用内置默认值
        return self.DEFAULTS.get(key, default)
    
    def get_all(self) -> dict[str, Any]:
        """获取所有配置"""
        config = self._load_config()
        result = dict(self.DEFAULTS)
        result.update(config)
        return result
    
    def invalidate_cache(self):
        """使配置缓存失效"""
        self._cache_valid = False
        self._cache.clear()
    
    def reload(self):
        """重新加载配置"""
        self.invalidate_cache()
        config = self._load_config()
        self._cache = dict(self.DEFAULTS)
        self._cache.update(config)
        self._cache_valid = True
        logger.info("配置已重新加载")
