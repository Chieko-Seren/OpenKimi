# 基本对话

本示例展示了如何使用 OpenKimi 进行基本的对话。

## 初始化 KimiEngine

```python
from openkimi import KimiEngine

# 使用默认配置初始化引擎
engine = KimiEngine()

# 或者使用配置文件
# engine = KimiEngine(config_path="config.json")

# 或者直接提供配置参数
# engine = KimiEngine(
#     llm_config={
#         "type": "api",
#         "api_key": "your-api-key",
#         "model_name": "gpt-4"
#     }
# )
```

## 简单对话

```python
# 发送用户消息并获取回复
response = engine.chat("你好，请告诉我你是谁？")
print(f"AI: {response}")

# 继续对话
response = engine.chat("你能做什么？")
print(f"AI: {response}")

# 继续对话，引用前面的回复
response = engine.chat("刚才你提到的功能中，我对无限上下文处理最感兴趣。能详细解释一下吗？")
print(f"AI: {response}")
```

## 重置对话历史

如果要开始新的对话，可以重置会话历史：

```python
# 重置会话历史
engine.reset()

# 开始新的对话
response = engine.chat("让我们开始一个新话题，谈谈人工智能的发展历史")
print(f"AI: {response}")
```

## 完整示例

下面是一个完整的交互式对话示例：

```python
from openkimi import KimiEngine

def main():
    # 初始化引擎
    print("正在初始化 KimiEngine...")
    engine = KimiEngine()
    print("初始化完成！")
    
    # 交互式对话循环
    print("\n=== 开始与 OpenKimi 对话（输入'exit'退出，'reset'重置会话）===\n")
    
    while True:
        user_input = input("用户: ")
        
        if user_input.lower() == "exit":
            print("再见！")
            break
            
        if user_input.lower() == "reset":
            engine.reset()
            print("会话已重置！")
            continue
            
        # 获取 AI 回复
        response = engine.chat(user_input)
        print(f"OpenKimi: {response}")
        print()
        
if __name__ == "__main__":
    main()
```

运行此脚本，你将能够与 OpenKimi 进行交互式对话。

## 注意事项

1. 首次调用 `chat()` 方法时，系统会自动初始化所需的模型和资源，可能需要一些时间。
2. OpenKimi 默认会记住对话历史，以便理解上下文。如果对话太长导致性能问题，可以调用 `reset()` 方法清除历史。
3. 如果使用 API 模式，请确保提供有效的 API 密钥。 