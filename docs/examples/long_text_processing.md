# 长文本处理示例

OpenKimi的核心优势在于处理超长文本。本文档提供如何有效处理长文本的示例。

## 处理超长文档

### 示例：分析长篇小说

假设我们想分析《战争与和平》全书，并回答一些问题。

```python
import asyncio
import time
from openkimi import KimiEngine

async def analyze_novel():
    # 初始化引擎，使用本地模型以节省API成本
    engine = KimiEngine(
        llm_config={
            "type": "local",
            "model_path": "mistralai/Mistral-7B-Instruct-v0.1",
            "device": "cuda",
            "load_in_4bit": True
        },
        processor_config={
            "batch_size": 1024,  # 使用更大的块大小
            "entropy_threshold": 2.2
        },
        rag_config={
            "embedding_model": "all-MiniLM-L6-v2",
            "top_k": 10  # 检索更多相关片段
        },
        mpr_candidates=2
    )
    
    # 加载《战争与和平》（假设为war_and_peace.txt）
    print("加载小说...")
    start_time = time.time()
    with open("war_and_peace.txt", "r", encoding="utf-8") as f:
        novel_text = f.read()
    
    # 摄入小说
    print("摄入小说，这可能需要一些时间...")
    await engine.ingest(novel_text)
    end_time = time.time()
    print(f"小说摄入完成，耗时: {end_time - start_time:.2f}秒")
    
    # 提问
    questions = [
        "安德烈·博尔孔斯基的主要性格特征是什么？",
        "描述1812年俄法战争期间莫斯科大火的情景。",
        "皮埃尔·别祖霍夫的人生哲学是如何演变的？",
        "小说中关于历史和个人作用的探讨是什么？",
        "娜塔莎·罗斯托娃和安德烈的关系是如何发展的？"
    ]
    
    for question in questions:
        print(f"\n问题: {question}")
        print("回答: ", end="", flush=True)
        answer_start_time = time.time()
        
        async for chunk in engine.stream_chat(question):
            print(chunk, end="", flush=True)
        
        answer_end_time = time.time()
        print(f"\n(回答耗时: {answer_end_time - answer_start_time:.2f}秒)")

# 运行异步函数
asyncio.run(analyze_novel())
```

### 关键技术点

- **递归RAG**：当构建的提示超过模型上下文长度时，OpenKimi会自动触发递归RAG压缩，将低信息熵内容存储到RAG中，保留高信息熵内容，确保核心信息不丢失。
- **信息熵评估**：通过评估文本块的信息密度，优先保留关键信息，优化上下文。
- **MPR**：即使在处理长文本时，也可以使用多路径推理来提高答案的全面性。

## 处理代码库

### 示例：理解一个大型Python项目

假设我们想理解一个大型Python项目（例如Django框架）的结构和关键组件。

```python
import os
import asyncio
from openkimi import KimiEngine

async def analyze_codebase(project_path):
    # 初始化引擎
    engine = KimiEngine(
        llm_config={
            "type": "api",
            "api_key": "your-api-key",
            "model_name": "gpt-4-turbo"
        },
        processor_config={
            "batch_size": 1024,
            "entropy_method": "structural"  # 结构熵可能更适合代码
        },
        rag_config={
            "top_k": 8
        },
        mpr_candidates=2
    )
    
    print(f"分析代码库: {project_path}")
    all_code = ""
    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        # 添加文件路径作为上下文
                        all_code += f"\n--- File: {os.path.relpath(file_path, project_path)} ---\n"
                        all_code += f.read()
                except Exception as e:
                    print(f"无法读取文件 {file_path}: {e}")
    
    print(f"总代码长度: {len(all_code)} 字符")
    print("摄入代码库...")
    await engine.ingest(all_code)
    print("代码库摄入完成！")
    
    # 提问
    questions = [
        "Django的MTV架构是什么？各个部分如何交互？",
        "描述Django ORM的主要功能。",
        "Django的请求处理流程是怎样的？",
        "Django中的中间件（Middleware）的作用是什么？",
        "如何实现自定义用户模型？"
    ]
    
    for question in questions:
        print(f"\n问题: {question}")
        print("回答: ", end="", flush=True)
        
        async for chunk in engine.stream_chat(question):
            print(chunk, end="", flush=True)
        
        print()

# 设置项目路径并运行
# project_path = "path/to/django/source/code"
# asyncio.run(analyze_codebase(project_path))
```

### 处理技巧

- **添加文件路径**：在摄入代码时，将文件路径作为上下文添加，有助于模型理解代码结构。
- **调整熵方法**：可以尝试不同的熵计算方法（如`"structural"`）来更好地适应代码的特性。
- **增大块大小**：对于代码，可能需要更大的`batch_size`来保留完整的函数或类定义。

## 处理大量文档集合

### 示例：分析一组研究论文

假设我们有一个包含多篇PDF研究论文的文件夹，需要进行综合分析。

```python
import os
import asyncio
from openkimi import KimiEngine
# 需要安装PyPDF2: pip install pypdf2
from PyPDF2 import PdfReader

async def analyze_papers(folder_path):
    engine = KimiEngine(
        llm_config={
            "type": "api",
            "api_key": "your-api-key",
            "model_name": "gpt-4"
        },
        mpr_candidates=3
    )
    
    print(f"分析文件夹中的论文: {folder_path}")
    all_text = ""
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(folder_path, filename)
            try:
                reader = PdfReader(file_path)
                paper_text = ""
                for page in reader.pages:
                    paper_text += page.extract_text() or ""
                
                # 添加文件名作为上下文
                all_text += f"\n--- Paper: {filename} ---\n"
                all_text += paper_text
                print(f"已加载: {filename}")
            except Exception as e:
                print(f"无法处理PDF文件 {filename}: {e}")
    
    print("摄入所有论文...")
    await engine.ingest(all_text)
    print("论文摄入完成！")
    
    # 提问
    questions = [
        "这些论文的主要研究主题是什么？",
        "比较论文A和论文B的研究方法和结论。",
        "总结这些论文中提到的未来研究方向。",
        "这些研究对行业有什么潜在影响？"
    ]
    
    for question in questions:
        print(f"\n问题: {question}")
        print("回答: ", end="", flush=True)
        
        async for chunk in engine.stream_chat(question):
            print(chunk, end="", flush=True)
        
        print()

# 设置文件夹路径并运行
# papers_folder = "path/to/research_papers"
# asyncio.run(analyze_papers(papers_folder))
```

### 处理技巧

- **提取高质量文本**：使用可靠的PDF提取库（如PyPDF2或更高级的OCR工具）来获取文本。
- **标识文档来源**：在摄入文本时，明确标识每个文档的来源（如文件名），有助于模型区分不同文档的内容。
- **分批摄入**：对于非常大的文档集合，可以考虑分批摄入，或者在每次查询时动态加载相关文档。

## 性能优化建议

处理长文本时，性能可能是一个挑战。以下是一些优化建议：

1. **使用更快的嵌入模型**：如果RAG检索成为瓶颈，可以考虑使用更轻量级的嵌入模型。
2. **优化RAG参数**：调整`top_k`和`similarity_threshold`来平衡检索质量和速度。
3. **硬件加速**：使用GPU（CUDA或MPS）加速本地模型。
4. **量化**：使用4位或8位量化来减少本地模型的内存占用。
5. **调整MPR候选数量**：对于长文本，减少MPR候选数量可以显著提高速度。
6. **缓存**：如果需要重复查询相同或相似的问题，可以实现结果缓存。

## 常见问题

- **处理时间过长**：尝试上述性能优化建议。
- **内存不足**：使用量化、减少`batch_size`或增加系统内存/显存。
- **结果不准确**：调整RAG和MPR参数，尝试不同的熵方法，确保文本提取质量高。

## 下一步

- 了解OpenKimi的[多模态功能](../guides/multimodal.md)
- 探索[API服务器](../guides/api_server.md)的使用方法 