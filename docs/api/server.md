# 服务器 API 参考

本页详细介绍 `openkimi.api` 模块提供的功能，主要是OpenAI兼容API服务器。

## API服务器

`openkimi.api.server` 模块提供了启动OpenAI兼容API服务器的功能。

### 启动脚本

服务器可以通过以下命令启动：

```bash
python -m openkimi.api.server [选项]
```

详细选项和使用方法请参考[API服务器指南](../guides/api_server.md)。

## API路由器

`openkimi.api.routers` 模块包含用于构建FastAPI应用的路由器。

### `create_chat_router`

创建处理`/v1/chat/completions`端点的FastAPI路由器。

```python
from fastapi import APIRouter
from openkimi import KimiEngine

def create_chat_router(engine: KimiEngine) -> APIRouter:
    pass
```

- **参数**：
    - `engine` (KimiEngine): 已初始化的`KimiEngine`实例。
- **返回**：
    - 一个`fastapi.APIRouter`实例，包含了处理聊天请求的逻辑。

### 使用示例

```python
from fastapi import FastAPI
from openkimi import KimiEngine
from openkimi.api.routers import create_chat_router

# 初始化引擎
engine = KimiEngine(config_path="config.json")

# 创建FastAPI应用
app = FastAPI()

# 创建并包含聊天路由器
chat_router = create_chat_router(engine)
app.include_router(chat_router)

# (可选) 添加其他自定义路由
@app.get("/health")
def health_check():
    return {"status": "ok"}

# 运行服务器 (例如使用 uvicorn)
# uvicorn main:app --reload
```

## 请求和响应模型

API服务器使用Pydantic模型来定义请求和响应体，与OpenAI API兼容。

### 主要模型 (部分)

- `ChatCompletionRequest`: `/v1/chat/completions`的请求体模型。
- `ChatCompletionResponse`: `/v1/chat/completions`的非流式响应模型。
- `ChatCompletionChunkResponse`: `/v1/chat/completions`的流式响应块模型。
- `ChatMessage`: 消息对象模型（`role`, `content`）。

这些模型主要在`openkimi/api/models.py`中定义（如果存在），或直接在路由器代码中使用。

## 总结

`openkimi.api`模块使得将OpenKimi的功能暴露为标准化的、与OpenAI兼容的API服务变得简单。这允许你使用任何支持OpenAI API的客户端库或工具与OpenKimi进行交互。 