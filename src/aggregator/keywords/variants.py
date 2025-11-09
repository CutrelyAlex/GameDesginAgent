"""
Keyword variant generator using LLM.

Generates multiple variations of search keywords to improve recall
across different search providers.
"""

import logging
import re
from typing import List, Optional

from src.aggregator.schemas import KeywordVariant
from src.aggregator.llm import LLMClient

logger = logging.getLogger(__name__)


class KeywordVariantGenerator:
    """
    Generate keyword variants using LLM for improved search recall.
    
    Generates variations like:
    - More humanized/natural language versions
    - More professional/technical versions
    - Long-tail keyword expansions
    """
    
    VARIANT_PROMPT_TEMPLATE = """给定关键词: "{keyword}"

请生成 6 个不同角度的关键词变体，用于提高搜索引擎的召回率。包括：
1. 人性化表达（更自然、口语化）
2. 专业术语表达
3. 长尾关键词（更具体、详细）
4. 相关领域术语
5. 同义词或近义词
6. 疑问句形式

这是一个工具流，只返回关键词列表，每行一个，禁止编号，禁止解释。

变体："""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize keyword variant generator.
        
        Args:
            llm_client: LLM client instance (will create default if None)
        """
        self.llm_client = llm_client
        self._llm_available = None
    
    async def _ensure_llm_client(self) -> LLMClient:
        """Ensure LLM client is initialized."""
        if self.llm_client is None:
            try:
                self.llm_client = LLMClient()
            except ValueError as e:
                logger.error(f"Cannot initialize LLM client: {e}")
                raise RuntimeError(
                    "LLM client not configured. Set SMALL_LLM_URL in .env. "
                    "Example: SMALL_LLM_URL=http://localhost:11434 for Ollama"
                ) from e
        return self.llm_client
    
    async def generate_variants(
        self,
        keyword: str,
        max_variants: int = 6
    ) -> List[KeywordVariant]:
        """
        Generate keyword variants using LLM.
        
        Args:
            keyword: Original keyword
            max_variants: Maximum number of variants to generate (default: 6)
            
        Returns:
            List of KeywordVariant objects
            
        Raises:
            RuntimeError: If LLM is not configured or fails
        """
        llm_client = await self._ensure_llm_client()
        
        # Generate prompt
        prompt = self.VARIANT_PROMPT_TEMPLATE.format(keyword=keyword)
        
        try:
            # Get LLM response
            response = await llm_client.generate_completion(prompt)
            
            # Parse variants from response
            variants = self._parse_variants(response, keyword, max_variants)
            
            if not variants:
                logger.warning(f"No variants generated for keyword: {keyword}")
                # Return original keyword as fallback
                return [KeywordVariant(
                    original=keyword,
                    variant=keyword,
                    variant_type="original"
                )]
            
            logger.info(f"Generated {len(variants)} variants for: {keyword}")
            return variants
            
        except Exception as e:
            logger.error(f"Failed to generate variants for '{keyword}': {e}")
            # Return original keyword as fallback
            return [KeywordVariant(
                original=keyword,
                variant=keyword,
                variant_type="original"
            )]
    
    def _parse_variants(
        self,
        response: str,
        original_keyword: str,
        max_variants: int
    ) -> List[KeywordVariant]:
        """
        Parse variants from LLM response.
        
        Args:
            response: Raw LLM response text
            original_keyword: Original keyword
            max_variants: Maximum variants to return
            
        Returns:
            List of KeywordVariant objects
        """
        variants = []
        
        # Split by newlines and clean
        lines = response.strip().split('\n')
        
        for line in lines:
            # Skip empty lines
            line = line.strip()
            if not line:
                continue
            
            # Remove numbering (1., 2., -, *, etc.)
            line = re.sub(r'^[\d\-\*\•\.]+\s*', '', line)
            line = line.strip()
            
            # Skip if too short or same as original
            if len(line) < 2 or line == original_keyword:
                continue
            
            # Detect variant type from position (simple heuristic)
            variant_type = self._infer_variant_type(len(variants))
            
            variants.append(KeywordVariant(
                original=original_keyword,
                variant=line,
                variant_type=variant_type
            ))
            
            # Stop if we have enough variants
            if len(variants) >= max_variants:
                break
        
        return variants
    
    def _infer_variant_type(self, index: int) -> str:
        """
        Infer variant type from its position in the list.
        
        Args:
            index: Position index (0-based)
            
        Returns:
            Variant type string
        """
        types = [
            "humanized",      # 0: More natural/conversational
            "professional",   # 1: Technical/professional
            "long-tail",      # 2: More specific/detailed
            "related",        # 3: Related domain terms
            "synonym",        # 4: Synonym/near-synonym
            "question"        # 5: Question form
        ]
        
        if index < len(types):
            return types[index]
        return f"variant-{index + 1}"


async def generate_variants_for_keywords(
    keywords: List[str],
    llm_client: Optional[LLMClient] = None
) -> List[str]:
    """
    Generate variants for multiple keywords and flatten to unique list.
    
    Args:
        keywords: List of original keywords
        llm_client: Optional LLM client instance
        
    Returns:
        Flattened list of unique keywords (originals + variants)
    """
    generator = KeywordVariantGenerator(llm_client)
    
    all_keywords = set(keywords)  # Start with originals
    
    for keyword in keywords:
        try:
            variants = await generator.generate_variants(keyword)
            for variant in variants:
                all_keywords.add(variant.variant)
        except Exception as e:
            logger.error(f"Failed to generate variants for '{keyword}': {e}")
            # Continue with other keywords
    
    return list(all_keywords)
