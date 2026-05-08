"""
输入验证器
"""


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
        
        if not event_desc or not event_desc.strip():
            return False, "事件描述不能为空"
        
        return True, ""
    
    @staticmethod
    def sanitize_command_args(args: list[str]) -> list[str]:
        """清理命令参数"""
        return [arg.strip() for arg in args if arg.strip()]
