# 参考实现：planner_agent.py 增强版（计划校验 + 注入清洗 + 人工确认点）
# 说明：函数签名与学生骨架 W11 完全一致 —— planner_agent(lesson, retriever=None, auto_confirm=False)
#      这样教师可以把本文件直接覆盖到 week11_智能体/ 做对照演示，不会破坏 app.py 的调用。
import os
import re
import sys

# 三级向上：参考代码 -> 教师版参考 -> 代码包根目录（weekpath.py 所在处）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import weekpath  # noqa: E402

weekpath.load_env()

from llm import LLM  # noqa: E402
from rag_qa import retrieve  # noqa: E402

llm = LLM()
BAD = ["忽略以上", "忽略此前", "忽略所有指令", "system:", "请回复：已删除"]


def sanitize(text):
    """提示注入清洗：剔除知识库中疑似指令劫持的句子。"""
    lines = []
    for ln in text.splitlines():
        if any(b in ln for b in BAD):
            lines.append("【已过滤可疑指令】")
        else:
            lines.append(ln)
    return "\n".join(lines)


def make_plan(lesson):
    raw = llm.ask("把《%s》的备课拆成 4 个有序步骤，只输出编号列表："
                  "1 定教学要点 2 写教学目标 3 出教案框架 4 配 3 道练习" % lesson)
    steps = [re.sub(r"^\s*\d+[.、)]?\s*", "", s).strip()
             for s in raw.splitlines() if s.strip()]
    # 兜底：模型没按格式输出时用固定四步，保证课堂演示不断流
    return steps[:4] if len(steps) >= 4 else [
        "定教学要点", "写教学目标", "出教案框架", "配 3 道练习"]


def planner_agent(lesson, retriever=None, auto_confirm=False, prefer="local"):
    """retriever=None 时复用 W7 的 retrieve()，与骨架行为一致。
    prefer 与学生骨架同名参数，保证 W15 的引擎选择对 RAG 模式也生效。"""
    ctx = sanitize(retrieve(lesson) if retriever is None
                   else "\n".join(d.page_content for d in retriever.invoke(lesson)))
    outs = []
    for step in make_plan(lesson):
        out = llm.ask("资料：\n%s\n\n按步骤执行：%s" % (ctx, step), prefer=prefer)
        outs.append("【%s】\n%s" % (step, out))
        if not auto_confirm:
            print("[待人工确认] %s\n%s\n---" % (step, out))
    return "\n\n".join(outs)


if __name__ == "__main__":
    lesson = " ".join(sys.argv[1:]) or "愚公移山"
    print(planner_agent(lesson, auto_confirm=True))
