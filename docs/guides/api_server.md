# OpenAI兼容API服务器

OpenKimi提供了一个与OpenAI API兼容的服务器，使你可以通过标准的OpenAI客户端库与OpenKimi交互。本文档详细介绍如何设置、配置和使用这个API服务器。

## 启动API服务器

### 基本用法

启动API服务器的基本命令如下：

```bash
python -m openkimi.api.server --config config.json
```

这将在默认地址（127.0.0.1:8000）上启动服务器，使用`config.json`中的配置。

### 完整命令行选项

```bash
python -m openkimi.api.server [选项]
```

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--host` | `127.0.0.1` | 服务器监听地址 |
| `--port` | `8000` | 服务器监听端口 |
| `--config` / `-c` | - | KimiEngine配置文件路径（必需） |
| `--mpr-candidates` | 配置文件中的值 | 覆盖配置中的MPR候选数量 |
| `--reload` | 否 | 开发模式，代码更改时自动重载 |

### 示例

```bash
# 在公网地址上启动服务器
python -m openkimi.api.server --config config.json --host 0.0.0.0 --port 8000

# 使用开发模式
python -m openkimi.api.server --config config.json --reload

# 覆盖MPR候选数量
python -m openkimi.api.server --config config.json --mpr-candidates 5
```

## API端点

API服务器提供以下端点：

### 1. 聊天接口

- **URL**: `/v1/chat/completions`
- **方法**: `POST`
- **功能**: 处理聊天请求，与OpenAI的chat completions API兼容

#### 请求格式

```json
{
    "model": "openkimi-model",
    "messages": [
        {"role": "system", "content": "这是需要处理的长文档内容..."},
        {"role": "user", "content": "请根据文档回答这个问题？"}
    ],
    "temperature": 0.7,
    "max_tokens": 500,
    "stream": false
}
```

#### 参数说明

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `model` | string | 是 | 模型标识符，任意值都会使用配置的模型 |
| `messages` | array | 是 | 消息数组，每个消息包含`role`和`content` |
| `temperature` | float | 否 | 采样温度，0-2之间，默认为1 |
| `max_tokens` | integer | 否 | 最大生成token数量 |
| `stream` | boolean | 否 | 是否使用流式响应，默认为false |

#### 响应格式

非流式响应：

```json
{
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1677858242,
    "model": "openkimi-model",
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "这是OpenKimi生成的回复..."
            },
            "index": 0,
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 56,
        "completion_tokens": 31,
        "total_tokens": 87
    }
}
```

流式响应（每个chunk）：

```json
{
    "id": "chatcmpl-123",
    "object": "chat.completion.chunk",
    "created": 1677858242,
    "model": "openkimi-model",
    "choices": [
        {
            "delta": {
                "content": "这是"
            },
            "index": 0,
            "finish_reason": null
        }
    ]
}
```

### 2. 健康检查

- **URL**: `/health`
- **方法**: `GET`
- **功能**: 检查服务器和引擎状态

#### 响应格式

```json
{
    "status": "ok",
    "version": "0.1.0"
}
```

## 使用示例

### 使用curl

```bash
# 非流式请求
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openkimi-model", 
    "messages": [
      {"role": "system", "content": "这是需要处理的长文档内容..."},
      {"role": "user", "content": "请根据文档回答这个问题？"}
    ]
  }'

# 流式请求
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openkimi-model", 
    "messages": [
      {"role": "system", "content": "这是需要处理的长文档内容..."},
      {"role": "user", "content": "请根据文档回答这个问题？"}
    ],
    "stream": true
  }'
```

### 使用Python客户端（OpenAI库）

```python
import openai

# 配置客户端
client = openai.OpenAI(
    api_key="随便填写",  # API密钥值不重要，但需要提供
    base_url="http://localhost:8000/v1"  # 指向OpenKimi API服务器
)

# 非流式请求
response = client.chat.completions.create(
    model="openkimi-model",
    messages=[
        {"role": "system", "content": "这是需要处理的长文档内容..."},
        {"role": "user", "content": "请根据文档回答这个问题？"}
    ],
    max_tokens=500
)
print(response.choices[0].message.content)

# 流式请求
stream = client.chat.completions.create(
    model="openkimi-model",
    messages=[
        {"role": "system", "content": "这是需要处理的长文档内容..."},
        {"role": "user", "content": "请根据文档回答这个问题？"}
    ],
    max_tokens=500,
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### 使用JavaScript客户端

```javascript
// 使用fetch API
async function chatWithOpenKimi() {
  const response = await fetch('http://localhost:8000/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'openkimi-model',
      messages: [
        {role: 'system', content: '这是需要处理的长文档内容...'},
        {role: 'user', content: '请根据文档回答这个问题？'}
      ],
      max_tokens: 500
    })
  });
  
  const data = await response.json();
  console.log(data.choices[0].message.content);
}

// 流式请求
async function streamChatWithOpenKimi() {
  const response = await fetch('http://localhost:8000/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'openkimi-model',
      messages: [
        {role: 'system', content: '这是需要处理的长文档内容...'},
        {role: 'user', content: '请根据文档回答这个问题？'}
      ],
      max_tokens: 500,
      stream: true
    })
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const {value, done} = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    // 处理SSE格式的数据流
    const lines = chunk.split('\n\n');
    for (const line of lines) {
      if (line.startsWith('data: ') && line !== 'data: [DONE]') {
        const data = JSON.parse(line.substring(6));
        if (data.choices[0].delta.content) {
          process.stdout.write(data.choices[0].delta.content);
        }
      }
    }
  }
}
```

## 工作流程示例

以下是使用OpenKimi API服务器的典型工作流程：

1. **准备配置文件**：创建包含所需LLM、处理器和RAG设置的配置文件
2. **启动API服务器**：使用配置文件启动服务器
3. **预加载数据**（可选）：在启动时加载常用文档
4. **接收客户端请求**：
   - 第一条系统消息通常包含要处理的长文档
   - 用户消息包含基于文档的问题
5. **处理请求**：
   - 使用TextProcessor分析文档
   - 应用RAG策略存储低信息密度内容
   - 使用MPR生成回复
6. **返回响应**：以OpenAI兼容格式返回结果

## 高级配置

### 自定义服务器行为

你可以通过修改`openkimi/api/server.py`来自定义服务器行为，或者创建自己的服务器脚本：

```python
from fastapi import FastAPI, Request
from openkimi import KimiEngine
from openkimi.api.routers import create_chat_router

# 创建自定义应用
app = FastAPI(title="Custom OpenKimi API")

# 初始化引擎
engine = KimiEngine(config_path="config.json")

# 添加聊天路由器
chat_router = create_chat_router(engine)
app.include_router(chat_router)

# 添加自定义路由
@app.get("/custom-endpoint")
async def custom_endpoint():
    return {"message": "这是自定义端点"}

# 启动服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Docker部署

你可以使用Docker部署OpenKimi API服务器：

1. 创建Dockerfile：

```dockerfile
FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "openkimi.api.server", "--config", "config.json", "--host", "0.0.0.0", "--port", "8000"]
```

2. 构建和运行Docker镜像：

```bash
docker build -t openkimi-api .
docker run -p 8000:8000 openkimi-api
```

## 安全性注意事项

使用API服务器时，请注意以下安全事项：

1. **访问控制**：默认情况下，API服务器不包含认证机制，建议在生产环境中：
   - 在反向代理（如Nginx）中添加认证
   - 限制IP访问范围
   - 添加自定义认证中间件

2. **数据隐私**：
   - 避免在没有适当保护的情况下在公网暴露服务
   - 考虑加密存储任何敏感文档

3. **资源限制**：
   - 设置请求大小限制
   - 实施速率限制以防止滥用

## 故障排除

### 常见问题

1. **服务器启动失败**：
   - 检查配置文件格式是否正确
   - 确保指定的端口未被占用

2. **请求超时**：
   - 增加客户端超时设置
   - 对于处理大文档，考虑使用流式响应

3. **内存不足**：
   - 减少MPR候选数量
   - 使用量化选项（对于本地模型）
   - 增加服务器内存

### 查看日志

API服务器日志包含有用的调试信息：

```bash
# 启用详细日志
python -m openkimi.api.server --config config.json --log-level debug
```

## 性能优化

提高API服务器性能的建议：

1. **使用本地模型时**：
   - 启用量化（8位或4位）
   - 使用FlashAttention加速
   - 对于多GPU系统，启用Accelerate

2. **使用API模型时**：
   - 调整MPR候选数量
   - 使用缓存避免重复查询

3. **内存管理**：
   - 对于长时间运行的服务器，定期重置引擎状态
   - 监控内存使用情况并设置适当的限制 