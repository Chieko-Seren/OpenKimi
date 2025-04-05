#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OpenKimi长对话示例

此示例展示如何使用OpenKimi处理长文本并进行智能对话。
"""

import os
import sys
import argparse

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from openkimi import KimiEngine

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='OpenKimi长对话示例')
    parser.add_argument('--input', '-i', type=str, default=None, help='输入文本文件路径')
    parser.add_argument('--model', '-m', type=str, default=None, help='模型路径')
    parser.add_argument('--config', '-c', type=str, default=None, help='配置文件路径')
    parser.add_argument('--batch_size', '-b', type=int, default=512, help='文本分块大小')
    args = parser.parse_args()
    
    # 初始化KimiEngine
    print("初始化OpenKimi引擎...")
    engine = KimiEngine(
        config_path=args.config,
        llm=args.model,
        batch_size=args.batch_size
    )
    
    # 处理输入文件
    if args.input:
        print(f"正在处理文件: {args.input}")
        try:
            with open(args.input, 'r', encoding='utf-8') as f:
                text = f.read()
                engine.ingest(text)
            print(f"成功摄入文本，长度: {len(text)} 字符")
        except Exception as e:
            print(f"读取文件失败: {e}")
            return
    
    # 交互式对话
    print("\n===== 开始对话 (输入'exit'退出) =====")
    while True:
        try:
            # 获取用户输入
            user_input = input("\n用户: ")
            if user_input.lower() in ['exit', 'quit', '退出']:
                break
                
            # 生成回复
            response = engine.chat(user_input)
            print(f"\nOpenKimi: {response}")
            
        except KeyboardInterrupt:
            print("\n对话已中断")
            break
        except Exception as e:
            print(f"发生错误: {e}")
    
    print("\n对话结束，感谢使用OpenKimi！")

if __name__ == "__main__":
    main() 