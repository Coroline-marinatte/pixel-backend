import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    # 服务器配置
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = True

    # AI API 配置
    # OpenRouter 配置
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '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')
    OPENROUTER_API_URL = os.getenv('OPENROUTER_API_URL', 'https://openrouter.ai/api/v1')
    OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'meta-llama/llama-3.3-70b-instruct:free')  # 默认用 Llama 3.3

    # 图像生成API配置（可选：豆包、即梦等）
    MODELSCOPE_API_KEY = os.getenv('MODELSCOPE_API_KEY', '')
    IMAGEROUTER_API_URL = 'https://api.imagerouter.io/v1/openai/images/generations'
    # 系统提示词模板
    SYSTEM_PROMPT = """你是一位专业的像素游戏美术概念设计师，精通2D横版游戏背景设计。

请严格按照以下步骤分析用户输入：
1. 识别场景类型（街道、森林、室内、废墟等）
2. 分析核心氛围（沉郁、神秘、温暖、冷峻等）
3. 提取3-4个关键叙事元素
4. 提供符合像素艺术特点的色彩建议
5. 给出适合游戏背景的光照描述

输出必须为JSON格式，包含以下字段：
- scene_type: 场景类型
- mood: 氛围描述
- key_elements: 关键元素列表（最多4个）
- color_scheme: 色彩方案描述
- lighting: 光照描述
- foreground_desc: 前景层描述
- midground_desc: 中景层描述
- background_desc: 背景层描述

请用英文生成描述，但保持专业性和准确性。"""