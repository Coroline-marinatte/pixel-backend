import sys
print("DEBUG: 开始导入", flush=True)

print("1. 正在导入 flask...", flush=True)
from flask import Flask, request, jsonify, send_from_directory
print("2. flask 导入成功", flush=True)

print("3. 正在导入 flask_cors...", flush=True)
from flask_cors import CORS
print("4. flask_cors 导入成功", flush=True)

print("5. 正在导入 logging...", flush=True)
import logging
print("6. logging 导入成功", flush=True)

print("7. 正在从 prompt_engine 导入...", flush=True)
from prompt_engine import PromptOptimizer, ImageGenerator
print("8. prompt_engine 导入成功", flush=True)

print("9. 正在从 config 导入...", flush=True)
from config import Config
print("10. config 导入成功", flush=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 初始化引擎
prompt_optimizer = PromptOptimizer()
image_generator = ImageGenerator()


@app.route('/api/analyze', methods=['POST'])
def analyze_scene():
    try:
        data = request.get_json()
        if not data or 'scene_desc' not in data:
            return jsonify({'success': False, 'message': '缺少场景描述', 'prompt': None}), 400

        user_input = data['scene_desc']
        user_options = data.get('options', {})

        logger.info(f"收到分析请求: {repr(user_input[:50])}...")

        result = prompt_optimizer.analyze_scene(user_input, user_options)

        return jsonify({
            'success': True,
            'message': '提示词生成成功',
            'prompt': result['prompt'],
            'used_fallback': result.get('used_fallback', False)
        })

    except Exception as e:
        logger.error(f"分析过程出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}',
            'prompt': None
        }), 500


@app.route('/api/generate', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        if 'scene_desc' in data:
            user_input = data['scene_desc']
            user_options = data.get('options', {})
            prompt, _ = prompt_optimizer.generate_prompt_directly(user_input, user_options)
        elif 'prompt' in data:
            prompt = data['prompt']
        else:
            return jsonify({'success': False, 'message': '需要提供场景描述或提示词'}), 400

        width = data.get('width', 1024)
        height = data.get('height', 576)
        result = image_generator.generate_image(prompt, width, height)

        if result['success']:
            return jsonify({
                'success': True,
                'message': '图像生成成功',
                'image_url': result['image_url'],
                'prompt': prompt
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message'],
                'prompt': prompt
            }), 500
    except Exception as e:
        logger.error(f"图像生成出错: {str(e)}")
        return jsonify({'success': False, 'message': f'生成失败: {str(e)}'}), 500


@app.route('/api/test', methods=['POST'])
def test_prompt():
    data = request.get_json()
    user_input = data.get('scene_desc', '测试场景')
    user_options = data.get('options', {})
    prompt, _ = prompt_optimizer.generate_prompt_directly(user_input, user_options)
    return jsonify({'input': user_input, 'prompt': prompt})


@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')


if __name__ == '__main__':
    logger.info(f"启动像素背景生成器API服务器，端口: {Config.PORT}")
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
@app.route('/api/stitch', methods=['POST'])
def stitch_images():
    try:
        data = request.get_json()
        image_urls = data.get('image_urls', [])
        if not image_urls:
            return jsonify({'success': False, 'message': 'No images provided'}), 400

        from PIL import Image
        import requests
        from io import BytesIO

        images = []
        for url in image_urls:
            resp = requests.get(url, timeout=30)
            img = Image.open(BytesIO(resp.content))
            images.append(img)

        # 计算总宽度和最大高度
        total_width = sum(img.width for img in images)
        max_height = max(img.height for img in images)

        # 创建新画布
        new_img = Image.new('RGB', (total_width, max_height))
        x_offset = 0
        for img in images:
            new_img.paste(img, (x_offset, 0))
            x_offset += img.width

        # 保存到 static 目录
        import uuid
        filename = f"stitch_{uuid.uuid4().hex}.png"
        filepath = os.path.join('static', filename)
        new_img.save(filepath)

        image_url = f"http://localhost:5000/static/{filename}"
        return jsonify({'success': True, 'image_url': image_url})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500