import uuid
from typing import List, Set, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from backend.app.adapters.models.graph_node_model import GraphNodeModel
from backend.app.adapters.models.graph_edge_model import GraphEdgeModel

class GraphTraversal:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def expand_graph(
        self,
        snapshot_id: str,
        initial_node_ids: List[str],
        max_depth: int = 1
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Expand the context graph starting from the initial semantic matches.
        Traverses nodes up to max_depth and returns a tuple (nodes, edges).
        """
        if not initial_node_ids:
            return [], []
            
        sid = uuid.UUID(snapshot_id)
        visited_nodes: Set[str] = set(initial_node_ids)
        traversed_edges: List[GraphEdgeModel] = []
        
        current_level = set(initial_node_ids)
        
        # Load all edges for this snapshot once to do fast traversal in memory
        res_edges = await self.db.execute(
            select(GraphEdgeModel).filter(GraphEdgeModel.snapshot_id == sid)
        )
        all_edges = list(res_edges.scalars().all())
        
        # BFS traversal
        for _ in range(max_depth):
            next_level = set()
            for edge in all_edges:
                src = str(edge.source_node_id)
                tgt = str(edge.target_node_id)
                
                if src in current_level and tgt not in visited_nodes:
                    visited_nodes.add(tgt)
                    next_level.add(tgt)
                    traversed_edges.append(edge)
                elif tgt in current_level and src not in visited_nodes:
                    visited_nodes.add(src)
                    next_level.add(src)
                    traversed_edges.append(edge)
                elif src in current_level or tgt in current_level:
                    # If both already visited but edge not tracked, record it
                    if edge not in traversed_edges:
                        traversed_edges.append(edge)
                        
            current_level = next_level
            if not current_level:
                break
                
        # Fetch node details
        visited_uuids = [uuid.UUID(nid) for nid in visited_nodes]
        nodes_details = []
        if visited_uuids:
            res_nodes = await self.db.execute(
                select(GraphNodeModel).filter(GraphNodeModel.id.in_(visited_uuids))
            )
            for node in res_nodes.scalars().all():
                nodes_details.append({
                    "id": str(node.id),
                    "snapshot_id": str(node.snapshot_id),
                    "entity_id": str(node.entity_id) if node.entity_id else None,
                    "name": node.name,
                    "type": node.type,
                    "properties": node.properties
                })
                
        edges_details = [{
            "id": str(e.id),
            "source_node_id": str(e.source_node_id),
            "target_node_id": str(e.target_node_id),
            "type": e.type,
            "properties": e.properties
        } for e in traversed_edges]
        
        return nodes_details, edges_details
