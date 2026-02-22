import os
import sys
import locale
import json
import logging
import requests
import io

# 设置环境变量，强制使用 UTF-8
os.environ["PYTHONIOENCODING"] = "utf-8"
# 设置默认区域为 UTF-8（忽略可能的错误）
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except Exception:
    pass

# 重新配置 stdout/stderr（只做一次）
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromptOptimizer:
    def __init__(self):
        self.api_key = Config.OPENROUTER_API_KEY
        print(f"DEBUG - 实际API密钥前8位: {self.api_key[:8] if self.api_key else 'None'}")
        self.api_url = Config.OPENROUTER_API_URL
        self.model_name = Config.OPENROUTER_MODEL

    def generate_prompt_directly(self, user_input, user_options=None):
        """直接调用AI生成完整的像素背景提示词"""
        logger.info("=== generate_prompt_directly 开始执行 ===")
        logger.info(f"user_input 类型: {type(user_input)}, 内容: {repr(user_input[:50])}")
        logger.info(f"API密钥是否存在: {bool(self.api_key)}")
        if self.api_key:
            logger.info(f"API密钥前4位: {self.api_key[:4]}...")

        if not self.api_key:
            logger.error("OpenRouter API key is not set.")
            fallback = self._generate_fallback_prompt(user_input)
            logger.info(f"返回 fallback (无 API key)，类型: {type(fallback)}")
            return fallback

        # 构建系统提示词
        system_prompt = (
            """You are an expert in creating 2D pixel art game backgrounds. Your task is to generate a detailed, structured prompt for an AI image generator, based on the user's scene description.

You must follow this template strictly:

**1. CORE STYLE MANDATE:**
- **Art Style:** Pixel art style. The entire scene must be constructed through the combination of pixel points, possessing a distinct retro-game visual texture.
- **Color Palette:** Choose a muted, limited palette appropriate for the scene. Use earthy tones (dark browns, greys, dull greens) for somber scenes; warm browns and oranges for nostalgic interiors; cool blues and greys for sci-fi; etc. Avoid bright, saturated colors.
- **Composition:** The image must have three clear layers: foreground, mid-ground, and background. Leave ample empty space in the foreground and mid-ground for character interaction. Create depth through overlapping elements and perspective.
- **Detail Presentation:** All elements must be presented through pixel clusters, forming clear shapes and silhouettes. Simplify details but keep key identifiable features.

**2. SCENE SPECIFICS:**
- **Foreground (Bottom Layer):** Describe objects close to the viewer, slightly out of focus to enhance depth. Keep this area clear for gameplay.
- **Mid-ground (Middle Layer - The Main Action Area):** This is the heart of the scene. Describe the main environment and key storytelling elements in detail. Include 3-4 key items that tell a story.
- **Background (Top Layer):** Describe distant elements that provide context and depth (walls, sky, distant structures, etc.).

**3. LIGHTING AND MOOD:**
Describe the primary light source, shadow direction, and overall mood. Make it evocative (e.g., solemn, mysterious, warm).

**4. TECHNICAL EXECUTION:**
- **View:** Perfect side-view for a 2D side-scrolling game.
- **Aspect Ratio:** 16:9.
- **MUST AVOID:** No watercolor/ink styles, no photo textures, no bright vibrant colors, no visual clutter.

**Output:** Only output the final prompt itself, following the above structure exactly. Do not add any explanations, comments, or extra text. The prompt must be in English.

Here is an example of a good prompt (do not copy it, just use it as a style reference):
[Example of a well-structured prompt:
Foreground: a simple wooden stool with a ceramic bowl (slightly blurred for depth).
Mid-ground: a sunken fire pit with a cold kettle; a traditional Lusheng (reed pipe) against the wall; a mud-stained wooden loom; shelves holding ritual masks and ancient songbooks.
Background: wooden walls with a small window letting in dim overcast light, and a doorway to another dark room.
Lighting: soft, directional light from the window, with faint ember glow from the fire pit. Mood: solemn, quiet, nostalgic.
Art style: pixel art, side view, 16:9, muted earthy palette, clean composition, no clutter.]

Now, generate a prompt for the following user request:"""
        )
        logger.info("system_prompt 初始构建完成")

        options = user_options or {}
        if options.get('game_style'):
            system_prompt += f"\n- The game style preferred by users：{options.get('game_style')}"
            logger.info(f"添加了 game_style: {options.get('game_style')}")
        if options.get('color_palette'):
            system_prompt += f"\n- The user's preferred color tone：{options.get('color_palette')}"
            logger.info(f"添加了 color_palette: {options.get('color_palette')}")
        if options.get('lighting'):
            system_prompt += f"\n- User-preferred lighting：{options.get('lighting')}"
            logger.info(f"添加了 lighting: {options.get('lighting')}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "Pixel Background Generator"
        }
        logger.info("headers 构建完成")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        logger.info("messages 构建完成")

        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.8,
            "max_tokens": 1500
        }
        logger.info(f"data 构建完成，model: {self.model_name}")

        try:
            logger.info("进入 try 块，准备发送请求")
            logger.info(f"发送生成提示词请求: {repr(user_input[:50])}...")

            json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            logger.info(f"JSON 序列化完成，长度: {len(json_data)} 字节")

            # 打印请求的简要信息（隐藏密钥）
            safe_headers = {k: v for k, v in headers.items() if k != 'Authorization'}
            logger.info(f"请求 URL: {self.api_url}/chat/completions")
            logger.info(f"请求头: {safe_headers}")

            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                data=json_data,
                timeout=30
            )
            logger.info(f"请求完成，状态码: {response.status_code}")

            if response.status_code == 200:
                logger.info("状态码 200，开始解析响应")
                result = response.json()
                logger.info("响应 JSON 解析成功")
                final_prompt = result['choices'][0]['message']['content']
                logger.info(f"最终提示词类型: {type(final_prompt)}, 长度: {len(final_prompt)}")
                return final_prompt
            else:
                logger.error(f"API 请求失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text[:500]}")
                fallback = self._generate_fallback_prompt(user_input)
                logger.info(f"返回 fallback (API 错误)，类型: {type(fallback)}")
                return fallback

        except Exception as e:
            logger.error(f"发生异常: {str(e)}", exc_info=True)
            fallback = self._generate_fallback_prompt(user_input)
            logger.info(f"返回 fallback (异常)，类型: {type(fallback)}")
            return fallback

    def _generate_fallback_prompt(self, user_input, user_options=None):
        """降级规则引擎：当API不可用时，使用用户选项生成简单但可用的提示词"""
        logger.warning("Generate prompt words using the downgrade rule engine")
        options = user_options or {}
        style = options.get('game_style', 'pixel art')
        color = options.get('color_palette', 'muted earthy')
        light = options.get('lighting', 'overcast')

        return f"""A 2D side-scrolling {style} background concept art of {user_input}.
    View: side-view, 16:9.
    Foreground: clear space for characters.
    Mid-ground: main scene with key elements.
    Background: atmospheric depth.
    Color palette: {color}.
    Lighting: {light}.
    Pixel art style, simplified details, large color blocks."""

    def analyze_scene(self, user_input, user_options=None):
        """兼容旧接口：直接返回提示词（不再是结构化数据）"""
        logger.info(f"analyze_scene 被调用，user_input: {repr(user_input[:50])}")
        prompt = self.generate_prompt_directly(user_input, user_options)
        logger.info(f"generate_prompt_directly 返回的 prompt 类型: {type(prompt)}")
        return {
            'success': True,
            'prompt': prompt
        }

    def _get_art_style(self, style):
        styles = {
            'retro': 'Classic retro pixel art',
            'modern': 'Modern pixel art',
            'lowpoly': 'Low-polygon pixel art',
            'rpg': 'JRPG-style pixel art',
            'indie': 'Indie game pixel art'
        }
        return styles.get(style, styles['retro'])


class ImageGenerator:
    def __init__(self):
        self.api_url = "https://image.pollinations.ai/prompt"


    def generate_image(self, prompt, width=1024, height=576):
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"{self.api_url}/{encoded_prompt}?width={width}&height={height}&nologo=true"
        return {
            'success': True,
            'message': 'Image generation successful',
            'image_url': image_url
        }