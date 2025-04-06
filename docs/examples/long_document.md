# 加载长文档

本示例展示了如何使用 OpenKimi 加载和处理超长文本文档，突破传统 LLM 的上下文长度限制。

## 导入必要库

```python
import os
from openkimi import KimiEngine
```

## 初始化 KimiEngine

```python
# 使用默认配置初始化引擎
engine = KimiEngine()

# 或者使用配置文件
# engine = KimiEngine(config_path="config.json")
```

## 加载长文档

OpenKimi 可以处理远超 LLM 上下文限制的超长文档：

```python
# 加载一本书（例如《三体》，约30万字）
with open("three_body.txt", "r", encoding="utf-8") as f:
    long_text = f.read()
    print(f"文档长度: {len(long_text)} 字符")
    
    # 摄入文本（OpenKimi 会自动处理）
    engine.ingest(long_text)
```

在调用 `ingest()` 方法时，OpenKimi 会：

1. 将长文本分块
2. 计算每个块的信息熵
3. 根据信息熵将文本分类为高信息熵（保留在上下文中）和低信息熵（存储在 RAG 系统中）
4. 为低信息熵文本生成摘要并向量化存储

## 基于文档提问

现在可以向 OpenKimi 提问文档内容相关的问题：

```python
# 基础问题
response = engine.chat("请总结这本书的主要情节。")
print(f"总结：\n{response}\n")

# 细节问题
response = engine.chat("叶文洁在文化大革命中有什么经历？")
print(f"回答：\n{response}\n")

# 分析性问题
response = engine.chat("分析一下这本书中的'黑暗森林'理论。")
print(f"分析：\n{response}\n")

# 复杂推理
response = engine.chat("如果将三体文明的技术能力与现代人类科技水平对比，有哪些关键差距？")
print(f"推理：\n{response}\n")
```

即使问题需要引用文档的不同部分，OpenKimi 也能够：

1. 从 RAG 系统中检索相关文本
2. 动态调整上下文
3. 生成框架和答案
4. 在需要时自动应用递归 RAG 压缩，确保不超过模型上下文限制

## 处理其他格式文档

除了纯文本文件，OpenKimi 还可以处理其他格式的文档：

```python
# 你需要先安装相关依赖：
# pip install python-docx PyPDF2

import docx  # 处理 .docx 文件
from PyPDF2 import PdfReader  # 处理 PDF 文件

# 加载 Word 文档
def load_docx(filepath):
    doc = docx.Document(filepath)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

# 加载 PDF 文件
def load_pdf(filepath):
    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# 示例：加载并处理 Word 文档
if os.path.exists("report.docx"):
    text = load_docx("report.docx")
    engine.ingest(text)
    print("已加载 Word 文档")

# 示例：加载并处理 PDF 文件
if os.path.exists("paper.pdf"):
    text = load_pdf("paper.pdf")
    engine.ingest(text)
    print("已加载 PDF 文档")
```

## 完整示例：分析长篇小说

下面是一个分析长篇小说的完整示例：

```python
from openkimi import KimiEngine
import time

def analyze_novel():
    # 初始化引擎
    print("正在初始化 KimiEngine...")
    engine = KimiEngine()
    print("初始化完成！")
    
    # 加载长篇小说
    novel_path = "novels/war_and_peace.txt"  # 《战争与和平》
    print(f"正在加载小说: {novel_path}")
    
    start_time = time.time()
    with open(novel_path, "r", encoding="utf-8") as f:
        novel_text = f.read()
        
    print(f"文件大小: {len(novel_text)/1024:.2f} KB")
    print("正在处理文本...")
    engine.ingest(novel_text)
    
    processing_time = time.time() - start_time
    print(f"处理完成！耗时: {processing_time:.2f} 秒")
    
    # 进行小说分析
    analysis_questions = [
        "请总结《战争与和平》的主要情节。",
        "分析小说中的主要人物及其性格特点。",
        "托尔斯泰在小说中表达了哪些哲学观点？",
        "小说中的战争场景如何反映了作者对战争的态度？",
        "小说的历史背景是什么，托尔斯泰如何将历史与小说情节融合？"
    ]
    
    print("\n=== 开始小说分析 ===\n")
    for i, question in enumerate(analysis_questions, 1):
        print(f"问题 {i}: {question}")
        start_time = time.time()
        response = engine.chat(question)
        query_time = time.time() - start_time
        print(f"回答 (用时 {query_time:.2f} 秒):\n{response}\n")
        
    print("分析完成！")

if __name__ == "__main__":
    analyze_novel()
```

## 注意事项

1. 处理超长文档时，初次摄入可能需要较长时间，这是正常的。
2. 如果文档极其庞大（如整本书集），建议进行分段处理。
3. 摄入的文档内容会在会话重置后清除，需要重新加载。
4. RAG 系统的质量会直接影响回答的准确性。 