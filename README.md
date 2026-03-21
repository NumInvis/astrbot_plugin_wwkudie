# 尽孝插件 - AstrBot 游戏评论生成插件

一个 AstrBot 插件，用于生成热爱游戏、把游戏公司当父亲尽孝风格的游戏深度评论文章。

## 功能特性

- 📝 自动生成尽孝风格的游戏深度评论
- 🎯 支持任意游戏，不局限于鸣潮
- ✨ 独特的尽孝写作风格
- 🎨 完全符合 AstrBot 官方插件规范

## 安装方法

### 方法一：通过 AstrBot 插件商店安装
1. 打开 AstrBot 管理面板
2. 进入插件商店
3. 搜索「尽孝」
4. 点击安装

### 方法二：手动安装
1. 将 `astrbot_plugin_wwkudie` 文件夹复制到 AstrBot 的 `data/plugins` 目录下
2. 重启 AstrBot
3. 插件自动加载

## 使用方法

### 命令格式

```
/尽孝 游戏名 事件描述
```

### 使用示例

```
/尽孝 鸣潮 有人黑角色西格莉卡绑男角色仇远所以不抽西格莉卡
/尽孝 原神 3.0版本须弥开放
/尽孝 王者荣耀 新英雄上线
```

### 其他命令

- `/尽孝帮助` - 显示帮助信息

## 写作风格特点

- 强烈的情感色彩
- 善于使用反问和排比
- 站在道德制高点批判反对者
- 无条件支持所热爱的游戏和游戏公司

## 代码结构

```
astrbot_plugin_wwkudie/
├── __init__.py       # 插件入口
├── _version.py       # 版本信息
├── main.py           # 插件主逻辑
├── prompts.py        # Prompt 配置文件
├── metadata.yaml     # 插件配置
├── requirements.txt  # 依赖文件
├── README.md         # 说明文档
└── LICENSE           # 许可证
```

## Prompt 文件说明

`prompts.py` 包含了两个核心部分：

1. **SYSTEM_PROMPT** - 系统提示词，定义尽孝风格的角色、写作风格、立场等
2. **build_article_prompt()** - 构建用户提示词的函数，解析游戏名和事件

## 依赖要求

- AstrBot 4.0+
- 已配置好的 LLM 提供商

## 注意事项

- 确保 AstrBot 已正确配置 AI 模型
- 建议根据实际需要调整 `prompts.py` 中的提示词

## 许可证

MIT License

## 作者

NumInvis

## 仓库

https://github.com/NumInvis/astrbot_plugin_wwkudie
