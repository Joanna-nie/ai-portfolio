# 官方 RAG 流水线 ↔ 我的 rag_qa.py 5行映射表

| 官方流水线 | llm-universe 对应章节 | 我的 rag_qa.py / assistant_v1.py |
| :--- | :--- | :--- |
| 加载与分块 | C3 数据处理：读取清洗切片 | `TextLoader` + `RecursiveCharacterTextSplitter(500/50)` |
| 向量化入库 | C3 词向量及向量库 | `OllamaEmbeddings(nomic-embed-text)` + `Chroma` 持久化 |
| 检索 | C4 搭建检索问答链 | `retrieve()` 取 top-k；`use_rag=True` 时先查资料 |
| 拼词与生成 | C4 将 LLM 接入 | `build_prompt()` 拼资料与问题，交 `LLM().ask()` |
| 部署与评估 | C4 Streamlit部署; C5 评估 | W7 幻觉对照表是最朴素评估；W15 用 Streamlit 发布 |