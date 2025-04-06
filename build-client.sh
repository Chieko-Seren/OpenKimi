#!/bin/bash

# OpenKimi客户端构建脚本
# 使用: ./build-client.sh [windows|linux|macos|all]

# 如果scripts目录不存在，则输出错误信息并退出
if [ ! -d "scripts" ]; then
  echo "❌ 错误: 找不到scripts目录"
  exit 1
fi

# 检查是否安装了Rust
if ! command -v cargo &> /dev/null; then
  echo "❌ 错误: 未安装Rust，请访问 https://rustup.rs/ 安装Rust工具链"
  exit 1
fi

# 进入scripts目录并编译Rust项目
cd scripts
cargo build --release

if [ $? -ne 0 ]; then
  echo "❌ 错误: Rust编译失败，请检查错误信息"
  exit 1
fi

# 获取参数
PLATFORM=${1:-all}

# 运行编译后的二进制文件
./target/release/build-client "$PLATFORM" 