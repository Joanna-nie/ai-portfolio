# W15 Streamlit 部署入口
# 依赖：pip install streamlit python-dotenv
# 运行：streamlit run app.py            -> http://localhost:8501
# 端口占用：streamlit run app.py --server.port 8502
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import weekpath  # noqa: E402  planner_agent 在 week11，靠它才能 import 到

weekpath.load_env()

import streamlit as st  # noqa: E402

st.set_page_config(page_title="华文小助手", page_icon="\U0001F4DA")
st.title("华文小助手 · 国际中文备课 Agent")

lesson = st.text_input("输入课文名称", "愚公移山")
use_rag = st.checkbox("启用知识库（RAG）", value=True)
engine = st.radio("引擎", ["本地优先", "云端优先"], index=0)
auto_confirm = st.checkbox("自动执行（关闭则每步在终端等待确认）", value=True)

if st.button("生成备课方案"):
    prefer = "local" if engine == "本地优先" else "api"
    try:
        from planner_agent import planner_agent
        from llm import LLM

        if not use_rag:
            # 关掉 RAG 的对照演示：直接问模型，用于课堂上做"幻觉对比"
            out = LLM().ask("请为《%s》写一份备课方案。" % lesson, prefer=prefer)
        else:
            with st.spinner("检索知识库并规划中..."):
                # prefer 必须透传，否则"云端优先"在 RAG 模式下会被忽略（v3 遗留缺陷）
                out = planner_agent(lesson, auto_confirm=auto_confirm, prefer=prefer)
        st.markdown(out)
    except Exception as e:
        st.error("运行失败：%s" % e)
        st.info("常见原因：本地 Ollama 未启动 / 未 ollama pull nomic-embed-text / "
                "API 密钥未设置 / 依赖未安装。可在项目根目录运行 python setup_check.py 自检。")
