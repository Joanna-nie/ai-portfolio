# 参考实现：rag_qa.py 增强版（来源标注 + 可调 top_k + 持久化复用）
# 说明：路径与 W7 学生骨架保持一致（都用 weekpath.data_path），避免教师本地
#      与学生本地行为不一致的"玄学 bug"。
import os
import sys

# 三级向上：参考代码 -> 教师版参考 -> 代码包根目录（weekpath.py 所在处）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import weekpath  # noqa: E402

weekpath.load_env()

from langchain_community.document_loaders import TextLoader  # noqa: E402
from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: E402
from langchain_ollama import OllamaEmbeddings  # noqa: E402
from langchain_chroma import Chroma  # noqa: E402

CORPUS = weekpath.data_path("等级标准节选.txt")
PERSIST = weekpath.root_path("chroma_db")


def build_or_load(chunk=500, overlap=50, k=3, rebuild=False):
    emb = OllamaEmbeddings(model="nomic-embed-text")
    if not rebuild and os.path.exists(PERSIST) and os.listdir(PERSIST):
        vs = Chroma(persist_directory=PERSIST, embedding_function=emb)
    else:
        docs = TextLoader(CORPUS, encoding="utf-8").load()
        sp = RecursiveCharacterTextSplitter(chunk_size=chunk, chunk_overlap=overlap)
        vs = Chroma.from_documents(sp.split_documents(docs), emb, persist_directory=PERSIST)
    return vs.as_retriever(search_kwargs={"k": k})


def retrieve(question, retriever=None):
    """与学生骨架同名同签名，可直接替换对照。"""
    retriever = retriever or build_or_load()
    return "\n".join(d.page_content for d in retriever.invoke(question))


def rag_qa(question, llm, retriever=None, prefer="local"):
    retriever = retriever or build_or_load()
    docs = retriever.invoke(question)
    if not docs:
        ctx, src = "（未检索到相关资料）", "无"
    else:
        ctx = "\n".join(d.page_content for d in docs)
        src = "；".join(sorted({os.path.basename(d.metadata.get("source", "?")) for d in docs}))
    prompt = ("严格依据以下资料回答，资料未涵盖的内容请回答“资料中未提及”，"
              "并在末尾注明依据来源。\n资料：\n%s\n\n问题：%s" % (ctx, question))
    ans = llm.ask(prompt, prefer=prefer)
    return ans, src
