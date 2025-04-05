"""
OpenKimi prompt 模板模块
==========================

包含系统使用的各种提示词模板
"""

from openkimi.prompts.summarize import SUMMARIZE_TEXT, BATCH_SUMMARIZE
from openkimi.prompts.framework import (
    GENERATE_FRAMEWORK, 
    GENERATE_SOLUTION,
    CONTEXT_SECTION,
    USEFUL_CONTEXT_SECTION,
    RAG_CONTEXT_SECTION
)
from openkimi.prompts.rag import (
    QUERY_EXPANSION,
    RELEVANCE_ASSESSMENT,
    RECURSIVE_RETRIEVAL,
    CONTEXT_COMPRESSION
)

__all__ = [
    "SUMMARIZE_TEXT",
    "BATCH_SUMMARIZE",
    "GENERATE_FRAMEWORK",
    "GENERATE_SOLUTION",
    "CONTEXT_SECTION",
    "USEFUL_CONTEXT_SECTION",
    "RAG_CONTEXT_SECTION",
    "QUERY_EXPANSION",
    "RELEVANCE_ASSESSMENT",
    "RECURSIVE_RETRIEVAL",
    "CONTEXT_COMPRESSION"
] 