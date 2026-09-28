import jieba  # 虽然图片中有导入，但本代码未实际使用，保留以符原图

# 规则：单音节代词、动词、形容词 → 自由语素
FREE_PRONOUNS = {"我", "你", "他", "人", "她", "它"}
FREE_VERBS = {"玩", "游", "看", "听", "说", "走", "跑", "来", "去", "可", "迎", "虽"}
FREE_ADJECTIVES = {"大", "小", "好", "坏", "高", "低", "多", "少"}

# 合并所有自由语素
FREE_MORPHEMES = FREE_PRONOUNS | FREE_VERBS | FREE_ADJECTIVES

# 音译连绵词 → 音节（其中的单字若不在自由语素中，则视为音节）
YINYI = {"葡萄", "可乐", "仿佛", "蜻蜓", "巧克力"}
# 提取所有连绵词中的单个汉字
YINYI_CHARS = set(char for word in YINYI for char in word)

def analyze_char(char):
    """判断单个汉字的类型"""
    if char in FREE_MORPHEMES:
        return "自由语素"
    elif char in YINYI_CHARS:
        return "音节"      # 只出现在连绵词中，不能独立使用
    else:
        return "不自由语素"  # 可以组词，但不能独立使用

def analyze_word(word):
    """分析一个词，打印每个字的类型"""
    print(f"词：{word}")
    for ch in word:
        print(f"  {ch}：{analyze_char(ch)}")
    print()

# 分析指定的四个词
if __name__ == "__main__":
    words = ["人民", "可怜", "欢迎", "虽然"]
    for w in words:
        analyze_word(w)