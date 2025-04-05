"""
解决方案框架生成相关的 prompt 模板
"""

GENERATE_FRAMEWORK = """请为以下问题生成一个解决框架，列出解决问题的关键步骤：

问题: {query}

{context_section}

请列出解决这个问题的思路框架，格式如下:
1. 第一步...
2. 第二步...
...

解决框架:"""

GENERATE_SOLUTION = """请根据以下框架回答用户的问题:

用户问题: {query}

解决框架:
{framework}

{useful_context_section}

{rag_context_section}

请根据框架和上下文生成完整的解决方案："""

# 上下文部分模板
CONTEXT_SECTION = """
相关上下文:
{context}
"""

USEFUL_CONTEXT_SECTION = """
主要上下文:
{useful_context}
"""

RAG_CONTEXT_SECTION = """额外上下文信息:
{rag_contexts}
""" 