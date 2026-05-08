"""
输入验证器
"""

from typing import Optional
from .exceptions import ValidationError


class InputValidator:
    """输入验证器"""
    
    @staticmethod
    def validate_article_input(
        game_name: str,
        event_desc: str,
        style: str = "",
        custom_style: str = "",
        max_game_name_length: int = 50,
        max_event_length: int = 500,
        max_custom_style_length: int = 200,
    ) -> tuple[bool, str]:
        """
        验证文章生成输入
        
        Returns:
            (是否有效, 错误信息)
        """
        if not game_name or not game_name.strip():
            return False, "游戏名不能为空"
        
        if len(game_name) > max_game_name_length:
            return False, f"游戏名太长啦，请控制在{max_game_name_length}字以内"
        
        if not event_desc or not event_desc.strip():
            return False, "事件描述不能为空"
        
        if len(event_desc) < 2:
            return False, "事件描述至少需要2个字"
        
        if len(event_desc) > max_event_length:
            return False, f"事件描述太长啦，请控制在{max_event_length}字以内"
        
        if custom_style and len(custom_style) > max_custom_style_length:
            return False, f"自定义风格描述太长啦，请控制在{max_custom_style_length}字以内"
        
        return True, ""
    
    @staticmethod
    def sanitize_command_args(args: list[str]) -> list[str]:
        """清理命令参数"""
        return [arg.strip() for arg in args if arg.strip()]
