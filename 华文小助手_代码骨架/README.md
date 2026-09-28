# 华文小助手 · 每周代码骨架（解压即用）

适用课程：407P1122《人工智能在学习环境中的应用与实践》（汉语国际教育，A 轨）
通识课 407G1014（B 轨）请把 data/ 下的学科数据换成自己的学科材料。

## 怎么用
1. 把整个文件夹解压到你的工作目录，建议重命名为 `ai-portfolio`（你的作品集仓库）。
2. 复制 `.env.example` 为 `.env`，填入你自己的 API 密钥（**绝不提交 .env**）。
3. 每周进对应目录，按该周 README 或直接运行当周文件。
4. 所有产物每周 `git add / commit / push`，16 周后仓库就是你的作品集。

## 依赖按周安装（不必一次装完）
- W1–W3：零第三方依赖
- W4：`pip install openai`
- W5–W6：`pip install ollama requests`
- W7–W8：`pip install langchain langchain-community langchain-chroma chromadb`
- W9–W10：`pip install "mcp[cli]"`
- W13：无（单文件 HTML，双击浏览器打开）
- W15：`pip install streamlit`

也可一次性安装：`pip install -r requirements.txt`

## 复核修订（v4，2026-09-19 二次复核）—— 修复 7 个遗留缺陷
上一轮只修了代码包本身，这轮把"代码包 + 生成脚本"一起复核，修掉会真实踩到的坑：

**代码包内**
1. **W15 的"云端优先"点了没用**：`planner_agent` 内部固定走 local，页面上的引擎单选
   在启用 RAG 时被忽略 → `planner_agent(..., prefer=...)` 增加透传参数，
   学生骨架与教师参考版**同步改名**，保持签名一致（app.py 不用改即可生效）。
2. **`setup_check.py` 自己不读 `.env`**：配好了 `.env` 却被自检报"未读到有效变量"（误报）
   → 检测前先 `load_dotenv()`，未装 python-dotenv 时退回只读系统变量。
3. **产物落在"当前目录"**：W3 的 `练习.txt`、W4 的 `chat_log.txt` 你从哪运行就生成在哪，
   与"任意目录运行"的承诺冲突，且散落的文件 `.gitignore` 拦不住 → 统一写代码包根目录。
4. **W9 用魔数 `16` 代替 `re.S`**：可读性差且易改错 → 改为 `re.S` 并在顶部 `import re`。

**生成脚本（build_*.py）**
5. **`build_master_doc_v3.py` 一跑就崩**：引用了不存在的 `工程实现路径_华文小助手_v3.docx`
   （v3 当年是"覆盖原文件"，磁盘上只有正式文件名）→ 改为真实文件名，已实跑通过。
6. **`build_code_pack.py` 无条件 `rmtree`**：单独重跑会把 `build_pack_extras.py` 增补的
   `教师版参考/` 一起抹掉 → 目录非空时拒绝覆盖，需显式 `python build_code_pack.py --force`。
7. **两份教学文档里的 W9 示例仍是裸 `eval`**：与代码包的安全红线不一致，
   且 `eval(expr, {"__builtins__": {}})` 能被 `__subclasses__()` 绕过（并不安全）
   → 改为白名单 AST，并重新生成了三份 docx。

## 复核修订（v3）—— 修复了 7 个真实缺陷
1. **跨周 import 失效**（最严重）：`llm.py` 在 week06、`rag_qa.py` 在 week07，
   但 W8/W11/W15 都要 `from llm import LLM`，直接跑会 `ModuleNotFoundError`。
   → 新增根目录 `weekpath.py`，把各 week 目录注册进 `sys.path`。
   每个脚本开头固定三行（照抄）：
   ```python
   import os, sys
   sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   import weekpath; weekpath.load_env()
   ```
   （`教师版参考/参考代码/` 下的文件深一层，用**三次** `os.path.dirname`。）
2. **Windows 读不到 `.env`**：`os.getenv()` 不会自动加载 `.env` 文件。
   → 新增 `python-dotenv` 依赖 + `weekpath.load_env()`，未安装时安全跳过。
3. **缺密钥时程序在 import 阶段就崩**：`openai.OpenAI(api_key=None)` 直接抛错，
   导致"只跑本地 Ollama"的同学也跑不起来 → 改为**按需创建客户端**。
4. **`eval()` 安全反模式**（W9 工具调用）→ 改为白名单 AST 安全四则运算，
   并在注释里点明"为什么不用 eval"，正好作为伦理教学素材。
5. **rag_qa 在 import 时就建向量库**（一导入就跑 embedding，慢且易报错）
   → 改为 `get_retriever()` 延迟构建 + 复用 `chroma_db/`。
6. **教师参考实现与学生骨架签名不一致**（`planner_agent` 参数不同，覆盖就坏）
   → 统一为 `planner_agent(lesson, retriever=None, auto_confirm=False)`。

7. **MCP 库升级导致 W10 必然报错**：实测 mcp 2.x 已把 `FastMCP` 改名为 `MCPServer`，
   旧写法 `from mcp.server.fastmcp import FastMCP` 直接 ImportError（学生按任何旧教程写都会踩）。
   → 骨架改为版本自适应，1.x / 2.x 都能跑，并给出可操作的安装提示。

其它小修：小游戏支持回车提交+防重复、参考 HTML 删掉一行会误建 AudioContext 的死代码、
`setup_check.py` 增加 `dotenv` 与代码包完整性检查、数据路径统一走 `weekpath.data_path()`。

## 实机验证（2026-09-19，非静态检查）
在真实环境跑通：Ollama 0.33.3 + qwen2.5:0.5b + nomic-embed-text，Python 3.13。
- W5 本地推理：首次含模型装载约 30s，热调用 **0.4–0.6s / 约 166 tokens/s**，机房节奏可接受
- W6 双引擎、W7 RAG（建库 32s，含嵌入模型装载）、W8 助手 v1.0：均返回正常结果
- W9 工具调用：安全计算正确、越权表达式被拒、```json 围栏容错解析通过
- W10 MCP：stdio 客户端真实握手成功，列出 hsk_level / list_by_level 并调用成功
- W15 Streamlit：`streamlit run app.py` 健康检查 ok，首页 HTTP 200
- W4/W9 的 openai SDK 路径：用 Ollama 的 OpenAI 兼容端点（/v1）跑通，无需云端密钥
- W14 图像/语音：需云端密钥，本机无密钥；已验证"缺密钥给出可操作提示、不崩溃"

## 新增（v2）
- `data/` 已替换为**真实材料**：《国际中文教育中文水平等级标准》(GF 0025—2021) 节选、
  《愚公移山》原文+白话+教学提示。数字类指标已核对官方文本，正式引用前请再核验。
- `setup_check.py` —— **环境自检脚本，双击即可运行**，一眼看到自己机器缺什么
  （Python/Git/Ollama/依赖包/.env/样例数据/内存/磁盘/网络），并给出处理建议。
  用法：双击本文件，或 `python setup_check.py`
- `教师版参考/` —— 教师专用（**勿提前发给学生**）：每周参考答案 + 增强版参考实现。


## 目录 × 周次对照
| 目录 | 周次 | 核心文件 |
|------|------|----------|
| week01_环境 | W1 | hello.py |
| week02_提示词 | W2 | prompt-library/（模板示例） |
| week03_Python | W3 | vocab_tool.py |
| week04_API | W4 | week4_api_bot.py |
| week05_本地部署 | W5 | ollama_notes.md |
| week06_双引擎 | W6 | llm.py |
| week07_RAG | W7 | rag_qa.py |
| week08_助手v1.0 | W8 | assistant_v1.py |
| week09_工具调用 | W9 | tool_agent.py |
| week10_MCP | W10 | hsk_mcp_server.py |
| week11_智能体 | W11 | planner_agent.py |
| week12_低代码 | W12 | system_prompt.md |
| week13_小游戏 | W13 | subject_game.html |
| week14_多模态 | W14 | multimodal.py |
| week15_部署 | W15 | app.py |
| week16_收官 | W16 | 项目报告模板.md |
| （根目录） | 全周 | `weekpath.py` 跨周导入/路径/`.env` 入口；`setup_check.py` 环境自检 |

## 运行约定（重要）
- **从哪个目录运行都行**：数据路径一律由 `weekpath.data_path()` 解析，不再依赖当前目录。
- **必须整体解压、不要拆散 week 目录**：跨周 import 依赖 `weekpath.py` 与各 week 目录同级。
- 若把单个 `.py` 拷到别处单独运行，需同时拷 `weekpath.py` 与 `data/`。

## 安全红线（每周必查）
- 密钥只存 `.env`，代码一律 `os.getenv("XXX_API_KEY")`
- `.env` 已在 `.gitignore` 中；提交前跑 `git status` 确认无 `.env`
- 绝不把密钥写进代码，也不截图含密钥的终端

注：API 域名、模型名与参数以各提供商官方文档为准。
