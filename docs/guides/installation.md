# 安装指南

本指南将帮助你安装OpenKimi并配置所需的环境。

## 系统要求

- **操作系统**：Windows、Linux 或 macOS
- **Python 版本**：3.8 或更高
- **内存**：建议 16GB+（根据模型和输入规模而定）

## 安装步骤

### 通过pip安装

最简单的安装方式是通过pip：

```bash
pip install openkimi
```

### 从源码安装

如果你希望使用最新的开发版本，可以从GitHub仓库克隆源码：

```bash
git clone https://github.com/Chieko-Seren/OpenKimi.git
cd OpenKimi
pip install -e .
```

### 安装可选依赖

根据你的使用需求，可能需要安装以下可选依赖：

1. **本地模型支持**（使用HuggingFace Transformers）：
```bash
pip install openkimi[local]
```

2. **API模型支持**（使用OpenAI API等）：
```bash
pip install openkimi[api]
```

3. **多模态支持**（图像处理）：
```bash
pip install openkimi[multimodal]
```

4. **高性能向量检索**（FAISS支持）：
```bash
pip install openkimi[faiss]
```

5. **全部依赖**：
```bash
pip install openkimi[all]
```

## 验证安装

安装完成后，你可以通过运行以下代码来验证安装是否成功：

```python
from openkimi import KimiEngine

# 初始化引擎（使用默认配置）
engine = KimiEngine()

# 简单的测试
response = engine.chat("你好，我是谁？")
print(response)
```

如果一切正常，你应该能看到一个生成的回复。

## 常见问题

### 1. CUDA支持

如果你打算使用GPU加速本地模型，确保已正确安装CUDA和PyTorch的CUDA版本：

```bash
# 例如，对于CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 2. Apple Silicon (M1/M2) 支持

在Apple Silicon设备上，建议使用MPS进行加速：

```python
engine = KimiEngine(llm_config={"device": "mps"})
```

### 3. 依赖冲突

如果遇到依赖冲突，建议使用虚拟环境：

```bash
python -m venv openkimi-env
source openkimi-env/bin/activate  # Linux/macOS
# 或
openkimi-env\Scripts\activate  # Windows
```

## 下一步

安装完成后，建议查看[快速入门指南](getting_started.md)来了解如何使用OpenKimi的基本功能。 