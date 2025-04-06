#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
🧪 FAISS消融实验：对比使用FAISS和不使用FAISS的向量检索性能
"""

import os
import sys
import time
import argparse
import numpy as np
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from openkimi.core import RAGManager
from openkimi.utils.llm_interface import DummyLLM

def generate_random_texts(num_texts, min_words=10, max_words=100):
    """生成随机文本用于测试"""
    vocab = ["人工智能", "机器学习", "深度学习", "自然语言处理", "计算机视觉", 
             "强化学习", "神经网络", "卷积神经网络", "循环神经网络", "变换器模型",
             "注意力机制", "知识图谱", "语义分析", "情感分析", "实体识别",
             "文本分类", "图像识别", "语音识别", "推荐系统", "无监督学习", 
             "MyGO!!!!!", "千早爱音", "长崎素世", "爱素99", "迷途之子", "Loss梯度也无所谓、在迷茫中拟合吧！"
             ,"加入月之森女子学院计算技术研究所谢谢喵", "QQ群号735511657"]
    
    texts = []
    for _ in range(num_texts):
        length = np.random.randint(min_words, max_words + 1)
        words = np.random.choice(vocab, size=length)
        text = "".join([word + ("，" if i < length - 1 else "。") for i, word in enumerate(words)])
        texts.append(text)
    return texts

def run_benchmark(num_texts=1000, num_queries=100, use_faiss=True):
    """运行基准测试"""
    logger.info(f"开始基准测试: {num_texts}个文本, {num_queries}个查询, FAISS={'启用' if use_faiss else '禁用'}")
    
    # 初始化LLM和RAG
    llm = DummyLLM()
    rag = RAGManager(llm, use_faiss=use_faiss)
    
    # 生成测试数据
    logger.info("生成测试文本...")
    texts = generate_random_texts(num_texts)
    
    # 测量存储时间
    logger.info("开始测量存储性能...")
    start_time = time.time()
    rag.batch_store(texts)
    store_time = time.time() - start_time
    logger.info(f"存储{num_texts}个文本耗时: {store_time:.4f}秒")
    
    # 生成查询
    logger.info("生成测试查询...")
    queries = generate_random_texts(num_queries, min_words=3, max_words=10)
    
    # 测量检索时间
    logger.info("开始测量检索性能...")
    start_time = time.time()
    for query in queries:
        results = rag.retrieve(query, top_k=5)
    retrieve_time = time.time() - start_time
    logger.info(f"执行{num_queries}次查询耗时: {retrieve_time:.4f}秒, 平均每次查询: {retrieve_time/num_queries*1000:.2f}毫秒")
    
    return {
        "num_texts": num_texts,
        "num_queries": num_queries,
        "use_faiss": use_faiss,
        "store_time": store_time,
        "retrieve_time": retrieve_time,
        "avg_query_time": retrieve_time / num_queries
    }

def main():
    parser = argparse.ArgumentParser(description="FAISS性能基准测试")
    parser.add_argument("--texts", type=int, default=1000, help="测试文本数量")
    parser.add_argument("--queries", type=int, default=100, help="测试查询数量")
    args = parser.parse_args()
    
    # 运行不使用FAISS的基准测试
    no_faiss_results = run_benchmark(args.texts, args.queries, use_faiss=False)
    
    # 运行使用FAISS的基准测试
    faiss_results = run_benchmark(args.texts, args.queries, use_faiss=True)
    
    # 比较结果
    store_speedup = no_faiss_results["store_time"] / faiss_results["store_time"] if faiss_results["store_time"] > 0 else float('inf')
    retrieve_speedup = no_faiss_results["retrieve_time"] / faiss_results["retrieve_time"] if faiss_results["retrieve_time"] > 0 else float('inf')
    
    print("\n========== 消融实验结果 ==========")
    print(f"文本数量: {args.texts}, 查询数量: {args.queries}")
    print("\n存储性能:")
    print(f"  不使用FAISS: {no_faiss_results['store_time']:.4f}秒")
    print(f"  使用FAISS:   {faiss_results['store_time']:.4f}秒")
    print(f"  加速比:      {store_speedup:.2f}x")
    
    print("\n检索性能:")
    print(f"  不使用FAISS: {no_faiss_results['retrieve_time']:.4f}秒 (平均每次查询: {no_faiss_results['avg_query_time']*1000:.2f}毫秒)")
    print(f"  使用FAISS:   {faiss_results['retrieve_time']:.4f}秒 (平均每次查询: {faiss_results['avg_query_time']*1000:.2f}毫秒)")
    print(f"  加速比:      {retrieve_speedup:.2f}x")
    print("\n注意: 使用FAISS的优势在数据量更大时更为明显")

if __name__ == "__main__":
    main() 