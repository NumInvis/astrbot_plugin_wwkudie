SYSTEM_PROMPT = """你是一位深度热爱游戏的玩家，你将游戏公司视为精神寄托，对其倾注全部的热爱与支持。你的写作风格极具深度和感染力，情感真挚而强烈。

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


# 风格配置字典 - 精简为6个核心风格
STYLE_CONFIGS = {
    "默认": {
        "alias": ["default", "正常", "普通", "标准"],
        "modifier": "",
        "description": "标准尽孝风格，情感真挚，立场鲜明"
    },
    "文言文": {
        "alias": ["古文", "文言", "古典", "史记", "春秋", "history"],
        "modifier": """模仿《史记》《左传》《战国策》等先秦两汉史书笔法，用典雅的文言文或文白相间的语言撰写。

具体要求：
1. 使用"之乎者也矣焉哉"等文言虚词，如"夫","盖","然则","是故"
2. 采用史传体例，开篇可用"初""昔者""方今"等时间词
3. 人物称述用字号或尊称，如"某某氏"
4. 文末可加"太史公曰""君子曰""赞曰"等史评
5. 用词古朴典雅，如以"谓"代"说"，以"甚"代"很"
6. 句式长短错落，有节奏感
7. 可适当引用典故，增加厚重感

示例句式："夫《某某》者，乃当世之杰作也。初，众人未识其妙...""",
        "description": "史书笔法，古文风格，典雅厚重"
    },
    "赞美诗歌": {
        "alias": ["诗歌", "诗意", "抒情", "文艺", "poem", "诗"],
        "modifier": """以诗人的浪漫情怀和抒情笔触，将游戏赞美提升到艺术高度。

具体要求：
1. 使用大量优美意象：星辰、大海、晨曦、繁花、烈火等
2. 多用比喻、拟人、通感等修辞：如"这款游戏如一首史诗"
3. 语言如诗如画，有韵律感和节奏感
4. 情感浓烈真挚，像写情书一样倾诉热爱
5. 可适当使用排比句增强气势
6. 用词优美华丽，如"璀璨""瑰丽"" sublime"等
7. 营造唯美浪漫的氛围

示例表达："它不仅是游戏，更是一首写给所有玩家的情书，在虚拟与现实的交界处，绽放出最动人的光芒。""",
        "description": "诗意盎然，像写情书一样赞美游戏"
    },
    "数据分析": {
        "alias": ["数据", "理性", "分析", "统计", "data", "数字"],
        "modifier": """以专业数据分析师和行业研究员的口吻，用"数据"说话。

具体要求：
1. 编造看似专业的数据：如"DAU突破500万""留存率提升37.5%""NPS评分9.2"
2. 使用数据来源表述："据内部消息""行业数据显示""第三方机构统计"
3. 运用对比分析："环比增长""同比提升""市占率扩大"
4. 使用专业术语：用户画像、付费转化率、LTV、ROI、ARPU
5. 引用"研究报告"：如"艾瑞咨询报告指出"
6. 用数据支撑每一个论点，显得有理有据
7. 语气客观理性，但结论必然是游戏大获成功

示例表达："据伽马数据最新统计，该游戏月活跃用户已突破1200万，DAU/MAU比值高达45%，远超行业平均水平的28%。""",
        "description": "用数据和统计支撑观点，显得专业可信"
    },
    "激烈反问": {
        "alias": ["反问", "激烈", "质问", "intense", "质疑"],
        "modifier": """采用结构化反问论证法，以强有力的质问展现观点的不可辩驳。

具体要求：
1. 开篇明确提出"我想问反对者X个问题"或"有几个问题不吐不快"
2. 采用"第一问...第二问...第三问..."的清晰结构
3. 每个问题都要直击要害，逻辑严密
4. 问题之间要有递进关系，层层深入
5. 每个反问后紧跟简短有力的论证
6. 结尾用总结性反问收束全文
7. 语气坚定有力，但不失风度

结构模板：
- 开篇：引出争议，表明立场
- 主体：我想问反对者四个问题
  第一问：关于...（反问+论证）
  第二问：关于...（反问+论证）
  第三问：关于...（反问+论证）
  第四问：关于...（反问+论证）
- 结尾：总结升华

示例："第一问：当你们说游戏氪金时，可曾算过一天一杯奶茶钱就能获得的快乐，难道不比这更值得？""",
        "description": "结构化反问论证，层层递进，气势逼人"
    },
    "商业精英": {
        "alias": ["商业", "精英", "老板", "MBA", "business", "资本"],
        "modifier": """以成功企业家、投资人和商业领袖的视角，从商业维度深度解读游戏价值。

具体要求：
1. 大量使用互联网/商业黑话：生态、闭环、抓手、赋能、颗粒度、底层逻辑、顶层设计
2. 从商业模式角度分析：变现能力、护城河、增长飞轮、第二曲线
3. 使用投资术语：赛道、风口、壁垒、估值、PMF、规模化
4. 强调战略眼光和长期价值
5. 分析用户价值：LTV、CAC、用户生命周期
6. 引用商业案例和成功企业对标
7. 语气自信专业，像董事会汇报

高频词汇：底层逻辑、顶层设计、商业模式、闭环、生态、抓手、赋能、颗粒度、赛道、壁垒、护城河、LTV、ROI、规模化、PMF、战略定力

示例表达："从底层逻辑来看，这款游戏成功构建了用户增长的飞轮效应，通过社交裂变形成闭环，在垂直赛道建立了深厚的护城河。""",
        "description": "商业视角，满嘴互联网黑话，精英范儿"
    },
    "业内人士": {
        "alias": ["业内", "内部", "从业者", "开发者", "insider", "专业"],
        "modifier": """以游戏行业资深从业者、开发者或内部人士的口吻，从专业角度揭秘游戏制作的匠心。

具体要求：
1. 使用游戏开发专业术语：渲染管线、物理引擎、AI寻路、关卡设计、数值平衡
2. 透露"内部消息"：据项目组朋友说、内部人士透露、参与过测试知道
3. 分析技术难点和解决方案：优化、兼容性、网络同步
4. 讲述开发背后的故事：加班、迭代、玩家的反馈改变了设计
5. 对比行业现状：其他厂商做不到、这是业内的共识
6. 强调制作团队的用心和付出
7. 语气像圈内人聊天，有专业深度又接地气

高频词汇：引擎、渲染、优化、迭代、版本、策划、程序、美术、QA、数值、关卡、剧情、沉浸感、心流、反馈机制

示例表达："作为从业十年的老策划，我深知这个交互设计背后的心血。据项目组的朋友说，为了这个手感，他们迭代了47个版本，这种工匠精神在当今快餐化时代实属难得。""",
        "description": "圈内人视角，揭秘开发内幕，专业接地气"
    }
}


def get_style_modifier(style_name: str) -> tuple[str, str]:
    """
    获取风格的修饰词和描述
    
    Args:
        style_name: 风格名称或别名
    
    Returns:
        (修饰词, 风格描述)
    """
    style_name = style_name.strip()
    
    # 直接匹配
    if style_name in STYLE_CONFIGS:
        config = STYLE_CONFIGS[style_name]
        return config["modifier"], config["description"]
    
    # 别名匹配
    for style_key, config in STYLE_CONFIGS.items():
        if style_name in config["alias"]:
            return config["modifier"], config["description"]
    
    # 默认返回空（默认风格）
    return "", STYLE_CONFIGS["默认"]["description"]


def get_available_styles() -> list[dict]:
    """
    获取所有可用风格列表
    
    Returns:
        风格列表，每项包含名称、描述和别名
    """
    styles = []
    for name, config in STYLE_CONFIGS.items():
        styles.append({
            "name": name,
            "description": config["description"],
            "alias": config["alias"]
        })
    return styles


def build_article_prompt(game_name: str, event_desc: str, style: str = "默认") -> str:
    """
    构建文章生成提示词
    
    Args:
        game_name: 游戏名称
        event_desc: 事件描述
        style: 写作风格，可选值见 STYLE_CONFIGS
    
    Returns:
        完整的用户提示词
    """
    # 清理输入，移除可能导致问题的字符
    game_name = game_name.strip()
    event_desc = event_desc.strip()
    
    # 确保输入不为空
    if not game_name:
        game_name = "游戏"
    if not event_desc:
        event_desc = "相关事件"
    
    # 获取风格修饰词
    style_modifier, _ = get_style_modifier(style)
    
    base_prompt = f"""游戏：{game_name}
事件：{event_desc}

请根据上述游戏和事件，撰写一篇符合风格要求的深度游戏评论文章新闻稿。"""
    
    if style_modifier:
        return f"{base_prompt}\n\n【风格要求】{style_modifier}"
    
    return base_prompt


def build_article_prompt_with_style(game_name: str, event_desc: str, style: str = "default") -> str:
    """
    构建带特定风格的文章生成提示词（兼容旧接口）
    
    Args:
        game_name: 游戏名称
        event_desc: 事件描述
        style: 写作风格
    
    Returns:
        完整的用户提示词
    """
    return build_article_prompt(game_name, event_desc, style)


def build_article_prompt_with_custom_style(game_name: str, event_desc: str, custom_style: str) -> str:
    """
    构建带自定义风格的文章生成提示词
    
    Args:
        game_name: 游戏名称
        event_desc: 事件描述
        custom_style: 用户自定义的风格描述
    
    Returns:
        完整的用户提示词
    """
    # 清理输入，移除可能导致问题的字符
    game_name = game_name.strip()
    event_desc = event_desc.strip()
    custom_style = custom_style.strip()
    
    # 确保输入不为空
    if not game_name:
        game_name = "游戏"
    if not event_desc:
        event_desc = "相关事件"
    if not custom_style:
        custom_style = "保持原有的尽孝风格"
    
    base_prompt = f"""游戏：{game_name}
事件：{event_desc}

请根据上述游戏和事件，撰写一篇符合风格要求的深度游戏评论文章新闻稿。"""
    
    return f"{base_prompt}\n\n【自定义风格要求】{custom_style}\n\n请严格按照上述自定义风格要求来撰写文章，同时保持对游戏的热爱和吹捧立场。"
