import asyncio
import logging
from typing import Dict, Any, List, Optional
from backend.app.gateway.provider_factory import ProviderFactory
from backend.app.gateway.model_router import ModelRouter

logger = logging.getLogger("codeatlas.gateway")


class AIGateway:
    """
    Main interface wrapper managing retry orchestration, backoff retry limits,
    cost logging trackers, and structured formatting schemas.
    """

    def __init__(self, default_provider: str = "gemini"):
        self.default_provider = default_provider
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    def estimate_tokens(self, text: str) -> int:
        """
        Character-based heuristic token calculator (1 token ~= 4 characters).
        """
        if not text:
            return 0
        return max(1, len(text) // 4)

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int, model_name: str) -> float:
        """
        Estimates API execution costs based on token metrics.
        - gemini-1.5-pro: $1.25 / 1M input, $5.00 / 1M output tokens (approx pricing)
        - gemini-1.5-flash: $0.075 / 1M input, $0.30 / 1M output tokens
        """
        model = model_name.lower()
        if "pro" in model:
            inp_rate = 1.25 / 1_000_000
            out_rate = 5.00 / 1_000_000
        else:
            inp_rate = 0.075 / 1_000_000
            out_rate = 0.30 / 1_000_000

        return (prompt_tokens * inp_rate) + (completion_tokens * out_rate)

    async def generate(
        self,
        prompt: str,
        task_type: str = "general",
        system_instruction: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Dispatches completion content with exponential retry backoffs.
        """
        model_name = ModelRouter.route_task(task_type)
        provider = ProviderFactory.get_provider(self.default_provider, model_name)
        
        attempt = 0
        delay = 1.0

        while attempt < max_retries:
            try:
                attempt += 1
                res = await provider.generate_content(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    tools=tools,
                    temperature=temperature
                )
                
                # Accumulate metrics
                p_tok = res.get("prompt_tokens", 0) or self.estimate_tokens(prompt)
                c_tok = res.get("completion_tokens", 0) or self.estimate_tokens(res.get("text", ""))
                
                self.total_prompt_tokens += p_tok
                self.total_completion_tokens += c_tok
                
                cost = self.calculate_cost(p_tok, c_tok, model_name)
                logger.info(
                    f"Gateway call succeeded on attempt {attempt}. "
                    f"Model: {model_name}. Tokens: {p_tok} input, {c_tok} output. Est Cost: ${cost:.6f}"
                )
                
                return {
                    "text": res.get("text", ""),
                    "tool_calls": res.get("tool_calls", []),
                    "prompt_tokens": p_tok,
                    "completion_tokens": c_tok,
                    "cost": cost,
                    "model": model_name
                }
            except Exception as e:
                logger.warning(f"Gateway request failed on attempt {attempt}: {str(e)}")
                if attempt >= max_retries:
                    raise Exception(f"AIGateway call exhausted all {max_retries} retries. Error: {str(e)}")
                
                await asyncio.sleep(delay)
                delay *= backoff_factor

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        task_type: str = "general",
        system_instruction: Optional[str] = None,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Dispatches structured queries requiring JSON output conforming to target schema.
        """
        model_name = ModelRouter.route_task(task_type)
        provider = ProviderFactory.get_provider(self.default_provider, model_name)

        attempt = 0
        delay = 1.0

        while attempt < max_retries:
            try:
                attempt += 1
                res = await provider.generate_structured_output(
                    prompt=prompt,
                    response_schema=response_schema,
                    system_instruction=system_instruction,
                    temperature=temperature
                )
                
                p_tok = res.get("prompt_tokens", 0) or self.estimate_tokens(prompt)
                c_tok = res.get("completion_tokens", 0) or 100
                
                self.total_prompt_tokens += p_tok
                self.total_completion_tokens += c_tok
                
                cost = self.calculate_cost(p_tok, c_tok, model_name)
                logger.info(
                    f"Gateway structured call succeeded on attempt {attempt}. "
                    f"Model: {model_name}. Tokens: {p_tok} input, {c_tok} output. Est Cost: ${cost:.6f}"
                )
                
                return {
                    "data": res.get("data", {}),
                    "prompt_tokens": p_tok,
                    "completion_tokens": c_tok,
                    "cost": cost,
                    "model": model_name
                }
            except Exception as e:
                logger.warning(f"Gateway structured request failed on attempt {attempt}: {str(e)}")
                if attempt >= max_retries:
                    raise Exception(f"AIGateway structured call exhausted all {max_retries} retries. Error: {str(e)}")
                
                await asyncio.sleep(delay)
                delay *= backoff_factor
