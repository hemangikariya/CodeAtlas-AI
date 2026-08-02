import json
import logging
from typing import Dict, Any, List
from backend.app.gateway.ai_gateway import AIGateway
from backend.app.prompts.prompt_registry import prompt_registry

logger = logging.getLogger("codeatlas.agents")


class ResponseSynthesizer:
    """
    ResponseSynthesizer aggregates intermediate results from specialized agents,
    deduplicates recommendations, maintains citations, and formats the final AI response.
    """

    def __init__(self, gateway: AIGateway):
        self.gateway = gateway

    async def synthesize(self, query: str, plan: Dict[str, Any], agent_outputs: List[Dict[str, Any]]) -> str:
        """
        Synthesizes agent logs into unified report.
        """
        logger.info(f"Synthesizer starting compilation for query: '{query}'")

        # Format outputs of specialized agents for LLM context injection
        formatted_outputs = []
        for out in agent_outputs:
            formatted_outputs.append(
                f"--- Agent: {out.get('agent')} ---\n"
                f"Report:\n{out.get('report')}\n"
            )
        agent_outputs_str = "\n".join(formatted_outputs)
        plan_json_str = json.dumps(plan, indent=2)

        prompt = prompt_registry.get_prompt(
            "response_synthesizer",
            query=query,
            plan=plan_json_str,
            agent_outputs=agent_outputs_str
        )

        try:
            res = await self.gateway.generate(
                prompt=prompt,
                task_type="synthesis",
                system_instruction="You are the final Response Synthesizer compiling multiple audits."
            )
            final_text = res.get("text", "")
            logger.info("Successfully synthesized final AI response.")
            return final_text
        except Exception as e:
            logger.error(f"Response synthesis failed: {str(e)}. Defaulting to raw reports aggregation.")
            # Fallback simple aggregation
            fallback = f"# CodeAtlas AI Audit Report\n\nQuery: {query}\n\n"
            for out in agent_outputs:
                fallback += f"## {out.get('agent')} Findings\n{out.get('report')}\n\n"
            return fallback
