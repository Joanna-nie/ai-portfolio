import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import weekpath 
import pandas as pd
import pandas as pd

def generate_fill_in_the_blank():
    # 1. 读取数据
    df = pd.read_csv(weekpath.data_path('生词表.csv'), encoding='utf-8')
    
    # 2. 筛选HSK4的词汇
    hsk4_words = df[df['HSK等级'] == 4]['词汇'].tolist()
    
    # 3. 生成填空题
    output_lines = []
    for word in hsk4_words:
        output_lines.append(f"用 ______ 造一个句子。（填空题）")
        
    # 4. 保存结果
        # 输出到代码包根目录，也就是和练习.txt一样的位置
    with open(os.path.join(weekpath.root_path(), '练习2.txt'), 'w', encoding='utf-8') as f:
        for line in output_lines:
            f.write(line + '\n')
            
    print(f"生成完成！共生成 {len(output_lines)} 道填空题。")

if __name__ == "__main__":
    generate_fill_in_the_blank()