from typing import List, Dict, Any

class ContextBuilder:
    @staticmethod
    def build_context(
        ranked_chunks: List[Dict[str, Any]],
        token_limit: int = 4000
    ) -> str:
        """
        Deduplicates, assembles, and formats ranked code chunks into a structured prompt context
        while respecting a strict token budget.
        
        Token estimation is calculated using 4 characters per token as a conservative baseline.
        """
        if not ranked_chunks:
            return "No relevant context found."

        seen_chunk_ids = set()
        context_parts = []
        current_token_count = 0

        # Header for the context block
        header = "=== RETRIEVED REPOSITORY CONTEXT ===\n\n"
        current_token_count += len(header) // 4

        for chunk in ranked_chunks:
            chunk_id = chunk.get("id")
            if chunk_id in seen_chunk_ids:
                continue

            # Format the chunk representation
            file_path = chunk.get("file_path", "unknown")
            chunk_type = chunk.get("type", "CODE")
            name = chunk.get("name", "anonymous")
            start = chunk.get("start_line", 0)
            end = chunk.get("end_line", 0)
            content = chunk.get("content", "")

            chunk_repr = (
                f"--- CHUNK ---\n"
                f"File: {file_path}\n"
                f"Type: {chunk_type}\n"
                f"Symbol: {name}\n"
                f"Lines: {start}-{end}\n"
                f"Content:\n{content}\n\n"
            )

            chunk_tokens = len(chunk_repr) // 4
            
            # Check budget constraints
            if current_token_count + chunk_tokens > token_limit:
                # If adding this exceeds the limit, stop
                break

            seen_chunk_ids.add(chunk_id)
            context_parts.append(chunk_repr)
            current_token_count += chunk_tokens

        if not context_parts:
            return "No context within token limit."

        return header + "".join(context_parts)
