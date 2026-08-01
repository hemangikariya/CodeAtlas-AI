from typing import List, Dict, Any, Tuple
import re

class RankingEngine:
    @staticmethod
    def rank_chunks(
        chunks_with_scores: List[Tuple[Dict[str, Any], float]],
        query: str,
        graph_nodes: List[Dict[str, Any]] = None,
        graph_edges: List[Dict[str, Any]] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Ranks and prioritizes code chunks using similarity scores, graph metrics, and metadata boosts.
        Returns a sorted list of Tuples (chunk_dict, final_score).
        """
        if not chunks_with_scores:
            return []

        ranked_results: List[Tuple[Dict[str, Any], float]] = []
        query_lower = query.lower()

        # 1. Gather graph connectivity context if available
        # Find which nodes are highly connected (hubs)
        node_degrees: Dict[str, int] = {}
        if graph_edges:
            for edge in graph_edges:
                src = edge.get("source_node_id")
                tgt = edge.get("target_node_id")
                if src:
                    node_degrees[src] = node_degrees.get(src, 0) + 1
                if tgt:
                    node_degrees[tgt] = node_degrees.get(tgt, 0) + 1

        # 2. Iterate and score each chunk
        for chunk, sim_score in chunks_with_scores:
            final_score = sim_score
            
            # Metadata boost A: Match query terms with chunk names
            chunk_name = chunk.get("name", "").lower()
            if chunk_name and chunk_name in query_lower:
                final_score += 0.15 # Direct name match boost
                
            # Metadata boost B: Query keyword mapping (e.g. "class", "test", "router")
            chunk_type = chunk.get("type", "").lower()
            if "class" in query_lower and chunk_type == "class":
                final_score += 0.10
            elif "function" in query_lower and chunk_type == "function":
                final_score += 0.08
            elif "method" in query_lower and chunk_type == "method":
                final_score += 0.05
                
            # Metadata boost C: Path matching (e.g., query includes filename or extension)
            file_path = chunk.get("file_path", "").lower()
            if file_path:
                path_segments = re.split(r'[\\/]', file_path)
                for segment in path_segments:
                    if segment and segment in query_lower:
                        final_score += 0.12 # Match file or folder name in query
                        break

            # Graph boosting: boost chunks that represent central nodes in the dependency graph
            chunk_id = chunk.get("id")
            # Bridge to graph node
            graph_node = None
            if graph_nodes:
                for node in graph_nodes:
                    if node.get("entity_id") == chunk_id:
                        graph_node = node
                        break
            
            if graph_node:
                node_id = graph_node.get("id")
                degree = node_degrees.get(node_id, 0)
                if degree > 0:
                    # Logarithmic degree scaling to prevent degree domination
                    import math
                    final_score += 0.02 * math.log(degree + 1)

            # Cap score between -1.0 and 2.0
            final_score = max(-1.0, min(2.0, final_score))
            ranked_results.append((chunk, final_score))

        # 3. Sort descending by final score
        ranked_results.sort(key=lambda x: x[1], reverse=True)
        return ranked_results
