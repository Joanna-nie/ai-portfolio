# 参考实现：llm.py 增强版（多轮对话 + 费用估算 + 重试 + 按需建客户端）
# 说明：与 W6 学生骨架 llm.py 的对外接口一致（LLM().ask(prompt, prefer=...)），
#      额外提供 history / retries / spent，仅供教师讲评或答疑演示使用。
import os
import sys
import time

# 三级向上：参考代码 -> 教师版参考 -> 代码包根目录（weekpath.py 所在处）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import weekpath  # noqa: E402

weekpath.load_env()

import requests  # noqa: E402
import openai  # noqa: E402


class LocalEngine:
    def __init__(self, model=None):
        self.model = model or os.getenv("LOCAL_MODEL", "qwen2.5:0.5b")

    def ask(self, prompt, history=None, temperature=0.7, max_tokens=800):
        msgs = list(history or []) + [{"role": "user", "content": prompt}]
        r = requests.post("http://localhost:11434/api/chat", json={
            "model": self.model, "messages": msgs,
            "options": {"temperature": temperature, "num_predict": max_tokens},
            "stream": False}, timeout=60)
        r.raise_for_status()
        return r.json()["message"]["content"]


class APIEngine:
    def __init__(self, base_url=None, model=None):
        self.base_url = base_url or "https://api.deepseek.com/v1"
        self.model = model or "deepseek-chat"
        self.spent = 0.0
        self._client = None

    def _get_client(self):
        """按需创建：缺密钥时不在此处崩溃，保证纯本地模式仍可用。"""
        if self._client is None:
            key = os.getenv("DEEPSEEK_API_KEY")
            if not key:
                raise RuntimeError("未配置 DEEPSEEK_API_KEY（纯本地模式请 prefer='local'）")
            self._client = openai.OpenAI(base_url=self.base_url, api_key=key)
        return self._client

    def ask(self, prompt, history=None, temperature=0.7, max_tokens=800, retries=2):
        msgs = list(history or []) + [{"role": "user", "content": prompt}]
        for i in range(retries + 1):
            try:
                r = self._get_client().chat.completions.create(
                    model=self.model, messages=msgs,
                    temperature=temperature, max_tokens=max_tokens)
                u = getattr(r, "usage", None)
                if u:
                    # 单价以官方公告为准，此处仅示意量级
                    self.spent += (u.prompt_tokens / 1e6 * 2) + (u.completion_tokens / 1e6 * 8)
                return r.choices[0].message.content
            except Exception:
                if i == retries:
                    raise
                time.sleep(1.5 ** i)


class LLM:
    """双向自动切换：prefer='local' 本地挂→切云端；prefer='api' 云端挂→切本地。"""

    def __init__(self, local_model=None):
        self.local, self.api = LocalEngine(local_model), APIEngine()

    def ask(self, prompt, history=None, prefer="local", **kw):
        if prefer == "local":
            first, second, tag = self.local, self.api, "本地失败，切换云端"
        else:
            first, second, tag = self.api, self.local, "云端失败，切换本地"
        try:
            return first.ask(prompt, history, **kw)
        except Exception as e:
            print("[%s] %s" % (tag, e))
            return second.ask(prompt, history, **kw)
