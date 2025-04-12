# 多模态输入示例

本文档提供使用OpenKimi多模态功能的示例。

## 初始化多模态引擎

```python
from openkimi import KimiEngine

# 配置使用OpenAI Vision模型
engine = KimiEngine(
    llm_config={
        "type": "multimodal",
        "api_key": "your-api-key",  # 你的OpenAI API密钥
        "model_name": "gpt-4-vision-preview"
    }
)

# 或者直接初始化模型
from openkimi.core.models import OpenAIMultiModalModel

model = OpenAIMultiModalModel(
    api_key="your-api-key",
    model_name="gpt-4-vision-preview"
)
```

## 处理单张图片

```python
import asyncio
from PIL import Image
from openkimi.core.models import OpenAIMultiModalModel

async def describe_image():
    # 初始化模型
    model = OpenAIMultiModalModel(api_key="your-api-key")
    
    # 使用文件路径
    image_path = "path/to/landscape.jpg"
    
    # 生成描述
    prompt = "详细描述这张图片的内容和氛围"
    response = await model.generate_with_images(prompt, [image_path])
    print(f"图片描述 (路径):\n{response}")
    
    # 使用PIL图像对象
    pil_image = Image.open("path/to/cityscape.png")
    prompt = "描述这张城市风景图"
    response = await model.generate_with_images(prompt, [pil_image])
    print(f"\n图片描述 (PIL):\n{response}")
    
    # 使用字节流
    with open("path/to/portrait.jpg", "rb") as f:
        image_bytes = f.read()
    prompt = "描述这张肖像画"
    response = await model.generate_with_images(prompt, [image_bytes])
    print(f"\n图片描述 (Bytes):\n{response}")

# 运行异步函数
asyncio.run(describe_image())
```

## 处理多张图片

```python
import asyncio
from PIL import Image
from openkimi.core.models import OpenAIMultiModalModel

async def compare_multiple_images():
    # 初始化模型
    model = OpenAIMultiModalModel(api_key="your-api-key")
    
    # 加载多张图片
    image1 = "path/to/cat.jpg"
    image2 = Image.open("path/to/dog.png")
    with open("path/to/bird.jpg", "rb") as f:
        image3_bytes = f.read()
        
    # 比较图片
    prompt = """比较这三张图片中的动物：
    1. 分别描述每张图片中的动物。
    2. 比较它们的共同点和不同点。
    3. 哪种动物看起来最友好？为什么？"""
    
    response = await model.generate_with_images(
        prompt,
        [image1, image2, image3_bytes]
    )
    
    print(f"多图比较结果:\n{response}")

# 运行异步函数
asyncio.run(compare_multiple_images())
```

## 结合文本和图像

```python
import asyncio
from PIL import Image
from openkimi.core.models import OpenAIMultiModalModel

async def combine_text_and_image():
    # 初始化模型
    model = OpenAIMultiModalModel(api_key="your-api-key")
    
    # 加载图片
    chart_image = Image.open("path/to/sales_data.png")
    
    # 准备文本上下文
    report_text = """年度销售报告摘要：
    - 第一季度销售额为100万美元，同比增长10%。
    - 第二季度销售额为120万美元，同比增长15%。
    - 第三季度销售额为110万美元，同比增长8%。
    - 第四季度销售额为150万美元，同比增长20%。
    整体表现超出预期。"""
    
    # 提问，结合文本和图像
    prompt = f"""结合以下销售报告摘要和图表，分析销售表现：
    1. 图表中的数据是否与报告摘要一致？
    2. 最显著的增长发生在哪个季度？
    3. 有没有数据上的矛盾之处？
    4. 综合文本和图表，提出两个提高未来销售的建议。
    
报告摘要：
{report_text}
"""
    
    response = await model.generate_with_images(prompt, [chart_image])
    print(f"图文结合分析结果:\n{response}")

# 运行异步函数
asyncio.run(combine_text_and_image())
```

## 流式处理多模态输入

```python
import asyncio
from PIL import Image
from openkimi.core.models import OpenAIMultiModalModel

async def stream_multimodal_analysis():
    # 初始化模型
    model = OpenAIMultiModalModel(api_key="your-api-key")
    
    # 加载图像
    image = Image.open("path/to/process_diagram.jpg")
    
    # 提问
    prompt = "详细解释这张流程图的每个步骤"
    print(f"问题: {prompt}")
    print("回答: ", end="", flush=True)
    
    # 流式生成
    async for chunk in model.stream_generate_with_images(
        prompt=prompt,
        images=[image]
    ):
        print(chunk, end="", flush=True)
    
    print()  # 打印最后的换行

# 运行异步函数
asyncio.run(stream_multimodal_analysis())
```

## 使用KimiEngine处理多模态

目前`KimiEngine`的`chat`和`stream_chat`接口主要设计用于文本处理。要使用多模态功能，建议直接调用配置好的多模态模型实例。

```python
import asyncio
from openkimi import KimiEngine
from PIL import Image

async def engine_multimodal_example():
    # 初始化引擎，配置多模态模型
    engine = KimiEngine(
        llm_config={
            "type": "multimodal",
            "api_key": "your-api-key",
            "model_name": "gpt-4-vision-preview"
        }
    )
    
    # 访问引擎内部的多模态模型实例
    if not engine.llm_interface.supports_image_input:
        print("配置的模型不支持图像输入")
        return
        
    multimodal_model = engine.llm_interface
    
    # 加载图像
    image = Image.open("path/to/ui_screenshot.png")
    
    # 提问
    prompt = "分析这个UI截图，并提出3个改进建议"
    print(f"问题: {prompt}")
    print("回答: ", end="", flush=True)
    
    # 使用模型实例的流式多模态方法
    async for chunk in multimodal_model.stream_generate_with_images(
        prompt=prompt,
        images=[image]
    ):
        print(chunk, end="", flush=True)
    
    print()

# 运行异步函数
asyncio.run(engine_multimodal_example())
```

## 注意事项

- 确保安装了多模态支持的依赖：`pip install openkimi[multimodal]`
- 使用多模态功能通常需要特定的API模型（如GPT-4 Vision）
- 处理图像可能会增加API成本和处理时间
- 检查模型对单次请求图像数量的限制

## 下一步

- 探索OpenKimi的[配置选项](../guides/configuration.md)
- 了解[模型接口](../guides/models.md)的详细信息 