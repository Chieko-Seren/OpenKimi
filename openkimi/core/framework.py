from typing import List, Dict, Any
from openkimi.utils.llm_interface import LLMInterface
from openkimi.utils.prompt_loader import load_prompt

class FrameworkGenerator:
    
    def __init__(self, llm_interface: LLMInterface):
        """
        初始化框架生成器
        
        Args:
            llm_interface: LLM接口，用于生成框架
        """
        self.llm_interface = llm_interface
        self.framework_prompt_template = load_prompt('generate_framework')
        self.solution_prompt_template = load_prompt('generate_solution')
        self.mcp_synthesize_prompt_template = load_prompt('synthesize_solutions_mcp')

    def _format_context_section(self, title: str, content: str) -> str:
        """Helper to format optional context sections for prompts"""
        if not content:
            return ""
        return f"{title}:\n{content}\n\n"

    def generate_framework(self, query: str, context: str = "") -> str:
        """
        生成解决问题的思路框架
        
        Args:
            query: 用户的问题
            context: 相关上下文（可选）
            
        Returns:
            问题解决框架
        """
        optional_context = self._format_context_section("相关上下文", context)
        # Todo: Add recursive RAG logic if context is too long
        prompt = self.framework_prompt_template.format(
            query=query, 
            optional_context_section=optional_context
        )
        
        # 调用LLM生成框架
        framework = self.llm_interface.generate(prompt)
        return framework
    
    def _generate_single_solution(self, query: str, framework: str, useful_context: str = "", rag_context: List[str] = None) -> str:
        """Generates one solution based on the framework and context."""
        optional_useful_ctx = self._format_context_section("主要上下文", useful_context)
        rag_text = ""
        if rag_context and len(rag_context) > 0:
            rag_items = []
            for i, ctx in enumerate(rag_context, 1):
                rag_items.append(f"{i}. {ctx}")
            rag_text = "\n".join(rag_items)
        optional_rag_ctx = self._format_context_section("额外上下文信息", rag_text)

        # Todo: Add recursive RAG logic if combined context is too long
        prompt = self.solution_prompt_template.format(
            query=query,
            framework=framework,
            optional_useful_context_section=optional_useful_ctx,
            optional_rag_context_section=optional_rag_ctx
        )
        
        # 调用LLM生成解决方案
        solution = self.llm_interface.generate(prompt)
        return solution
        
    def generate_solution_mcp(self, query: str, framework: str, useful_context: str = "", rag_context: List[str] = None, num_candidates: int = 3) -> str:
        """
        使用 MCP 生成解决方案
        
        Args:
            query: 用户的问题
            framework: 解决问题的框架
            useful_context: 主要上下文
            rag_context: 从RAG检索的上下文列表
            num_candidates: 生成候选方案的数量
            
        Returns:
            最终合成的解决方案
        """
        candidate_solutions = []
        # Todo: Implement smarter context variations for MCP
        for _ in range(num_candidates):
            # Simple approach: Use the same context for all candidates for now
            candidate = self._generate_single_solution(query, framework, useful_context, rag_context)
            candidate_solutions.append(candidate)
            
        if num_candidates == 1:
            return candidate_solutions[0]
        
        # Synthesize solutions
        candidates_text = ""
        for i, sol in enumerate(candidate_solutions, 1):
            candidates_text += f"候选方案 {i}:\n{sol}\n\n"
            
        # Todo: Add recursive RAG logic if combined candidates are too long
        synthesize_prompt = self.mcp_synthesize_prompt_template.format(
            query=query,
            candidate_solutions=candidates_text.strip()
        )
        
        final_solution = self.llm_interface.generate(synthesize_prompt)
        return final_solution 