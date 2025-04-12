# 多模态功能

OpenKimi支持多模态输入，允许模型同时处理文本和图像。本指南介绍如何使用OpenKimi的多模态功能。

## 多模态概述

多模态功能允许模型理解和分析图像内容，并将图像信息与文本结合起来进行推理和生成。常见的应用场景包括：

- 图像描述和内容分析
- 基于图像的问答
- 图文结合的内容生成
- 图表和数据可视化分析
- 文档和截图理解

## 使用多模态模型

### 初始化多模态模型

```python
from openkimi import KimiEngine
from openkimi.core.models import OpenAIMultiModalModel

# 方法1：直接使用多模态模型类
model = OpenAIMultiModalModel(
    api_key="your-api-key",
    model_name="gpt-4-vision-preview"
)

# 方法2：通过KimiEngine配置使用多模态模型
engine = KimiEngine(
    llm_config={
        "type": "multimodal",
        "api_key": "your-api-key",
        "model_name": "gpt-4-vision-preview"
    }
)
```

### 处理图像输入

OpenKimi支持多种图像输入格式：

```python
import asyncio
from PIL import Image
from openkimi.core.models import OpenAIMultiModalModel

async def process_images():
    # 初始化模型
    model = OpenAIMultiModalModel(
        api_key="your-api-key",
        model_name="gpt-4-vision-preview"
    )
    
    # 1. 使用文件路径
    image_path = "path/to/image.jpg"
    
    # 2. 使用PIL图像对象
    pil_image = Image.open("another_image.png")
    
    # 3. 使用字节流
    with open("third_image.jpg", "rb") as f:
        image_bytes = f.read()
    
    # 组合多种图像输入
    response = await model.generate_with_images(
        prompt="描述这些图像并比较它们的内容",
        images=[image_path, pil_image, image_bytes],
        max_tokens=1000
    )
    
    print(response)

# 运行异步函数
asyncio.run(process_images())
```

### 流式输出

多模态模型也支持流式输出：

```python
import asyncio
from PIL import Image
from openkimi.core.models import OpenAIMultiModalModel

async def stream_image_processing():
    # 初始化模型
    model = OpenAIMultiModalModel(
        api_key="your-api-key",
        model_name="gpt-4-vision-preview"
    )
    
    # 加载图像
    image = Image.open("chart.png")
    
    # 流式生成
    prompt = "分析这个图表中的数据趋势"
    print(f"问题: {prompt}")
    print("回答: ", end="")
    
    async for chunk in model.stream_generate_with_images(
        prompt=prompt,
        images=[image],
        max_tokens=1000
    ):
        print(chunk, end="", flush=True)
    
    print()  # 打印最后的换行

# 运行异步函数
asyncio.run(stream_image_processing())
```

## 与RAG结合使用

多模态功能可以与RAG（检索增强生成）结合使用，允许模型根据检索到的文本和提供的图像进行推理：

```python
from openkimi import KimiEngine
from PIL import Image
import asyncio

async def multimodal_rag_example():
    # 初始化引擎，使用多模态模型
    engine = KimiEngine(
        llm_config={
            "type": "multimodal",
            "api_key": "your-api-key",
            "model_name": "gpt-4-vision-preview"
        }
    )
    
    # 加载文本资料
    with open("research_paper.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    # 摄入文本
    engine.ingest(text)
    
    # 加载图像
    image = Image.open("data_visualization.png")
    
    # 创建多模态模型实例（从引擎内部获取）
    multimodal_model = engine.llm_interface
    
    # 基于检索的文本和图像提问
    prompt = "根据研究论文和图表，总结主要发现并解释图中的数据如何支持这些发现"
    
    # 检索相关内容
    rag_context = engine.rag_manager.retrieve(prompt, top_k=3)
    
    # 构建带有RAG上下文的提示
    enhanced_prompt = f"""基于以下研究论文的相关部分和提供的图表，回答问题:
    
问题: {prompt}

研究论文相关内容:
{"".join(rag_context)}
"""
    
    # 使用多模态能力生成回答
    print("生成回答中...")
    
    async for chunk in multimodal_model.stream_generate_with_images(
        prompt=enhanced_prompt,
        images=[image],
        max_tokens=1000
    ):
        print(chunk, end="", flush=True)
    
    print()

# 运行异步函数
asyncio.run(multimodal_rag_example())
```

## 多模态处理技巧

### 图像预处理

为获得更好的结果，可以考虑对图像进行预处理：

```python
from PIL import Image, ImageEnhance

# 加载图像
image = Image.open("document.jpg")

# 调整大小（保持纵横比）
max_size = 1024
if max(image.size) > max_size:
    ratio = max_size / max(image.size)
    new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
    image = image.resize(new_size, Image.LANCZOS)

# 增强对比度
enhancer = ImageEnhance.Contrast(image)
image = enhancer.enhance(1.5)

# 增强清晰度
enhancer = ImageEnhance.Sharpness(image)
image = enhancer.enhance(1.2)
```

### 有效提示技巧

为多模态模型创建有效的提示：

1. **具体指定任务**：告诉模型你希望它关注图像的哪些方面
2. **步骤分解**：对于复杂任务，可以要求模型按步骤分析
3. **结合上下文**：提供相关的背景信息
4. **指定输出格式**：明确你希望得到的输出格式（列表、表格等）

例如：

```python
prompt = """分析这张图表，请执行以下步骤：
1. 描述图表类型和整体结构
2. 识别X轴和Y轴表示的数据
3. 总结主要数据趋势
4. 指出任何异常值或有趣的模式
5. 提出2-3个可能的解释或见解

最后，将你的分析总结为3-5个关键点。"""
```

## 多模态使用场景

### 文档分析

```python
from PIL import Image
from openkimi.core.models import OpenAIMultiModalModel
import asyncio

async def analyze_document():
    model = OpenAIMultiModalModel(api_key="your-api-key")
    document_image = Image.open("contract.jpg")
    
    prompt = """分析这份合同文档，并提供以下信息：
    1. 合同双方
    2. 主要条款摘要
    3. 任何潜在的法律风险
    4. 需要特别注意的细节"""
    
    response = await model.generate_with_images(prompt, [document_image])
    print(response)

asyncio.run(analyze_document())
```

### 数据可视化分析

```python
from PIL import Image
from openkimi.core.models import OpenAIMultiModalModel
import asyncio

async def analyze_chart():
    model = OpenAIMultiModalModel(api_key="your-api-key")
    chart_image = Image.open("sales_chart.png")
    
    prompt = """分析这个销售图表：
    1. 描述图表展示的主要销售趋势
    2. 识别销售高峰和低谷期
    3. 与行业季节性模式相比较
    4. 预测未来可能的趋势
    5. 提出3个提高销售的具体建议"""
    
    response = await model.generate_with_images(prompt, [chart_image])
    print(response)

asyncio.run(analyze_chart())
```

### 多图对比分析

```python
from PIL import Image
from openkimi.core.models import OpenAIMultiModalModel
import asyncio

async def compare_images():
    model = OpenAIMultiModalModel(api_key="your-api-key")
    
    image1 = Image.open("product_v1.jpg")
    image2 = Image.open("product_v2.jpg")
    
    prompt = """比较这两个产品设计：
    1. 描述两者的主要差异
    2. 评估每种设计的优缺点
    3. 从用户体验角度分析哪个设计更好
    4. 建议可能的改进
    以表格形式总结你的发现。"""
    
    response = await model.generate_with_images(prompt, [image1, image2])
    print(response)

asyncio.run(compare_images())
```

## 注意事项

- 多模态处理可能需要更长的处理时间和更高的计算资源
- 图像分辨率会影响处理结果和API成本
- OpenAI的GPT-4 Vision模型对每次请求有图像数量限制
- 处理敏感或私人图像时，请注意数据隐私和安全 