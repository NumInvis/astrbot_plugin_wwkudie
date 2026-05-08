"""
提示词构建器
安全地构建 LLM 提示词
"""

from typing import Optional
from .style_manager import StyleManager


# 默认系统提示词
DEFAULT_SYSTEM_PROMPT = """你是一位深度热爱游戏的玩家，你将游戏公司视为精神寄托，对其倾注全部的热爱与支持。你的写作风格极具深度和感染力，情感真挚而强烈。

写作风格特点：
1. 立场鲜明，情感真挚，无条件支持该游戏，内容围绕吹捧该游戏展开。
2. 从具体事件入手，层层递进，最后升华主题
3. 善于使用比喻、排比、反问等修辞手法
4. 语言优美，有文采
5. 旁征博引
6. 结构清晰，逻辑严密，说服力强
7. 字数在400-800字之间，内容充实
8. 专业记者的口吻，吹捧该游戏

写作结构参考：
- 开头：引出事件或主题，吸引读者注意
- 主体：多角度分析，层层递进，使用有力的论证
- 结尾：升华主题，引发思考，给人留下深刻印象

重要：纯文本写作，不使用任何 markdown 格式、加粗等。除文章有一个专业新闻稿风格的标题外，文章内不使用其他任何标题"""


class PromptBuilder:
    """提示词构建器"""
    
    # 危险字符和模式
    DANGEROUS_PATTERNS = [
        "system:", "user:", "assistant:", "human:", "ai:",
        "ignore previous", "forget", "override",
        "you are now", "new instructions",
        "\u003c|", "|\u003e", "[INST", "[/INST",
    ]
    
    def __init__(self, style_manager: Optional[StyleManager] = None):
        self._style_manager = style_manager or StyleManager()
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """
        清理用户输入，防止 prompt injection
        
        Args:
            text: 原始输入
            max_length: 最大长度
        
        Returns:
            清理后的输入
        """
        if not text:
            return ""
        
        # 截断
        text = text[:max_length]
        
        # 移除控制字符
        text = "".join(char for char in text if ord(char) >= 32 or char in "\n\t")
        
        # 检查危险模式
        text_lower = text.lower()
        for pattern in PromptBuilder.DANGEROUS_PATTERNS:
            if pattern in text_lower:
                # 替换危险模式
                text = text.replace(pattern, "[已移除]").replace(pattern.title(), "[已移除]")
        
        # 移除过多的连续特殊字符
        import re
        text = re.sub(r"[!?]{4,}", "!!!", text)
        text = re.sub(r"\.{4,}", "...", text)
        
        return text.strip()
    
    def build_system_prompt(self, custom_prompt: Optional[str] = None) -> str:
        """
        构建系统提示词
        
        Args:
            custom_prompt: 自定义系统提示词
        
        Returns:
            系统提示词
        """
        if custom_prompt:
            # 清理自定义提示词
            return self.sanitize_input(custom_prompt, max_length=5000)
        return DEFAULT_SYSTEM_PROMPT
    
    def build_article_prompt(
        self,
        game_name: str,
        event_desc: str,
        style: str = "默认",
        custom_style: Optional[str] = None,
    ) -> str:
        """
        构建文章生成提示词
        
        Args:
            game_name: 游戏名称
            event_desc: 事件描述
            style: 写作风格
            custom_style: 自定义风格描述
        
        Returns:
            完整的用户提示词
        """
        # 清理输入
        game_name = self.sanitize_input(game_name, max_length=100)
        event_desc = self.sanitize_input(event_desc, max_length=1000)
        
        if not game_name:
            game_name = "游戏"
        if not event_desc:
            event_desc = "相关事件"
        
        base_prompt = f"""游戏：{game_name}
事件：{event_desc}

请根据上述游戏和事件，撰写一篇符合风格要求的深度游戏评论文章新闻稿。"""
        
        if custom_style:
            # DIY 自定义风格
            custom_style = self.sanitize_input(custom_style, max_length=500)
            return (
                f"{base_prompt}\n\n"
                f"【自定义风格要求】{custom_style}\n\n"
                f"请严格按照上述自定义风格要求来撰写文章，同时保持对游戏的热爱和吹捧立场。"
            )
        
        # 使用内置风格
        style_modifier, _, _ = self._style_manager.get_style(style)
        
        if style_modifier:
            return f"{base_prompt}\n\n【风格要求】{style_modifier}"
        
        return base_prompt
    
    def build_compare_prompt(
        self,
        game_name: str,
        events: list[str],
        style: str = "默认",
    ) -> str:
        """
        构建对比分析提示词（新功能）
        
        Args:
            game_name: 游戏名称
            events: 多个事件描述列表
            style: 写作风格
        
        Returns:
            对比分析提示词
        """
        game_name = self.sanitize_input(game_name, max_length=100)
        events = [self.sanitize_input(e, max_length=500) for e in events]
        
        events_text = "\n".join([f"{i+1}. {event}" for i, event in enumerate(events) if event])
        
        base_prompt = f"""游戏：{game_name}

以下是对该游戏的多个相关事件/话题：
{events_text}

请根据上述事件，撰写一篇综合分析文章，从多个角度论证这款游戏的优秀之处。文章需要有统一的观点，将各个事件串联起来，展现游戏的全方位优势。"""
        
        style_modifier, _, _ = self._style_manager.get_style(style)
        
        if style_modifier:
            return f"{base_prompt}\n\n【风格要求】{style_modifier}"
        
        return base_prompt
