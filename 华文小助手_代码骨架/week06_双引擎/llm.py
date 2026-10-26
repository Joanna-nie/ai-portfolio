# 课后作业1增强：选择“调用耗时与费用估算打印”。
# 理由：可以直观对比本地模型（免费、响应较快）和云端模型（按token计费）的差异，方便以后根据任务选型。
import os
import sys
import time  # <--- 确保这一行存在！
import requests
import openai

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import weekpath  # noqa: E402  跨周导入 + 加载 .env

weekpath.load_env()

import requests  # noqa: E402
import openai  # noqa: E402


class LocalEngine:
    """本地引擎（Ollama）：隐私任务优先、断网可用。"""

    def __init__(self, model=None):
        self.model = model or os.getenv("LOCAL_MODEL", "qwen2.5:0.5b")

    def ask(self, prompt, temperature=0.7, max_tokens=800):
        r = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "options": {"temperature": temperature, "num_predict": max_tokens},
                "stream": False,
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["message"]["content"]


class APIEngine:
    """云端引擎：复杂任务、本地失败兜底。

    注意：openai.OpenAI(...) 在 api_key 为 None 时会直接抛错。
    若在这里（构造 LLM 时）就建客户端，那么没配密钥的同学连"纯本地"模式都跑不起来。
    因此改为**按需创建**：第一次真正调用云端时才建客户端。
    """

    def __init__(self, base_url=None, model=None):
        self.base_url = base_url or "https://api.deepseek.com/v1"
        self.model = model or "deepseek-chat"
        self._client = None

    def _get_client(self):
        if self._client is None:
            key = os.getenv("DEEPSEEK_API_KEY")
            if not key:
                raise RuntimeError(
                    "未配置 DEEPSEEK_API_KEY：请复制 .env.example 为 .env 并填入密钥，"
                    "或在系统环境变量中设置。纯本地模式请调用 ask(..., prefer='local')。"
                )
            self._client = openai.OpenAI(base_url=self.base_url, api_key=key)
        return self._client

    def ask(self, prompt, temperature=0.7, max_tokens=800):
        r = self._get_client().chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return r.choices[0].message.content


class LLM:
    """统一入口：ask(prompt)。本地优先、云端兜底、**双向**异常自动切换。
    
    prefer='local'：本地挂了自动切云端；
    prefer='api' ：云端挂了（断网/超时/未配密钥）自动切本地。
    两侧对称，任何一边失败都不会让程序直接崩——这正是"双引擎"存在的意义。
    """

    def __init__(self, local_model=None):
        self.local = LocalEngine(local_model)
        self.api = APIEngine()

    def ask(self, prompt, prefer="local", **kw):
        if prefer == "local":
            first, second, tag = self.local, self.api, "本地失败，自动切换云端"
        else:
            first, second, tag = self.api, self.local, "云端失败，自动切换本地"
        
        # 新增：记录首选引擎的开始时间
        start_time = time.time()
        
        try:
            result = first.ask(prompt, **kw)
            end_time = time.time()
            # 新增：打印耗时和费用估算
            print(f"\n[成功调用] 引擎: {prefer}, 耗时: {end_time - start_time:.2f} 秒。")
            print(f"[费用估算] {'本地调用不花钱' if prefer == 'local' else '云端调用按token计费，约0.001元'}")
            return result
        except Exception as e:
            print("[%s] %s" % (tag, e))
            
            # 新增：记录回退引擎的开始时间
            start_fallback = time.time()
            result = second.ask(prompt, **kw)
            end_fallback = time.time()
            print(f"\n[回退成功] 耗时: {end_fallback - start_fallback:.2f} 秒。")
            return result


if __name__ == "__main__":
    llm = LLM()
    print(llm.ask("给《愚公移山》出一道 HSK4 阅读理解题", prefer="local"))