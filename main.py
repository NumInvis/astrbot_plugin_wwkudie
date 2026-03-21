"""
尽孝插件 - 热爱游戏，把游戏公司当父亲尽孝的人
"""

from astrbot.api import logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from ._version import __version__, __plugin_name__, __plugin_desc__, __author__
from .prompts import SYSTEM_PROMPT, build_article_prompt


@register(__plugin_name__, __author__, __plugin_desc__, __version__)
class WwkudiePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        logger.info(f"尽孝插件已初始化")

    @filter.command("尽孝")
    async def wwkudie_command(self, event: AstrMessageEvent, message: str = ""):
        if not message:
            yield event.plain_result("请提供游戏名和事件描述！\n使用方式：/尽孝 游戏名 事件描述")
            return

        try:
            yield event.plain_result("🖊️ 正在写文章...")
            
            umo = event.unified_msg_origin
            provider_id = await self.context.get_current_chat_provider_id(umo=umo)
            
            if not provider_id:
                yield event.plain_result("错误：未找到 LLM 提供商")
                return

            full_prompt = f"{SYSTEM_PROMPT}\n\n{build_article_prompt(message)}"
            
            llm_resp = await self.context.llm_generate(
                chat_provider_id=provider_id,
                prompt=full_prompt,
            )

            if llm_resp and hasattr(llm_resp, 'completion_text') and llm_resp.completion_text:
                yield event.plain_result(llm_resp.completion_text)
            else:
                yield event.plain_result("生成失败")
        except Exception as e:
            logger.error(f"错误: {str(e)}", exc_info=True)
            yield event.plain_result(f"错误：{str(e)}")

    @filter.command("尽孝帮助")
    async def wwkudie_help(self, event: AstrMessageEvent):
        yield event.plain_result("使用方式：/尽孝 游戏名 事件描述")
