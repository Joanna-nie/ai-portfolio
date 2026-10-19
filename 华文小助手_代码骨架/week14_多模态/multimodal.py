# W14 多模态接入：图像理解 + 语音转写
# 依赖：pip install openai python-dotenv（复用 W4）
import os
import sys
import base64

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import weekpath  # noqa: E402  数据路径 + 加载 .env

weekpath.load_env()

import openai  # noqa: E402

_vl = None
_asr = None


def vl_client():
    """通义视觉模型（兼容 OpenAI 接口）——按需创建，缺密钥时给出可操作的报错。"""
    global _vl
    if _vl is None:
        key = os.getenv("DASHSCOPE_API_KEY")
        if not key:
            raise RuntimeError("未配置 DASHSCOPE_API_KEY，图像功能不可用（语音功能不受影响）")
        _vl = openai.OpenAI(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1", api_key=key)
    return _vl


def asr_client():
    """Whisper 语音转写——按需创建。"""
    global _asr
    if _asr is None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("未配置 OPENAI_API_KEY，语音转写不可用（图像功能不受影响）")
        _asr = openai.OpenAI(api_key=key)
    return _asr


def image_to_exercise(image_path):
    """看图生成'看图写话'练习题。"""
    with open(image_path, "rb") as f:
        img = base64.b64encode(f.read()).decode()
    r = vl_client().chat.completions.create(
        model="qwen-vl-plus",
        messages=[{"role": "user", "content": [
            {"type": "text", "text": "基于这张图出一道国际中文'看图写话'练习题，并附 3 条评分要点。"},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,%s" % img}},
        ]}],
    )
    return r.choices[0].message.content


def speech_to_text(audio_path):
    """Whisper 转写教学音频。"""
    with open(audio_path, "rb") as f:
        return asr_client().audio.transcriptions.create(model="whisper-1", file=f).text


if __name__ == "__main__":
    pic = weekpath.data_path("pic1.jpg")
    audio = weekpath.data_path("student_speech.mp3")

    if os.path.exists(pic):
        print("【看图写话】\n", image_to_exercise(pic))
    else:
        print("跳过图像：未找到 data/pic1.jpg（自行放入一张教学图片即可）")

    if os.path.exists(audio):
        text = speech_to_text(audio)
        print("【转写文本】\n", text)
        from llm import LLM
        print("【口语点评】\n", LLM().ask("请按口语流利度框架点评这段转写文本：\n" + text))
    else:
        print("跳过语音：未找到 data/student_speech.mp3")

# 隐私纪律：放入真实学生作文/录音/照片前必须脱敏并取得授权；
# data/private/ 已在 .gitignore 中排除，绝不提交进公开仓库。
