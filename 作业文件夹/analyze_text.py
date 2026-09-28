import nltk
import jieba
import jieba.posseg as pseg
from collections import Counter
import re
import string
import matplotlib.pyplot as plt
from collections import Counter

# 下载必要的NLTK数据包
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class ChineseTextAnalyzer:
    def __init__(self):
        # 中文停用词列表（常用）
        self.chinese_stopwords = set([
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这',
            '与', '及', '或', '但', '而', '且', '之', '其', '此', '那', '哪', '谁', '何', '几', '多', '少', '又', '再', '更', '最', '只', '才', '总', '曾', '经', '将', '要',
            '来', '去', '上', '下', '前', '后', '内', '外', '中', '间', '东', '西', '南', '北', '里', '年', '月', '日', '时', '分', '秒', '为', '把', '对', '向', '往', '朝',
            '从', '自', '由', '因', '于', '为', '与', '跟', '和', '同', '比', '被', '给', '让', '叫', '使', '请', '用', '拿', '以', '据', '按', '凭', '当', '打', '到', '得',
            '所', '着', '了', '过', '的', '地', '得', '等', '等等', '之', '乎', '者', '也', '呢', '吗', '嘛', '呀', '啊', '哇', '哦', '呃', '恩', '吧', '哈', '嘿', '喂', '哎'
        ])
        
        self.text = ""
        
    def analyze(self, text):
        """
        使用jieba分析输入的中文文本
        """
        if len(text) > 3000:
            raise ValueError("文本长度超过3000字限制")
        
        self.text = text
        
        # 使用jieba进行中文分词
        words = jieba.lcut(text)
        # 过滤掉标点符号和空白字符
        chinese_punctuation = '！？｡。＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〱〲〳〴〵〶〷〸〹〺〻〼〽〾〿'
        all_punctuation = chinese_punctuation + string.punctuation
        words = [w.strip() for w in words if w.strip() and w not in all_punctuation]
        
        # 使用jieba进行词性标注
        words_with_pos = pseg.cut(text)
        pos_tags = [(word, flag) for word, flag in words_with_pos if word.strip() and word not in all_punctuation]
        
        # 词性统计
        pos_counts = Counter([flag for word, flag in pos_tags])
        
        # 词频统计
        word_freq = Counter(words)
        filtered_word_freq = Counter({word: count for word, count in word_freq.items() 
                                    if word not in self.chinese_stopwords and len(word) > 1})
        
        # 句子分割
        sentences = re.split(r'[。！？\n]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 句子长度分析
        sentence_lengths = [len(sent) for sent in sentences]
        avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
        
        # 人名、地名等实体识别（通过词性标注）
        entities = [(word, flag) for word, flag in pos_tags if flag in ['nr', 'ns', 'nt']]  # nr:人名, ns:地名, nt:机构名
        
        # 情感词汇示例（简化版）
        positive_words = ['好', '优秀', '棒', '赞', '喜欢', '爱', '美好', '幸福', '成功', '快乐', '高兴', '满意', '精彩', '完美', '厉害', '牛', '强', '美', '雅', '佳']
        negative_words = ['坏', '差', '讨厌', '恨', '痛苦', '失败', '悲伤', '难过', '糟糕', '失望', '伤心', '愤怒', '生气', '烦', '糟', '毁', '烂', '丑', '恶', '劣']
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        result = {
            '基础统计': {
                '总字符数': len(text),
                '词语总数': len(words),
                '句子数': len(sentences),
                '词汇总数（去重）': len(set(words)),
                '平均句长': round(avg_sentence_length, 2)
            },
            '词频分析': {
                '高频词（含停用词）': dict(word_freq.most_common(10)),
                '高频词（去除停用词，词长>1）': dict(filtered_word_freq.most_common(10))
            },
            '词性分析': dict(pos_counts.most_common()),
            '命名实体识别（基于词性）': entities,
            '情感分析（简化版）': {
                '正面词数量': positive_count,
                '负面词数量': negative_count,
                '情感倾向': '积极' if positive_count > negative_count else '消极' if negative_count > positive_count else '中性'
            },
            '句子分析': {
                '最长句子': max(sentences, key=len) if sentences else '',
                '最短句子': min(sentences, key=len) if sentences else ''
            }
        }
        
        return result
    
    def print_analysis(self, text):
        """
        打印分析结果
        """
        try:
            result = self.analyze(text)
            print("=" * 60)
            print("中文文本分析结果（使用jieba和NLTK）")
            print("=" * 60)
            
            for category, data in result.items():
                print(f"\n{category}:")
                print("-" * 40)
                
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, list):
                            if all(isinstance(item, tuple) for item in value):
                                print(f"{key}:")
                                for item in value[:10]:  # 只显示前10个项目
                                    if isinstance(item, tuple) and len(item) >= 2:
                                        print(f"  - {item[0]} ({item[1]})")
                                    else:
                                        print(f"  - {item}")
                            else:
                                print(f"{key}: {value[:5]}...")  # 只显示前5个项目
                        elif isinstance(value, str) and len(value) > 100:
                            print(f"{key}: {value[:100]}...")
                        else:
                            print(f"{key}: {value}")
                else:
                    print(data)

        except ValueError as e:
            print(f"错误: {e}")
            
         # 生成词频图
        try:
            import matplotlib.pyplot as plt
            from collections import Counter
            # 使用传入的 text 重新分词
            plt.rcParams['font.sans-serif'] = ['SimHei']      # 用来正常显示中文标签
            plt.rcParams['axes.unicode_minus'] = False        # 用来正常显示负号
            words = list(jieba.cut(text))
            word_counts = Counter(words)
            top_words = word_counts.most_common(20)
            if top_words:
                word_list, counts = zip(*top_words)
                plt.figure(figsize=(10, 6))
                plt.barh(word_list, counts)
                plt.xlabel('词频')
                plt.title('Top 20 词频分布')
                plt.gca().invert_yaxis()
                plt.tight_layout()
                plt.savefig('word_freq.png', dpi=150)
                plt.close()
                print("词频图已保存为 word_freq.png")
            else:
                print("没有足够的词语生成词频图")
        except Exception as e:
            print(f"生成词频图时出错：{e}") 

        except ValueError as e:
            print(f"错误: {e}")


# 示例使用
if __name__ == "__main__":
    import sys
    analyzer = ChineseTextAnalyzer()
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        with open(filename, 'r', encoding='utf-8') as f:
            user_input = f.read()
        print(f"正在分析文件：{filename}")
        analyzer.print_analysis(user_input)
    else:
        print("请输入您要分析的中文文本[不超过3000字]：")
        user_input = input()
        analyzer.print_analysis(user_input)
    