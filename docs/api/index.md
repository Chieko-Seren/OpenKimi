# API 参考

本部分提供OpenKimi API的详细技术参考。

## 目录

- [核心API](core.md) - `openkimi.core`模块API
  - [KimiEngine](core.md#kimiengine) - 主引擎
  - [TextProcessor](core.md#textprocessor) - 文本处理器
  - [RAGManager](core.md#ragmanager) - RAG管理器
  - [FrameworkGenerator](core.md#frameworkgenerator) - 框架生成器
  - [EntropyEvaluator](core.md#entropyevaluator) - 熵评估器

- [模型API](models.md) - `openkimi.core.models`模块API
  - [BaseModel](models.md#basemodel) - 基础模型接口
  - [MultiModalModel](models.md#multimodalmodel) - 多模态模型接口
  - [OpenAIModel](models.md#openaimodel) - OpenAI模型实现
  - [LocalModel](models.md#localmodel) - 本地模型实现
  - [OpenAIMultiModalModel](models.md#openaimultimodalmodel) - OpenAI多模态模型实现

- [工具API](utils.md) - `openkimi.utils`模块API
  - [LLMInterface](utils.md#llminterface) - LLM接口
  - [PromptLoader](utils.md#promptloader) - 提示加载器

- [服务器API](server.md) - `openkimi.api`模块API
  - [API服务器](server.md#api服务器) - OpenAI兼容API服务器
  - [路由器](server.md#路由器) - API路由器

## 快速入门

以下是使用OpenKimi API的基本示例：

```python
from openkimi import KimiEngine

# 初始化引擎
engine = KimiEngine()

# 加载长文本
with open("document.txt", "r", encoding="utf-8") as f:
    engine.ingest(f.read())

# 提问
response = engine.chat("根据文档内容，总结主要观点")
print(response)
```

有关更多示例，请参考[示例](../examples/)部分。

## 版本兼容性

OpenKimi API遵循[语义化版本控制](https://semver.org/)规范：

- **主版本**：不兼容的API更改
- **次版本**：向后兼容的功能添加
- **补丁版本**：向后兼容的错误修复

## 贡献

欢迎对OpenKimi API进行贡献！请参阅[贡献指南](../contributing.md)了解如何参与。

## 许可证

OpenKimi使用MIT许可证。详情请参阅[LICENSE](https://github.com/Chieko-Seren/OpenKimi/blob/main/LICENSE)文件。 