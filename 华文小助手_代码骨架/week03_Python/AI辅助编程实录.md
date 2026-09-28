# AI辅助编程实录

## 1. 任务与提示词
**要做什么：** 读生词表CSV → 筛HSK4 → 造练习题
**我写的提示词：** 
请帮我写一个Python脚本，读取 `data/生词表.csv` 文件，筛选出HSK等级为4的词汇，然后生成一份填空题（把目标词挖空成 ______ ），保存为 `练习2.txt`。

## 2. AI 初版代码
（以下为 AI 第一次给出的完整代码，未修改）
```python
import pandas as pd

def generate_fill_in_the_blank():
    # 1. 读取数据
    df = pd.read_csv('data/生词表.csv')
    
    # 2. 筛选HSK4的词汇
    hsk4_words = df[df['HSK Level'] == 4]['词语'].tolist()
    
    # 3. 生成填空题
    output_lines = []
    for word in hsk4_words:
        output_lines.append(f"用 ______ 造一个句子。（填空题）")
        
    # 4. 保存结果
    with open('练习2.txt', 'w') as f:
        for line in output_lines:
            f.write(line + '\n')
            
    print(f"生成完成！共生成 {len(output_lines)} 道填空题。")

if __name__ == "__main__":
    generate_fill_in_the_blank()
```

## 3.我的修改点
 ① 修改了读取路径，并加上了编码。
AI 默认写的相对路径 'data/生词表.csv' 在我的电脑上引发了 FileNotFoundError。我根据项目要求，改成了项目自带的 weekpath.data_path('生词表.csv')，并加上了 encoding='utf-8'，防止读取或写入时出现中文乱码。

 ② 修改了列名（HSK Level）。
AI 默认猜测我的表头是英文的 HSK Level，但真实的数据表（生词表.csv）中用的是中文表头 HSK等级。如果不修改，会引发 KeyError 报错，无法筛选数据。

 ③ 修改了列名（词语）。
 同样是因为 AI 对数据结构不熟悉，它写了 词语，但我实际 CSV 表头里叫 词汇，必须改成 df['HSK等级'] == 4]['词汇'] 才能正确提取词汇列表。

 ④ 修改了输出路径及拼接方式。
 AI 默认把文件生成在当前运行目录，我改成了 weekpath.root_path() 以便统一输出到代码包根目录。但最初尝试用 / 拼接时遇到了 TypeError（字符串不支持除法），后来查阅资料改用 os.path.join(weekpath.root_path(), '练习2.txt') 成功解决。

 ⑤ 加入了项目路径注册代码。
 为了在 week03_Python 目录里也能成功 import weekpath，我在文件开头加了 sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))，确保跨目录运行时模块能被正确找到。

 ⑥ 利用列表推导式和 f.writelines() 优化了文件写入。
 为什么：读了官方教程列表一节后，我把原代码中 for w in words: 逐行 f.write 的循环，改成了 lines = [...] 的列表推导式，配合 f.writelines(lines) 一次性写入。代码从 4 行缩减到 2 行，逻辑更直观，也符合 Pythonic 的写法。

## 4.最终版 vs 初版差异说明
AI 初版没有处理 CSV 编码，会导致中文报错，我加上了 encoding='utf-8'。

AI 把路径写死了，没有考虑项目的跨目录结构，我用 weekpath 工具替代了相对路径。

AI 瞎猜了数据列名（英文），我根据实际数据文件对齐了真实的中文列名。

AI 用 / 拼接字符串导致报错，我改成了更稳妥的 os.path.join()。