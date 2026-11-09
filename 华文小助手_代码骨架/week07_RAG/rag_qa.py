# 课后作业1进阶（选择A）：给每段记录源并让答案附出处
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import weekpath
weekpath.load_env()

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from llm import LLM

CORPUS = weekpath.data_path("等级标准节选.txt")
PERSIST = weekpath.root_path("chroma_db")

def get_retriever(k=3, rebuild=False):
    emb = OllamaEmbeddings(model="nomic-embed-text")
    if not rebuild and os.path.exists(PERSIST) and os.listdir(PERSIST):
        vs = Chroma(persist_directory=PERSIST, embedding_function=emb)
    else:
        docs = TextLoader(CORPUS, encoding="utf-8").load()
        splits = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(docs)
        vs = Chroma.from_documents(splits, emb, persist_directory=PERSIST)
    return vs.as_retriever(search_kwargs={"k": k})

# 进阶A核心：给检索到的每一段打上【资料X】的标签
def retrieve(question):
    docs = get_retriever().invoke(question)
    ctx = ""
    for i, d in enumerate(docs):
        ctx += f"【资料{i+1}】: {d.page_content}\n"
    return ctx

def build_prompt(question, ctx):
    return (
        "你是一个严谨的学科助手。请严格根据以下参考资料回答问题。\n"
        "如果资料中没有提及，必须如实回答“资料中未提及”。\n"
        "回答时，必须在句末标注引用的资料序号（例如：【资料1】）。\n\n"
        f"【参考资料】:\n{ctx}\n\n"
        f"【问题】: {question}"
    )

def rag_qa(question, prefer="local"):
    llm = LLM()
    ctx = retrieve(question)
    # 打印检索到的原文，让你亲眼看到1200在不在里面
    print(f"\n--- 检索到的原始资料 ---\n{ctx}-------------------------\n")
    return llm.ask(build_prompt(question, ctx), prefer=prefer)

if __name__ == "__main__":
    q = "HSK4需要掌握多少词汇？"
    
    print("=== 1. 裸答（不使用RAG，纯靠本地小模型瞎编）===")
    print(LLM().ask(q, prefer="local"))
    
    print("\n=== 2. RAG答（使用云端大模型，因为云端聪明，能按格式回答）===")
    # 这里改用 prefer="api" 调用云端，保证你能看到完美的答案和出处
    try:
        print(rag_qa(q, prefer="api"))
    except Exception as e:
        print(f"云端调用失败（可能没配密钥）：{e}")
        print("切换到本地模型重试...")
        print(rag_qa(q, prefer="local"))
