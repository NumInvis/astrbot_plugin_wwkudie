"""
尽孝插件 - 热爱游戏，把游戏公司当父亲尽孝的人
"""

import asyncio
import time
from typing import Optional, Any
from astrbot.api import logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from ._version import __version__, __plugin_name__, __plugin_desc__, __author__
from .prompts import build_article_prompt, build_article_prompt_with_custom_style, get_available_styles, get_style_modifier


class LLMResponseParser:
    """LLM响应解析器"""
    
    @staticmethod
    def parse(response: Any) -> Optional[str]:
        """
        解析LLM响应，提取文本内容
        
        Args:
            response: LLM响应对象
        
        Returns:
            解析后的文本，解析失败返回None
        """
        if response is None:
            return None
        
        # 处理对象属性
        if hasattr(response, 'completion_text') and response.completion_text:
            return response.completion_text
        elif hasattr(response, 'text') and response.text:
            return response.text
        elif hasattr(response, 'content') and response.content:
            return response.content
        
        # 处理字典格式
        elif isinstance(response, dict):
            return response.get('completion_text') or response.get('text') or response.get('content')
        
        # 处理字符串
        elif isinstance(response, str):
            return response
        
        return None


@register(__plugin_name__, __author__, __plugin_desc__, __version__)
class WwkudiePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        
        # 用户冷却时间字典: {user_id: last_request_time}
        self._user_cooldown: dict[str, float] = {}
        
        # 并发锁，保护冷却字典的读写
        self._cooldown_lock = asyncio.Lock()
        
        # 上次清理时间
        self._last_cleanup_time = time.time()
        
        logger.info("尽孝插件已初始化")
    
    def _get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置项，支持从AstrBot配置系统读取
        
        Args:
            key: 配置键名
            default: 默认值
        
        Returns:
            配置值
        """
        try:
            # 尝试从AstrBot配置读取
            if hasattr(self.context, 'get_config'):
                config = self.context.get_config()
                if config and key in config:
                    return config[key]
        except Exception as e:
            logger.debug(f"读取配置失败，使用默认值: {e}")
        
        # 默认配置值
        defaults = {
            "cooldown_seconds": 30,
            "max_game_name_length": 50,
            "max_event_length": 500,
            "max_custom_style_length": 200,
            "cleanup_interval": 3600,
            "enable_cooldown": True,
            "default_style": "默认",
            "system_prompt": None
        }
        
        return defaults.get(key, default)
    
    async def _cleanup_old_cooldown(self):
        """清理过期的冷却记录，防止内存泄漏"""
        current_time = time.time()
        cleanup_interval = self._get_config("cleanup_interval", 3600)
        cooldown_seconds = self._get_config("cooldown_seconds", 30)
        
        # 检查是否需要清理
        if current_time - self._last_cleanup_time < cleanup_interval:
            return
        
        async with self._cooldown_lock:
            # 找出过期的记录（超过冷却时间2倍的视为过期）
            expired_threshold = cooldown_seconds * 2
            expired_keys = [
                uid for uid, t in self._user_cooldown.items()
                if current_time - t > expired_threshold
            ]
            
            # 删除过期记录
            for uid in expired_keys:
                del self._user_cooldown[uid]
            
            if expired_keys:
                logger.debug(f"清理了 {len(expired_keys)} 条过期冷却记录")
            
            self._last_cleanup_time = current_time
    
    async def _check_cooldown(self, user_id: str) -> tuple[bool, int]:
        """
        检查用户是否处于冷却状态
        
        Args:
            user_id: 用户ID
        
        Returns:
            (是否可用, 剩余冷却秒数)
        """
        # 如果冷却机制被禁用，直接返回可用
        if not self._get_config("enable_cooldown", True):
            return True, 0
        
        # 先清理过期记录
        await self._cleanup_old_cooldown()
        
        cooldown_seconds = self._get_config("cooldown_seconds", 30)
        current_time = time.time()
        
        async with self._cooldown_lock:
            last_request = self._user_cooldown.get(user_id, 0)
            
            if current_time - last_request < cooldown_seconds:
                remaining = int(cooldown_seconds - (current_time - last_request))
                return False, remaining
        
        return True, 0
    
    async def _update_cooldown(self, user_id: str):
        """更新用户最后请求时间"""
        async with self._cooldown_lock:
            self._user_cooldown[user_id] = time.time()
    
    def _validate_input(self, game_name: str, event_desc: str, style: str = "", custom_style: str = "") -> tuple[bool, str]:
        """
        验证输入参数
        
        Args:
            game_name: 游戏名
            event_desc: 事件描述
            style: 风格
            custom_style: 自定义风格
        
        Returns:
            (是否有效, 错误信息)
        """
        max_game_name = self._get_config("max_game_name_length", 50)
        max_event = self._get_config("max_event_length", 500)
        max_custom = self._get_config("max_custom_style_length", 200)
        
        if len(game_name) > max_game_name:
            return False, f"游戏名太长啦，请控制在{max_game_name}字以内"
        
        if len(event_desc) > max_event:
            return False, f"事件描述太长啦，请控制在{max_event}字以内"
        
        if custom_style and len(custom_style) > max_custom:
            return False, f"自定义风格描述太长啦，请控制在{max_custom}字以内"
        
        if len(game_name) < 1:
            return False, "游戏名不能为空"
        
        if len(event_desc) < 2:
            return False, "事件描述至少需要2个字"
        
        return True, ""
    
    def _parse_command(self, content: str) -> tuple[str, str, str, str]:
        """
        解析命令参数
        
        Args:
            content: 去除命令前缀后的内容
        
        Returns:
            (游戏名, 事件描述, 风格, 自定义风格描述)
        """
        if not content:
            return "", "", self._get_config("default_style", "默认"), ""
        
        parts = content.split()
        
        if len(parts) < 2:
            return "", "", self._get_config("default_style", "默认"), ""
        
        game_name = parts[0]
        
        # 检查是否是DIY自定义风格模式
        # 格式: /尽孝 游戏 事件 diy 自定义风格描述
        diy_index = None
        for i, part in enumerate(parts):
            if part.lower() == "diy":
                diy_index = i
                break
        
        if diy_index is not None and diy_index >= 2:
            # DIY模式：游戏名 事件 diy 自定义风格
            event_desc = " ".join(parts[1:diy_index])
            custom_style = " ".join(parts[diy_index+1:]) if diy_index + 1 < len(parts) else ""
            return game_name, event_desc, "diy", custom_style
        
        # 检查最后一部分是否是已知风格
        potential_style = parts[-1]
        
        # 检查是否是已知的风格名称或别名
        _, style_desc = get_style_modifier(potential_style)
        is_known_style = style_desc != "标准尽孝风格，情感真挚，立场鲜明" or potential_style in ["默认", "default", "正常", "普通"]
        
        # 如果最后一部分是已知风格，且前面有足够的内容作为事件描述
        if is_known_style and len(parts) >= 3:
            # 事件描述是中间部分（去掉游戏名和风格）
            event_desc = " ".join(parts[1:-1])
            style = potential_style
        else:
            # 没有指定风格，使用默认
            event_desc = " ".join(parts[1:])
            style = self._get_config("default_style", "默认")
        
        return game_name, event_desc, style, ""
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词，支持配置覆盖"""
        custom_prompt = self._get_config("system_prompt")
        if custom_prompt:
            return custom_prompt
        
        # 默认系统提示词
        return """你是一位深度热爱游戏的玩家，你将游戏公司视为精神寄托，对其倾注全部的热爱与支持。你的写作风格极具深度和感染力，情感真挚而强烈。

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
    
    @filter.command("尽孝")
    async def wwkudie_command(self, event: AstrMessageEvent):
        """尽孝命令主处理函数"""
        # 获取用户ID用于冷却控制
        user_id = event.get_sender_id()
        
        # 检查冷却时间
        can_use, remaining = await self._check_cooldown(user_id)
        if not can_use:
            yield event.plain_result(f"⏳ 请稍等{remaining}秒后再使用尽孝功能")
            return
        
        # 获取消息内容（包含命令前缀，需要手动移除）
        full_msg = event.message_str.strip()
        
        # 移除命令前缀 /尽孝
        content = full_msg
        if content.startswith('/尽孝'):
            content = content[3:].strip()
        
        if not content:
            yield event.plain_result("请提供游戏名和事件描述！\n使用方式：/尽孝 游戏名 事件描述 [风格/diy 自定义风格]\n\n可用风格：/尽孝风格")
            return
        
        # 解析参数
        game_name, event_desc, style, custom_style = self._parse_command(content)
        
        if not game_name or not event_desc:
            yield event.plain_result("请提供游戏名和事件描述！\n使用方式：/尽孝 游戏名 事件描述 [风格/diy 自定义风格]\n\n可用风格：/尽孝风格")
            return
        
        # 验证输入
        is_valid, error_msg = self._validate_input(game_name, event_desc, style, custom_style)
        if not is_valid:
            yield event.plain_result(f"❌ {error_msg}")
            return
        
        # 更新冷却时间
        await self._update_cooldown(user_id)
        
        try:
            # 获取风格描述用于显示
            if style == "diy":
                style_display = f"DIY:{custom_style[:20]}..." if len(custom_style) > 20 else f"DIY:{custom_style}"
            else:
                style_display = style if style != "默认" else "默认风格"
            
            yield event.plain_result(f"🖊️ 正在尽孝... [{style_display}]")
            
            umo = event.unified_msg_origin
            provider_id = await self.context.get_current_chat_provider_id(umo=umo)
            
            if not provider_id:
                yield event.plain_result("❌ 错误：未找到 LLM 提供商，请先配置AI模型")
                return
            
            # 获取系统提示词
            system_prompt = self._get_system_prompt()
            
            # 根据是否DIY模式构建不同的prompt
            if style == "diy" and custom_style:
                full_prompt = f"{system_prompt}\n\n{build_article_prompt_with_custom_style(game_name, event_desc, custom_style)}"
            else:
                full_prompt = f"{system_prompt}\n\n{build_article_prompt(game_name, event_desc, style)}"
            
            llm_resp = await self.context.llm_generate(
                chat_provider_id=provider_id,
                prompt=full_prompt,
            )
            
            # 使用解析器解析响应
            response_text = LLMResponseParser.parse(llm_resp)
            
            if response_text:
                yield event.plain_result(response_text)
            else:
                if llm_resp is None:
                    logger.error("LLM响应为None")
                    yield event.plain_result("❌ 生成失败：AI没有返回响应")
                else:
                    logger.error(f"无法解析LLM响应: {type(llm_resp)}, {llm_resp}")
                    yield event.plain_result("❌ 生成失败：无法解析AI响应")
        
        except asyncio.TimeoutError:
            logger.error("LLM生成超时")
            yield event.plain_result("⏰ 生成超时，请稍后再试")
        
        except Exception as e:
            logger.error(f"尽孝插件错误: {str(e)}", exc_info=True)
            # 向用户显示友好的错误信息，不暴露内部细节
            error_message = str(e).lower()
            if "rate" in error_message or "limit" in error_message:
                yield event.plain_result("🚫 API调用频率限制，请稍后再试")
            elif "connect" in error_message or "network" in error_message:
                yield event.plain_result("🔌 网络连接失败，请检查网络配置")
            elif "timeout" in error_message:
                yield event.plain_result("⏰ 生成超时，请稍后再试")
            else:
                yield event.plain_result(f"❌ 生成失败，请稍后重试")
    
    @filter.command("尽孝风格")
    async def wwkudie_styles(self, event: AstrMessageEvent):
        """显示所有可用风格"""
        styles = get_available_styles()
        
        style_list = ["🎨 尽孝插件 - 可用风格列表\n"]
        
        for i, style in enumerate(styles, 1):
            name = style["name"]
            desc = style["description"]
            alias = ", ".join(style["alias"])
            style_list.append(f"{i}. 【{name}】{desc}")
            style_list.append(f"   别名: {alias}\n")
        
        style_list.append("\n🎨 DIY自定义风格：")
        style_list.append("使用 diy 关键字+你的风格描述")
        style_list.append("\n💡 使用方式：")
        style_list.append("/尽孝 游戏名 事件描述 [风格]")
        style_list.append("/尽孝 游戏名 事件 diy 你的风格要求")
        style_list.append("\n示例：")
        style_list.append("/尽孝 鸣潮 新角色上线 激烈反问")
        style_list.append("/尽孝 原神 版本更新 diy 用鲁迅的口吻写")
        style_list.append("/尽孝 王者荣耀 新英雄 diy 模仿新闻联播播音员")
        
        yield event.plain_result("\n".join(style_list))
    
    @filter.command("尽孝帮助")
    async def wwkudie_help(self, event: AstrMessageEvent):
        """显示帮助信息"""
        help_text = """🎮 尽孝插件使用帮助

📖 命令格式：
/尽孝 游戏名 事件描述 [风格/diy 自定义风格]

✨ 使用示例：
/尽孝 鸣潮 有人黑角色西格莉卡绑男角色仇远所以不抽西格莉卡
/尽孝 原神 3.0版本须弥开放 激烈反问
/尽孝 王者荣耀 新英雄上线 数据分析
/尽孝 崩坏星穹铁道 剧情太刀 diy 用鲁迅的口吻写

🎨 内置风格（/尽孝风格 查看全部）：
• 默认 - 标准尽孝风格
• 文言文 - 史书笔法，典雅厚重
• 赞美诗歌 - 诗意盎然，像写情书
• 数据分析 - 用数据说话，专业可信
• 激烈反问 - 结构化反问，层层递进
• 商业精英 - 互联网黑话，精英范儿
• 业内人士 - 揭秘内幕，专业接地气

🎨 DIY自定义风格：
使用 diy 关键字+你的风格描述
/尽孝 游戏 事件 diy 你的风格要求

⚠️ 注意事项：
• 游戏名最多50字（可在配置中调整）
• 事件描述最多500字（可在配置中调整）
• 自定义风格描述最多200字
• 每次使用后有30秒冷却时间（可在配置中调整）
• 风格不填则使用默认风格

⚙️ 配置说明：
在AstrBot管理面板中可以配置：
• 冷却时间
• 最大长度限制
• 默认风格
• 系统提示词
• 是否启用冷却机制

💡 提示：
描述越详细，生成的文章越有深度！"""
        yield event.plain_result(help_text)
    
    @filter.command("尽孝状态")
    async def wwkudie_status(self, event: AstrMessageEvent):
        """查看插件状态"""
        user_id = event.get_sender_id()
        
        # 检查是否处于冷却
        can_use, remaining = await self._check_cooldown(user_id)
        
        if can_use:
            status_text = "✅ 可以使用尽孝功能"
        else:
            status_text = f"⏳ 冷却中，还需等待{remaining}秒"
        
        yield event.plain_result(status_text)
