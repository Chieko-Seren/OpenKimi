# API 服务器

OpenKimi 提供了一个与 OpenAI 兼容的 API 服务器，可以将 OpenKimi 的无限上下文能力作为服务提供给其他应用程序。

## 启动服务器

### 使用命令行工具

```bash
# 基本用法
python run_server.py --config examples/config.json

# 指定主机和端口
python run_server.py --config examples/config.json --host 0.0.0.0 --port 8000

# 启用 MCP
python run_server.py --config examples/config.json --mcp-candidates 3

# 开发模式（自动重载）
python run_server.py --config examples/config.json --reload
```

### 使用 Python 模块

```bash
python -m openkimi.api.server --config examples/config.json
```

## API 端点

### 聊天完成 API

```
POST /v1/chat/completions
```

**请求格式：**

```json
{
  "model": "openkimi-model",
  "messages": [
    {"role": "system", "content": "这是长文档内容..."},
    {"role": "user", "content": "请根据文档回答这个问题"}
  ]
}
```

**响应格式：**

```json
{
  "id": "chatcmpl-123456789",
  "object": "chat.completion",
  "created": 1677858242,
  "model": "openkimi-model",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "这是回答内容..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 1024,
    "completion_tokens": 256,
    "total_tokens": 1280
  }
}
```

**示例使用（curl）：**

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openkimi-model", 
    "messages": [
      {"role": "system", "content": "这是需要处理的长文档内容..."},
      {"role": "user", "content": "请根据文档回答这个问题？"}
    ]
  }'
```

### 健康检查 API

```
GET /health
```

**响应：**

```json
{
  "status": "healthy",
  "engine": "ready"
}
```

## 使用 Python 客户端

你可以使用标准的 OpenAI 客户端库与 OpenKimi API 服务器交互：

```python
import openai

# 配置客户端
openai.api_key = "任意值"  # OpenKimi 服务器不验证 API 密钥
openai.api_base = "http://localhost:8000/v1"  # 指向 OpenKimi 服务器

# 发送请求
response = openai.ChatCompletion.create(
    model="openkimi-model",
    messages=[
        {"role": "system", "content": "这里是长文档内容..."},
        {"role": "user", "content": "请分析这个文档的主要观点"}
    ]
)

# 处理响应
print(response.choices[0].message.content)
```

## 注意事项

1. 当前 API 实现较为简单，每次请求会重置引擎状态并重新处理 `system` 消息中的文档，效率不高。
2. 服务器不支持流式输出（`stream=True`）。
3. 所有请求共享同一个 KimiEngine 实例，但每个请求会重置会话状态。
4. API 服务器默认不进行身份验证，在生产环境中应添加适当的安全措施。 