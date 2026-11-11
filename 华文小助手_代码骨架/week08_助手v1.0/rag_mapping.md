# 官方 RAG 流水线 ↔ 我的 rag_qa.py 5行映射表

| # | 官方流水线 | llm-universe对应章节 | 我自己的代码（第三列必须是真实函数/类名） |
| :--- | :--- | :--- | :--- |
| 1 | Load + Split | C3 数据处理：读取、清洗与切片 | `TextLoader` + `RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)`，读取 `等级标准节选.txt` |
| 2 | Embed + Store | C3 搭建并使用向量数据库 | `OllamaEmbeddings(model="nomic-embed-text")` + `Chroma(persist_directory=...)` 本地持久化 |
| 3 | Retrieve | C4 基于LangChain搭建检索问答链 | `retrieve(question)` 取 top-k；`use_rag=True` 时先查资料再答 |
| 4 | Prompt + Generate | C4 将LLM接入LangChain | `build_prompt(question, ctx)` 拼 `SYSTEM_HINT` + 检索片段 + 问题，交 `LLM().ask(prefer=...)` 生成 |
| 5 | Deploy + Evaluate | C4 Streamlit部署；C5 系统评估 | 评估用 W7 的 `hallucination_log.md`；W15 计划用 Streamlit 发布网页助手 |