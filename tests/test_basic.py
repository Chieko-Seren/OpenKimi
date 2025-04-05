#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from openkimi import KimiEngine
from openkimi.core import TextProcessor, RAGManager, FrameworkGenerator
from openkimi.utils.llm_interface import DummyLLM

class TestTextProcessor(unittest.TestCase):
    """文本处理器测试"""
    
    def setUp(self):
        self.processor = TextProcessor(batch_size=10)
        
    def test_split_into_batches(self):
        text = "这是一个测试文本，用于测试分块功能。"
        batches = self.processor.split_into_batches(text)
        self.assertGreater(len(batches), 0)
        
    def test_calculate_entropy(self):
        text1 = "aaaaaaaaaa"  # 低熵
        text2 = "abcdefghij"  # 高熵
        
        entropy1 = self.processor.calculate_entropy(text1)
        entropy2 = self.processor.calculate_entropy(text2)
        
        self.assertLess(entropy1, entropy2)
        
    def test_classify_by_entropy(self):
        batches = ["aaaaaaaaaa", "abcdefghij"]
        useful, less_useful = self.processor.classify_by_entropy(batches, threshold=2.0)
        
        self.assertEqual(len(useful) + len(less_useful), 2)

class TestRAGManager(unittest.TestCase):
    """RAG管理器测试"""
    
    def setUp(self):
        self.llm = DummyLLM()
        self.rag = RAGManager(self.llm)
        
    def test_store_and_retrieve(self):
        text = "这是需要存储的测试文本。"
        summary = self.rag.store_text(text)
        
        results = self.rag.retrieve("测试文本")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], text)

class TestFrameworkGenerator(unittest.TestCase):
    """框架生成器测试"""
    
    def setUp(self):
        self.llm = DummyLLM()
        self.framework_gen = FrameworkGenerator(self.llm)
        
    def test_generate_framework(self):
        query = "如何解决这个框架问题？"
        framework = self.framework_gen.generate_framework(query)
        self.assertIsNotNone(framework)
        
    def test_generate_solution(self):
        query = "如何解决这个问题？"
        framework = "1. 步骤一\n2. 步骤二"
        solution = self.framework_gen.generate_solution(query, framework)
        self.assertIsNotNone(solution)

class TestKimiEngine(unittest.TestCase):
    """Kimi引擎集成测试"""
    
    def setUp(self):
        self.engine = KimiEngine()
        
    def test_ingest_and_chat(self):
        text = "这是一个测试文本，用于测试Kimi引擎的摄入和对话功能。"
        self.engine.ingest(text)
        
        response = self.engine.chat("这个文本是关于什么的？")
        self.assertIsNotNone(response)
        
if __name__ == "__main__":
    unittest.main() 