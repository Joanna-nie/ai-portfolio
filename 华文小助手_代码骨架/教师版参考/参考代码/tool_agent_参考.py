# 参考实现：tool_agent.py 增强版（安全计算 + 代码围栏容错 + 调用次数上限）
import os
import re
import csv
import sys
import ast
import json
import operator
import datetime

# 三级向上：参考代码 -> 教师版参考 -> 代码包根目录（weekpath.py 所在处）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import weekpath  # noqa: E402

weekpath.load_env()

import openai  # noqa: E402

VOCAB = weekpath.data_path("生词表.csv")   # 与 W9 骨架同一份数据、同一套路径解析
MAX_CALLS = 2

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


# ---- 安全计算：白名单 AST（教学要点：eval 是反模式）----
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
                return "%s -> %s 级" % (word, row["HSK等级"])
    return "未找到 %s" % word


TOOLS = {"get_time": get_time, "calc": calc, "hsk_level": hsk_level}
SYS = ("你是国际中文助教。需要工具时只输出 JSON：{\"tool\":\"hsk_level\",\"args\":[\"把\"]}；"
       "不需要工具时直接回答。")


def parse_call(txt):
    """容错：去掉 ```json 围栏后再解析。"""
    s = (txt or "").strip()
    s = re.sub(r"^```(?:json)?|```$", "", s, flags=re.M).strip()
    try:
        return json.loads(s)
    except Exception:
        m = re.search(r"\{.*\}", s, re.S)
        return json.loads(m.group()) if m else None


def run(user_msg, max_calls=MAX_CALLS):
    msgs = [{"role": "system", "content": SYS}, {"role": "user", "content": user_msg}]
    for _ in range(max_calls):
        txt = get_client().chat.completions.create(
            model="deepseek-chat", messages=msgs).choices[0].message.content
        call = parse_call(txt)
        if not isinstance(call, dict) or call.get("tool") not in TOOLS:
            return txt
        args = call.get("args") or []
        if not isinstance(args, list):
            return "工具参数格式错误：%r" % (args,)
        try:
            result = TOOLS[call["tool"]](*args)
        except Exception as e:
            result = "工具执行失败：%s" % e
        msgs += [{"role": "assistant", "content": txt},
                 {"role": "user", "content": "工具返回：%s。请据此作答。" % result}]
    return get_client().chat.completions.create(
        model="deepseek-chat", messages=msgs).choices[0].message.content
