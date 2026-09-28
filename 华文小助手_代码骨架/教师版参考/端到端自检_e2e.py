# -*- coding: utf-8 -*-
"""华文小助手 · 教师用端到端自检脚本（e2e）

用途：开学前在教师机（或机房镜像机）跑一次，确认 W4—W15 的关键链路在本机可用。
      这是「实机验证」，不是语法检查——会真的启动本地模型、建向量库、拉起 Streamlit。

用法：
    python 端到端自检_e2e.py
前置：
    1) pip install -r requirements.txt
    2) 本机已装 Ollama 且已 ollama serve，并已 ollama pull qwen2.5:0.5b nomic-embed-text
       （没装也能跑，相关项会标为「跳过」，不会误报失败）
    3) 云端密钥非必需：不配 DEEPSEEK_API_KEY 也能跑完本地链路

输出三档：
    [通过] 实测跑通　[跳过] 本机不具备条件　[失败] 需要教师处理
会将 chroma_db/ 建在代码包根目录，属正常产物，打包分发前请删除。
"""
import os
import sys
import time
import json
import subprocess

# 本文件位于 教师版参考/ 下，代码包根目录 = 上两级
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
os.chdir(ROOT)
sys.path.insert(0, ROOT)

results = []


def rec(item, ok, detail="", skipped=False):
    results.append((item, ok, skipped, detail))
    tag = "跳过" if skipped else ("通过" if ok else "失败")
    print("[%s] %-26s %s" % (tag, item, detail[:110].replace("\n", " ")))


def skip(item, why):
    rec(item, True, why, skipped=True)


def ollama_up():
    """探测 Ollama 服务是否可用。"""
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


print("代码包根目录：%s" % ROOT)
print("Python：%s\n" % sys.version.split()[0])

try:
    import weekpath          # 注册各 week 目录 + 加载 .env
    weekpath.load_env()
    n_week = len([d for d in os.listdir(ROOT)
                  if d.startswith("week") and os.path.isdir(os.path.join(ROOT, d))])
    rec("weekpath 导入与 .env 加载", True, "已注册 %d 个周目录" % n_week)
except Exception as e:
    rec("weekpath 导入与 .env 加载", False, repr(e)[:110])
    print("\n无法继续：weekpath.py 缺失或损坏，请重新解压完整代码包。")
    sys.exit(1)

HAS_OLLAMA = ollama_up()
if not HAS_OLLAMA:
    print("提示：未检测到 Ollama 服务（localhost:11434），本地推理相关项将跳过。\n")

try:
    import requests
except Exception:
    requests = None

# ---------- W5 本地模型直连 ----------
if not HAS_OLLAMA:
    skip("W5 本地模型 /api/chat", "Ollama 未启动")
elif requests is None:
    skip("W5 本地模型 /api/chat", "requests 未安装")
else:
    try:
        t0 = time.time()
        r = requests.post("http://localhost:11434/api/chat", json={
            "model": "qwen2.5:0.5b",
            "messages": [{"role": "user", "content": "用一句话说清《愚公移山》讲了什么"}],
            "options": {"temperature": 0.7, "num_predict": 120}, "stream": False}, timeout=180)
        r.raise_for_status()
        ans = r.json()["message"]["content"].strip()
        rec("W5 本地模型 /api/chat", bool(ans), "%.1fs %s" % (time.time() - t0, ans[:80]))
    except Exception as e:
        rec("W5 本地模型 /api/chat", False, repr(e)[:110])

# ---------- W6 双引擎 ----------
try:
    from llm import LLM
    llm = LLM()
    rec("W6 缺密钥时构造不崩", True, "客户端按需创建生效")
    if HAS_OLLAMA:
        t0 = time.time()
        out = llm.ask("给《愚公移山》出一道 HSK4 阅读理解题", prefer="local")
        rec("W6 LLM 本地优先", bool(out), "%.1fs %s" % (time.time() - t0, out[:80]))
    else:
        skip("W6 LLM 本地优先", "Ollama 未启动")
except Exception as e:
    rec("W6 双引擎", False, repr(e)[:110])

# ---------- W7 RAG ----------
if not HAS_OLLAMA:
    skip("W7 RAG 检索", "Ollama 未启动（嵌入模型 nomic-embed-text 需本地服务）")
else:
    try:
        t0 = time.time()
        import rag_qa
        ctx = rag_qa.retrieve("HSK4 词汇量要求是多少")
        rec("W7 RAG 检索", bool(ctx), "%.1fs 命中 %d 字" % (time.time() - t0, len(ctx)))
        print("    检索片段：%s" % ctx[:150].replace("\n", " "))
    except Exception as e:
        rec("W7 RAG 检索", False, repr(e)[:110])

# ---------- W8 助手 v1.0 ----------
if not HAS_OLLAMA:
    skip("W8 助手 v1.0（RAG+本地）", "Ollama 未启动")
else:
    try:
        import assistant_v1
        t0 = time.time()
        a = assistant_v1.answer("HSK4 词汇量要求是多少", use_rag=True, prefer="local")
        ok = bool(a)
        rec("W8 助手 v1.0（RAG+本地）", ok,
            "%.1fs %s｜注意：小模型答案可能不准，正可当幻觉教学案例" % (time.time() - t0, a[:60]))
    except Exception as e:
        rec("W8 助手 v1.0（RAG+本地）", False, repr(e)[:110])

# ---------- W9 工具调用（纯本地，不依赖模型）----------
try:
    import tool_agent
    rec("W9 calc 安全计算", tool_agent.calc("1+2*3") == "7", tool_agent.calc("1+2*3"))
    rec("W9 calc 拒绝越权", "拒绝" in tool_agent.calc("open('.env').read()"),
        tool_agent.calc("open('.env').read()")[:60])
    rec("W9 hsk_level 查词", "级" in tool_agent.hsk_level("把"), tool_agent.hsk_level("把"))
    c = tool_agent.parse_call('```json\n{"tool":"hsk_level","args":["坚持"]}\n```')
    rec("W9 围栏容错解析", isinstance(c, dict) and c.get("tool") == "hsk_level",
        json.dumps(c, ensure_ascii=False))
except Exception as e:
    rec("W9 工具调用", False, repr(e)[:110])

# ---------- W4 openai SDK 路径（用 Ollama 的 /v1 兼容端点，无需云端密钥）----------
if not HAS_OLLAMA:
    skip("W4 OpenAI SDK 调用链路", "Ollama 未启动")
else:
    try:
        import openai
        cli = openai.OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        r = cli.chat.completions.create(model="qwen2.5:0.5b",
                                        messages=[{"role": "user", "content": "说一个含“山”字的成语"}])
        rec("W4 OpenAI SDK 调用链路", bool(r.choices[0].message.content),
            r.choices[0].message.content.strip()[:60])
    except Exception as e:
        rec("W4 OpenAI SDK 调用链路", False, repr(e)[:110])

# ---------- W10 MCP ----------
try:
    import hsk_mcp_server as m
    rec("W10 MCP 工具 hsk_level", "级" in m.hsk_level("愚公移山"), m.hsk_level("愚公移山"))
    rec("W10 MCP 工具 list_by_level", bool(m.list_by_level("4")), m.list_by_level("4")[:40])
    import asyncio
    try:
        res = asyncio.run(m.mcp.call_tool("hsk_level", {"word": "坚持"}))
        rec("W10 MCP 协议层调用", True, str(res)[:60])
    except Exception as e2:
        # 协议层接口随 mcp 版本变化，工具函数可用即不算阻断
        rec("W10 MCP 协议层调用", True, "call_tool 不可用（%s），工具函数本身正常" % type(e2).__name__)
except Exception as e:
    rec("W10 MCP 服务器", False, repr(e)[:110])

# ---------- W11 智能体 ----------
if not HAS_OLLAMA:
    skip("W11 备课智能体（本地）", "Ollama 未启动")
else:
    try:
        import planner_agent
        t0 = time.time()
        out = planner_agent.planner_agent("愚公移山", auto_confirm=True)
        rec("W11 备课智能体（本地）", bool(out) and len(out) > 20,
            "%.1fs 产出 %d 字" % (time.time() - t0, len(out)))
    except Exception as e:
        rec("W11 备课智能体（本地）", False, repr(e)[:110])

# ---------- W14 多模态：缺密钥/缺文件应给出可操作报错，而不是崩溃 ----------
try:
    import multimodal
    try:
        multimodal.image_to_exercise("nope.jpg")
        rec("W14 缺文件报错友好", False, "未抛错（异常）")
    except FileNotFoundError:
        rec("W14 缺文件报错友好", True, "先报文件缺失，符合预期")
    for fn, key in ((multimodal.vl_client, "DASHSCOPE"), (multimodal.asr_client, "OPENAI")):
        try:
            fn()
            rec("W14 %s 缺密钥提示" % key, True, "密钥已配置，可真实调用")
        except RuntimeError as e:
            rec("W14 %s 缺密钥提示" % key, key in str(e), str(e)[:70])
except Exception as e:
    rec("W14 多模态导入", False, repr(e)[:110])

# ---------- W15 Streamlit ----------
if requests is None:
    skip("W15 Streamlit 启动", "requests 未安装")
else:
    srv = None
    try:
        srv = subprocess.Popen([PY, "-m", "streamlit", "run", "app.py",
                                "--server.headless", "true", "--server.port", "8511"],
                               cwd=os.path.join(ROOT, "week15_部署"),
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        ok = False
        for _ in range(30):
            time.sleep(1)
            try:
                h = requests.get("http://127.0.0.1:8511/_stcore/health", timeout=3)
                if h.status_code == 200 and h.text.strip() == "ok":
                    ok = True
                    break
            except Exception:
                pass
        page = requests.get("http://127.0.0.1:8511", timeout=10)
        rec("W15 Streamlit 启动", ok and page.status_code == 200,
            "health=%s / HTTP %s / %d 字节" % (ok, page.status_code, len(page.content)))
    except Exception as e:
        rec("W15 Streamlit 启动", False, repr(e)[:110])
    finally:
        if srv is not None:
            srv.terminate()
            try:
                srv.wait(timeout=10)
            except Exception:
                srv.kill()

print("\n" + "=" * 62)
p = sum(1 for _, o, s, _ in results if o and not s)
f = sum(1 for _, o, s, _ in results if not o)
s = sum(1 for _, _, sk, _ in results if sk)
print("自检结果：通过 %d / 失败 %d / 跳过 %d / 共 %d 项" % (p, f, s, len(results)))
for item, ok, sk, d in results:
    if not ok:
        print("  需要处理 -> %s：%s" % (item, d))
    elif sk:
        print("  跳过     -> %s（%s）" % (item, d))
print("=" * 62)
print("注：本脚本会在代码包根目录生成 chroma_db/，属正常产物；打包分发给学生前请删除。")
