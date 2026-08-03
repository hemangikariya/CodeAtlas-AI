import json
import httpx
from typing import Dict, Any, List, Optional
from backend.app.core.config import settings
from backend.app.gateway.base_provider import BaseProvider


class GeminiProvider(BaseProvider):
    """
    Google Gemini provider connecting via HTTP REST services.
    Includes fallback mock behavior for offline testing and when api key is absent.
    """

    def __init__(self, api_key: str = "", model_name: str = "gemini-1.5-pro", use_mock: Optional[bool] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name
        self.use_mock = use_mock if use_mock is not None else (settings.ENVIRONMENT == "testing" or not self.api_key)
        self.endpoint_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

    async def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        if self.use_mock:
            return self._mock_generate_content(prompt, system_instruction, tools)

        # 1. Map contents
        contents = [{"parts": [{"text": prompt}]}]
        payload: Dict[str, Any] = {"contents": contents}

        # 2. Add system instructions
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        # 3. Add generation config
        payload["generationConfig"] = {"temperature": temperature}

        # 4. Add tools declaration in Gemini format
        if tools:
            # Format MCP tools into Gemini function declarations
            declarations = []
            for t in tools:
                declarations.append({
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t.get("parameters", {"type": "OBJECT", "properties": {}})
                })
            payload["tools"] = [{"functionDeclarations": declarations}]

        # 5. Execute API Call
        url = f"{self.endpoint_url}?key={self.api_key}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise Exception(f"Gemini API failure (status {resp.status_code}): {resp.text}")
            
            data = resp.json()
            return self._parse_gemini_response(data)

    async def generate_structured_output(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        system_instruction: Optional[str] = None,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        if self.use_mock:
            return self._mock_generate_structured(prompt, response_schema)

        contents = [{"parts": [{"text": prompt}]}]
        payload: Dict[str, Any] = {"contents": contents}

        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        # Configure Gemini generation config for structured output
        payload["generationConfig"] = {
            "temperature": temperature,
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }

        url = f"{self.endpoint_url}?key={self.api_key}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise Exception(f"Gemini Structured API failure (status {resp.status_code}): {resp.text}")
            
            data = resp.json()
            parsed = self._parse_gemini_response(data)
            
            # Load structured JSON data
            try:
                structured_data = json.loads(parsed["text"])
                return {"data": structured_data, "prompt_tokens": parsed["prompt_tokens"], "completion_tokens": parsed["completion_tokens"]}
            except Exception as e:
                raise ValueError(f"Failed to parse structured output: {str(e)}. Original text: {parsed['text']}")

    def _parse_gemini_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        candidates = data.get("candidates", [])
        if not candidates:
            return {"text": "", "tool_calls": [], "prompt_tokens": 0, "completion_tokens": 0}

        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        
        text = ""
        tool_calls = []

        for part in parts:
            if "text" in part:
                text += part["text"]
            elif "functionCall" in part:
                func_call = part["functionCall"]
                tool_calls.append({
                    "name": func_call.get("name"),
                    "arguments": func_call.get("args", {})
                })

        # Token metrics extraction
        usage = data.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", 0)
        completion_tokens = usage.get("candidatesTokenCount", 0)

        return {
            "text": text,
            "tool_calls": tool_calls,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens
        }

    # --- Offline Testing Mocks ---

    def _mock_generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Mock text completion generator for isolated testing.
        """
        text = "Mocked Response text."
        tool_calls = []

        # If tools are provided, let's simulate calling one of them if the prompt invites search
        if tools and ("search" in prompt.lower() or "find" in prompt.lower() or "read" in prompt.lower()):
            tool_calls.append({
                "name": tools[0]["name"],
                "arguments": {
                    "query": "evaluate",
                    "path": "math_utils.py",
                    "top_k": 3
                }
            })
            text = "" # Tool recommendations return empty texts typically
        elif "synthesizer" in (system_instruction or "").lower():
            text = "### Unified Analysis Report\n- **Verification**: Verified successfully.\n- **Results**: Code exhibits clean SOLID designs."

        return {
            "text": text,
            "tool_calls": tool_calls,
            "prompt_tokens": len(prompt) // 4,
            "completion_tokens": len(text) // 4
        }

    def _mock_generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock structured output generator validating targeting schemas.
        """
        # Determine target mock data by checking schema properties
        props = schema.get("properties", {})
        
        # 1. Safety Guardrail mock schema
        if "is_safe" in props:
            mock_data = {
                "is_safe": True,
                "reason": "Request is completely benign.",
                "confidence": 0.99
            }
            # Check if prompt content contains unsafe markers by extracting the query content
            import re
            lower_prompt = prompt.lower()
            match = re.search(r"content to analyze:\n\"(.*?)\"", lower_prompt, re.DOTALL)
            content_part = match.group(1) if match else lower_prompt

            if "ignore all" in content_part or "system override" in content_part or "rm -rf /" in content_part:
                mock_data["is_safe"] = False
                mock_data["reason"] = "Malicious pattern or dangerous command detected."
        
        # 2. Planner execution tasks mock schema
        elif "tasks" in props:
            # Match prompt intent to build plan
            intent = "repository_analysis"
            agent = "RepositoryAgent"
            tool = "RepositorySearch"
            
            if "security" in prompt.lower():
                intent = "security_audit"
                agent = "SecurityAgent"
                tool = "FileReader"
            elif "architecture" in prompt.lower() or "depend" in prompt.lower():
                intent = "architecture_analysis"
                agent = "ArchitectureAgent"
                tool = "DependencyLookup"
            elif "documentation" in prompt.lower():
                intent = "documentation_review"
                agent = "DocumentationAgent"
                tool = "ContextBuilder"
                
            mock_data = {
                "intent": intent,
                "complexity": "medium",
                "tasks": [
                    {
                        "agent": agent,
                        "tool": tool,
                        "priority": 1
                    }
                ]
            }
        
        # 3. Agent execution result validation schema
        elif "is_valid" in props:
            mock_data = {
                "is_valid": True,
                "sanitized_output": "Sanitized content here."
            }
        
        # 4. Copilot Structured Artifact schema
        elif "sections" in props:
            mock_data = {
                "title": "Mocked Copilot Engineering Artifact",
                "summary": "This is a mocked high-fidelity engineering document output.",
                "sections": [
                    {
                        "heading": "Introduction",
                        "content": "This is a detailed analysis section from the CodeAtlas Copilot."
                    },
                    {
                        "heading": "Core Analysis Details",
                        "content": "Specific observations, component interactions, and file audits."
                    }
                ],
                "references": ["math_utils.py", "main.py"],
                "generator": "RepositoryExplainer",
                "generator_version": "1.0",
                "prompt_version": "1.0",
                "knowledge_snapshot": "snap-123",
                "artifact_version": "1.0",
                "created_at": "2026-08-03T12:00:00Z"
            }
        
        # 4. Standard properties fallback
        else:
            mock_data = {}
            for name, val in props.items():
                t = val.get("type", "string")
                if t == "boolean":
                    mock_data[name] = True
                elif t == "array":
                    mock_data[name] = []
                elif t == "integer" or t == "number":
                    mock_data[name] = 1
                else:
                    mock_data[name] = "Mock text"

        return {
            "data": mock_data,
            "prompt_tokens": len(prompt) // 4,
            "completion_tokens": 40
        }
