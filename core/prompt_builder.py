"""
提示词构建器
构建 LLM 提示词
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
    
    def __init__(self, style_manager: Optional[StyleManager] = None):
        self._style_manager = style_manager or StyleManager()
    
    def build_system_prompt(self, custom_prompt: Optional[str] = None) -> str:
        """
        构建系统提示词
        
        Args:
            custom_prompt: 自定义系统提示词
        
        Returns:
            系统提示词
        """
        if custom_prompt:
            return custom_prompt
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
        if not game_name:
            game_name = "游戏"
        if not event_desc:
            event_desc = "相关事件"
        
        base_prompt = f"""游戏：{game_name}
事件：{event_desc}

请根据上述游戏和事件，撰写一篇符合风格要求的深度游戏评论文章新闻稿。"""
        
        if custom_style:
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
    

