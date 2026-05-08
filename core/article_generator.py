"""
文章生成器
处理 LLM 调用和响应解析
"""

import asyncio
from typing import Any, Optional
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.api.star import Context

from .config_manager import ConfigManager
from .prompt_builder import PromptBuilder
from .style_manager import StyleManager


class LLMResponseParser:
    """LLM 响应解析器"""
    
    @staticmethod
    def parse(response: Any) -> Optional[str]:
        """
        解析 LLM 响应，提取文本内容
        
        Args:
            response: LLM 响应对象
        
        Returns:
            解析后的文本，失败返回 None
        """
        if response is None:
            return None
        
        # 处理对象属性
        if hasattr(response, 'completion_text') and response.completion_text:
            return response.completion_text
        if hasattr(response, 'text') and response.text:
            return response.text
        if hasattr(response, 'content') and response.content:
            return response.content
        if hasattr(response, 'message') and response.message:
            return response.message
        
        # 处理字典格式
        if isinstance(response, dict):
            for key in ['completion_text', 'text', 'content', 'message', 'response']:
                if key in response and response[key]:
                    return str(response[key])
            return str(response) if response else None
        
        # 处理字符串
        if isinstance(response, str):
            return response if response.strip() else None
        
        # 其他类型，尝试字符串化
        try:
            text = str(response)
            return text if text and text not in ['None', 'null', ''] else None
        except Exception:
            return None


class ArticleGenerator:
    """文章生成器"""
    
    def __init__(
        self,
        context: Context,
        config_manager: ConfigManager,
        prompt_builder: PromptBuilder,
    ):
        self._context = context
        self._config = config_manager
        self._prompt_builder = prompt_builder
        self._parser = LLMResponseParser()
    
    async def generate(
        self,
        event: AstrMessageEvent,
        game_name: str,
        event_desc: str,
        style: str = "默认",
        custom_style: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        生成文章
        
        Args:
            event: 消息事件
            game_name: 游戏名称
            event_desc: 事件描述
            style: 写作风格
            custom_style: 自定义风格
        
        Returns:
            (是否成功, 结果文本)
        """
        try:
            # 获取系统提示词
            system_prompt = self._prompt_builder.build_system_prompt(
                self._config.get("system_prompt")
            )
            
            # 构建用户提示词
            user_prompt = self._prompt_builder.build_article_prompt(
                game_name=game_name,
                event_desc=event_desc,
                style=style,
                custom_style=custom_style,
            )
            
            # 合并提示词
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # 获取 LLM 提供商
            umo = event.unified_msg_origin
            provider_id = await self._context.get_current_chat_provider_id(umo=umo)
            
            if not provider_id:
                return False, "❌ 错误：未找到 LLM 提供商，请先配置AI模型"
            
            # 调用 LLM
            llm_resp = await self._context.llm_generate(
                chat_provider_id=provider_id,
                prompt=full_prompt,
            )
            
            # 解析响应
            response_text = self._parser.parse(llm_resp)
            
            if response_text:
                # 检查文章长度
                max_length = self._config.get("max_article_length", 2000)
                if len(response_text) > max_length:
                    logger.warning(f"生成的文章过长 ({len(response_text)} 字)，已截断")
                    response_text = response_text[:max_length] + "\n\n[文章已截断]"
                
                return True, response_text
            else:
                if llm_resp is None:
                    logger.error("LLM 响应为 None")
                    return False, "❌ 生成失败：AI没有返回响应"
                else:
                    logger.error(f"无法解析 LLM 响应: {type(llm_resp)}, {llm_resp}")
                    return False, "❌ 生成失败：无法解析AI响应"
        
        except asyncio.TimeoutError:
            logger.error("LLM 生成超时")
            return False, "⏰ 生成超时，请稍后再试"
        
        except Exception as e:
            logger.error(f"文章生成错误: {str(e)}", exc_info=True)
            return False, self._format_error_message(e)
    
    @staticmethod
    def _format_error_message(error: Exception) -> str:
        """格式化错误信息"""
        error_message = str(error).lower()
        
        if "rate" in error_message or "limit" in error_message:
            return "🚫 API调用频率限制，请稍后再试"
        elif "connect" in error_message or "network" in error_message or "url" in error_message:
            return "🔌 网络连接失败，请检查网络配置"
        elif "timeout" in error_message:
            return "⏰ 生成超时，请稍后再试"
        elif "auth" in error_message or "key" in error_message or "token" in error_message:
            return "🔑 API认证失败，请检查API密钥配置"
        elif "quota" in error_message or "billing" in error_message:
            return "💳 API额度不足，请检查账户余额"
        elif "content" in error_message or "policy" in error_message or "safety" in error_message:
            return "🛡️ 内容被安全策略拦截，请尝试更换描述"
        else:
            return "❌ 生成失败，请稍后重试"
