# W7 RAG 学科知识库问答器
# 依赖：pip install langchain langchain-community langchain-chroma langchain-ollama chromadb
# 准备：ollama pull nomic-embed-text
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import weekpath  # noqa: E402  数据路径 + 加载 .env

weekpath.load_env()

from langchain_community.document_loaders import TextLoader  # noqa: E402
from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: E402
from langchain_ollama import OllamaEmbeddings  # noqa: E402
from langchain_chroma import Chroma  # noqa: E402

CORPUS = weekpath.data_path("等级标准节选.txt")      # 不再依赖当前工作目录
PERSIST = weekpath.root_path("chroma_db")            # .gitignore 已排除

_retriever = None


def get_retriever(k=3, rebuild=False):
    """延迟构建：import 本模块不会触发 embedding 计算，
    只有真正检索时才建库；已存在 chroma_db 则直接复用。"""
    global _retriever
    if _retriever is not None and not rebuild:
        return _retriever
    emb = OllamaEmbeddings(model="nomic-embed-text")   # 本地嵌入，数据不出本机
    if not rebuild and os.path.exists(PERSIST) and os.listdir(PERSIST):
        vs = Chroma(persist_directory=PERSIST, embedding_function=emb)
    else:
        docs = TextLoader(CORPUS, encoding="utf-8").load()
        splits = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=50).split_documents(docs)
        vs = Chroma.from_documents(splits, emb, persist_directory=PERSIST)
    _retriever = vs.as_retriever(search_kwargs={"k": k})
    return _retriever


def retrieve(question):
    return "\n".join(d.page_content for d in get_retriever().invoke(question))


def build_prompt(question, ctx):
    return ("根据以下资料回答问题，资料中没有的内容就如实说“资料中未提及”：\n"
            "%s\n\n问题：%s" % (ctx, question))


if __name__ == "__main__":
    from llm import LLM          # week06 的模块，靠 weekpath 才能 import 到

    llm = LLM()
    q = " ".join(sys.argv[1:]) or "HSK4 要求掌握哪些语法点？"
    ctx = retrieve(q)
    print("【检索片段】\n", ctx[:300], "\n---")
    # 隐私任务用 prefer="local"；复杂任务用 prefer="api"
    print(llm.ask(build_prompt(q, ctx), prefer="local"))
