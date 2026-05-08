"""
尽孝插件主逻辑
v2.0.0 重构版本
"""

import asyncio
from pathlib import Path
from typing import Optional

from astrbot.api import logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register

from ._version import __version__, __plugin_name__, __plugin_desc__, __author__
from .core.config_manager import ConfigManager
from .core.cooldown_manager import CooldownManager
from .core.style_manager import StyleManager
from .core.prompt_builder import PromptBuilder
from .core.article_generator import ArticleGenerator
from .core.history_manager import HistoryManager
from .utils.validators import InputValidator
from .utils.exceptions import ValidationError, CooldownError, RateLimitError


@register(__plugin_name__, __author__, __plugin_desc__, __version__)
class WwkudiePlugin(Star):
    """尽孝插件主类"""
    
    def __init__(self, context: Context):
        super().__init__(context)
        
        # 初始化配置管理器
        self._config = ConfigManager(context)
        
        # 初始化冷却管理器
        self._cooldown = CooldownManager(
            cooldown_seconds=self._config.get("cooldown_seconds", 30),
            cleanup_interval=self._config.get("cleanup_interval", 3600),
            enable_cooldown=self._config.get("enable_cooldown", True),
            enable_rate_limit=self._config.get("enable_rate_limit", True),
            rate_limit_count=self._config.get("rate_limit_count", 10),
            rate_limit_window=self._config.get("rate_limit_window", 3600),
        )
        
        # 初始化风格管理器
        self._style_manager = StyleManager()
        
        # 初始化提示词构建器
        self._prompt_builder = PromptBuilder(self._style_manager)
        
        # 初始化文章生成器
        self._generator = ArticleGenerator(
            context=context,
            config_manager=self._config,
            prompt_builder=self._prompt_builder,
        )
        
        # 初始化历史记录管理器
        data_dir = Path(__file__).parent / "data"
        self._history = HistoryManager(
            data_dir=data_dir,
            max_history_per_user=self._config.get("max_history_per_user", 10),
        )
        
        logger.info(f"尽孝插件 v{__version__} 已初始化")
    
    async def _check_permission(self, user_id: str) -> tuple[bool, Optional[str]]:
        """
        检查用户权限（冷却 + 限流）
        
        Returns:
            (是否允许, 错误信息)
        """
        # 检查冷却
        can_use, cooldown_remaining = await self._cooldown.check_cooldown(user_id)
        if not can_use:
            return False, f"⏳ 请稍等{cooldown_remaining}秒后再使用尽孝功能"
        
        # 检查限流
        can_use, current_count, remaining = await self._cooldown.check_rate_limit(user_id)
        if not can_use:
            return False, f"🚫 您已达到使用上限（每小时{self._config.get('rate_limit_count', 10)}次），请{remaining}秒后再试"
        
        return True, None
    
    def _parse_article_args(self, content: str) -> tuple[str, str, str, str]:
        """
        解析文章生成命令参数
        
        Args:
            content: AstrBot 已移除命令前缀后的内容
        
        Returns:
            (游戏名, 事件描述, 风格, 自定义风格)
        """
        if not content:
            return "", "", self._config.get("default_style", "默认"), ""
        
        parts = content.split()
        
        if len(parts) < 2:
            return "", "", self._config.get("default_style", "默认"), ""
        
        game_name = parts[0]
        
        # 检查是否是 DIY 自定义风格模式
        # 格式: /尽孝 游戏 事件 diy 自定义风格描述
        diy_index = None
        for i, part in enumerate(parts):
            if part.lower() == "diy":
                diy_index = i
                break
        
        if diy_index is not None and diy_index >= 2:
            event_desc = " ".join(parts[1:diy_index])
            custom_style = " ".join(parts[diy_index + 1:]) if diy_index + 1 < len(parts) else ""
            return game_name, event_desc, "diy", custom_style
        
        # 检查最后一部分是否是已知风格
        potential_style = parts[-1]
        is_known_style = self._style_manager.is_valid_style(potential_style)
        
        # 如果最后一部分是已知风格，且前面有足够的内容
        if is_known_style and len(parts) >= 3:
            event_desc = " ".join(parts[1:-1])
            style = potential_style
        else:
            # 没有指定风格，使用默认
            event_desc = " ".join(parts[1:])
            style = self._config.get("default_style", "默认")
        
        return game_name, event_desc, style, ""
    
    # ==================== 命令处理 ====================
    
    @filter.command("尽孝")
    async def wwkudie_command(self, event: AstrMessageEvent):
        """尽孝命令 - 生成单篇文章"""
        user_id = event.get_sender_id()
        
        # 权限检查
        can_use, error_msg = await self._check_permission(user_id)
        if not can_use:
            yield event.plain_result(error_msg)
            return
        
        # 获取命令参数（AstrBot 已移除命令前缀）
        content = event.message_str.strip()
        
        if not content:
            yield event.plain_result(
                "请提供游戏名和事件描述！\n"
                "使用方式：/尽孝 游戏名 事件描述 [风格/diy 自定义风格]\n\n"
                "可用风格：/尽孝风格"
            )
            return
        
        # 解析参数
        game_name, event_desc, style, custom_style = self._parse_article_args(content)
        
        if not game_name or not event_desc:
            yield event.plain_result(
                "请提供游戏名和事件描述！\n"
                "使用方式：/尽孝 游戏名 事件描述 [风格/diy 自定义风格]\n\n"
                "可用风格：/尽孝风格"
            )
            return
        
        # 验证输入
        is_valid, error_msg = InputValidator.validate_article_input(
            game_name=game_name,
            event_desc=event_desc,
            style=style,
            custom_style=custom_style,
            max_game_name_length=self._config.get("max_game_name_length", 50),
            max_event_length=self._config.get("max_event_length", 500),
            max_custom_style_length=self._config.get("max_custom_style_length", 200),
        )
        if not is_valid:
            yield event.plain_result(f"❌ {error_msg}")
            return
        
        # 记录请求
        await self._cooldown.record_request(user_id)
        
        # 显示风格信息
        if style == "diy":
            style_display = f"DIY:{custom_style[:20]}..." if len(custom_style) > 20 else f"DIY:{custom_style}"
        else:
            _, _, icon = self._style_manager.get_style(style)
            style_display = f"{icon} {style}" if style != "默认" else "默认风格"
        
        yield event.plain_result(f"🖊️ 正在尽孝... [{style_display}]")
        
        # 生成文章
        success, result = await self._generator.generate(
            event=event,
            game_name=game_name,
            event_desc=event_desc,
            style=style,
            custom_style=custom_style if style == "diy" else None,
        )
        
        if success:
            # 保存历史记录
            if self._config.get("enable_history", True):
                self._history.add_record(
                    user_id=user_id,
                    game_name=game_name,
                    event_desc=event_desc,
                    style=style if style != "diy" else f"diy:{custom_style}",
                    article=result,
                )
            yield event.plain_result(result)
        else:
            yield event.plain_result(result)
    
    @filter.command("尽孝风格")
    async def wwkudie_styles(self, event: AstrMessageEvent):
        """显示所有可用风格"""
        styles = self._style_manager.get_all_styles()
        
        lines = ["🎨 尽孝插件 - 可用风格列表\n"]
        
        for i, style in enumerate(styles, 1):
            name = style["name"]
            desc = style["description"]
            alias = ", ".join(style["alias"])
            icon = style.get("icon", "✨")
            lines.append(f"{i}. {icon} 【{name}】{desc}")
            lines.append(f"   别名: {alias}\n")
        
        lines.extend([
            "\n🎨 DIY自定义风格：",
            "使用 diy 关键字+你的风格描述",
            "\n💡 使用方式：",
            "/尽孝 游戏名 事件描述 [风格]",
            "/尽孝 游戏名 事件 diy 你的风格要求",
            "\n示例：",
            "/尽孝 鸣潮 新角色上线 激烈反问",
            "/尽孝 原神 版本更新 diy 用鲁迅的口吻写",
        ])
        
        yield event.plain_result("\n".join(lines))
    
    @filter.command("尽孝历史")
    async def wwkudie_history(self, event: AstrMessageEvent):
        """查看历史记录"""
        if not self._config.get("enable_history", True):
            yield event.plain_result("❌ 历史记录功能未启用")
            return
        
        user_id = event.get_sender_id()
        records = self._history.get_history(user_id, limit=5)
        
        if not records:
            yield event.plain_result("📭 您还没有生成过尽孝文章")
            return
        
        lines = ["📜 您的尽孝历史记录\n"]
        
        for i, record in enumerate(records, 1):
            from datetime import datetime
            timestamp = datetime.fromtimestamp(record["timestamp"]).strftime("%m-%d %H:%M")
            game = record["game_name"]
            style = record["style"]
            event_desc = record["event_desc"]
            
            lines.append(f"{i}. [{timestamp}] {game}")
            lines.append(f"   风格: {style}")
            lines.append(f"   事件: {event_desc[:30]}...\n")
        
        lines.append(f"\n共 {len(records)} 条记录（最多保留 {self._config.get('max_history_per_user', 10)} 条）")
        
        yield event.plain_result("\n".join(lines))
    
    @filter.command("尽孝清除")
    async def wwkudie_clear(self, event: AstrMessageEvent):
        """清除历史记录"""
        if not self._config.get("enable_history", True):
            yield event.plain_result("❌ 历史记录功能未启用")
            return
        
        user_id = event.get_sender_id()
        success = self._history.clear_history(user_id)
        
        if success:
            yield event.plain_result("✅ 已清除您的尽孝历史记录")
        else:
            yield event.plain_result("📭 您还没有历史记录需要清除")
    
    @filter.command("尽孝状态")
    async def wwkudie_status(self, event: AstrMessageEvent):
        """查看插件状态"""
        user_id = event.get_sender_id()
        
        # 获取用户统计
        user_stats = await self._cooldown.get_user_stats(user_id)
        
        lines = [
            "📊 尽孝插件状态",
            f"\n版本: v{__version__}",
            f"作者: {__author__}",
            f"\n您的状态:",
        ]
        
        if user_stats["is_cooldown_active"]:
            lines.append(f"⏳ 冷却中，还需等待 {user_stats['cooldown_remaining']} 秒")
        else:
            lines.append("✅ 可以使用尽孝功能")
        
        lines.extend([
            f"📈 当前窗口请求数: {user_stats['requests_in_window']}",
            f"🎯 剩余可用次数: {user_stats['rate_limit_remaining']}",
            f"📊 总请求次数: {user_stats['total_requests']}",
        ])
        
        # 全局统计
        global_stats = self._cooldown.get_global_stats()
        lines.extend([
            f"\n全局统计:",
            f"👥 活跃用户数: {global_stats['tracked_users']}",
            f"⏱️ 冷却时间: {global_stats['cooldown_seconds']}秒",
            f"🎯 每小时限流: {global_stats['rate_limit_count']}次",
        ])
        
        # 历史记录统计
        if self._config.get("enable_history", True):
            history_stats = self._history.get_stats()
            lines.extend([
                f"\n历史记录:",
                f"📝 总记录数: {history_stats['total_records']}",
                f"👤 总用户数: {history_stats['total_users']}",
            ])
        
        # 风格数量
        lines.append(f"\n🎨 可用风格数: {self._style_manager.get_style_count()}")
        
        yield event.plain_result("\n".join(lines))
    
    @filter.command("尽孝帮助")
    async def wwkudie_help(self, event: AstrMessageEvent):
        """显示帮助信息"""
        help_text = """🎮 尽孝插件 v2.0.0 使用帮助

📖 基础命令：
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
• 新闻联播 - 庄重权威的新闻播报
• 学术期刊 - 严谨的学术论文风格

🎨 DIY自定义风格：
使用 diy 关键字+你的风格描述
/尽孝 游戏 事件 diy 你的风格要求

📜 其他命令：
/尽孝历史 - 查看您的生成历史
/尽孝清除 - 清除您的历史记录
/尽孝状态 - 查看插件和个人状态
/尽孝风格 - 查看所有可用风格

⚠️ 限制说明：
• 游戏名最多50字
• 事件描述最多500字
• 自定义风格描述最多200字
• 每次使用后有30秒冷却时间
• 每小时最多使用10次
• 风格不填则使用默认风格

⚙️ 配置说明：
在AstrBot管理面板中可以配置：
• 冷却时间和限流设置
• 最大长度限制
• 默认风格
• 系统提示词
• 是否启用历史记录

💡 提示：
描述越详细，生成的文章越有深度！
使用 diy 模式可以创造无限可能！"""
        
        yield event.plain_result(help_text)
