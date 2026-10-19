# W9 手写最小工具调用循环（不用框架）
# 依赖：pip install openai python-dotenv
import os
import csv
import sys
import ast
import json
import re
import operator
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import weekpath  # noqa: E402  数据路径 + 加载 .env

weekpath.load_env()

import openai  # noqa: E402

VOCAB = weekpath.data_path("生词表.csv")

_client = None


def get_client():
    global _client
    if _client is None:
        key = os.getenv("DEEPSEEK_API_KEY")
        if not key:
            raise RuntimeError("未配置 DEEPSEEK_API_KEY，请先在 .env 中填写")
        _client = openai.OpenAI(base_url="https://api.deepseek.com/v1", api_key=key)
    return _client


def get_time():
    return str(datetime.datetime.now())


# ---- 安全计算：白名单 AST，绝不使用裸 eval ----
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("只允许数字与 + - * / ** % 运算")


def calc(expr):
    """教学演示用：只做四则运算。为什么不用 eval？
    因为 eval 会执行任意 Python 代码，是典型的安全反模式（本课程伦理红线之一）。"""
    try:
        return str(_eval_node(ast.parse(str(expr), mode="eval")))
    except ZeroDivisionError:
        return "错误：除数为 0"
    except Exception as e:
        return "拒绝计算：%s" % e


def hsk_level(word):
    with open(VOCAB, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["词汇"].strip() == str(word).strip():
                return "%s 是 %s 级" % (word, row["HSK等级"])
    return "未找到 %s" % word


TOOLS = {"get_time": get_time, "calc": calc, "hsk_level": hsk_level}

SYS = ("你是国际中文助教。如需查时间、计算、查 HSK 等级，请只输出 JSON："
       '{"tool": "hsk_level", "args": ["把"]}；无需工具时直接回答。')


def parse_call(txt):
    """容错解析：模型常输出 ```json 围栏或前后客套话，这里都剥掉。"""
    s = (txt or "").strip()
    s = s.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(s)
    except Exception:
        m = re.search(r"\{.*\}", s, re.S)  # re.S：跨行也能匹配到 JSON 块
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                return None
    return None


def run(user_msg, max_calls=2):
    msgs = [{"role": "system", "content": SYS}, {"role": "user", "content": user_msg}]
    for _ in range(max_calls):
        txt = get_client().chat.completions.create(
            model="deepseek-chat", messages=msgs).choices[0].message.content
        call = parse_call(txt)
        if not isinstance(call, dict) or call.get("tool") not in TOOLS:
            return txt                                   # 没调用工具 → 直接回答
        args = call.get("args") or []
        if not isinstance(args, list):
            return "工具参数格式错误：%r" % (args,)
        try:
            result = TOOLS[call["tool"]](*args)
        except Exception as e:
            result = "工具执行失败：%s" % e
        msgs += [{"role": "assistant", "content": txt},
                 {"role": "user", "content": "工具返回：%s。请据此作答。" % result}]
    # 达到上限后强制收口，避免无限循环烧 token
    return get_client().chat.completions.create(
        model="deepseek-chat", messages=msgs).choices[0].message.content


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "'把'字是 HSK 几级词汇？现在几点了？"
    print("用户输入：", q)
    print("助手：", run(q))
