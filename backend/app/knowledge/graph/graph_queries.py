import uuid
from typing import Dict, Any, List, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.app.adapters.models.graph_node_model import GraphNodeModel
from backend.app.adapters.models.graph_edge_model import GraphEdgeModel

class GraphQueries:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_graph_statistics(self, snapshot_id: str) -> Dict[str, Any]:
        sid = uuid.UUID(snapshot_id)
        
        # 1. Total Nodes
        res_nodes = await self.db.execute(select(func.count(GraphNodeModel.id)).filter(GraphNodeModel.snapshot_id == sid))
        total_nodes = res_nodes.scalar() or 0
        
        # 2. Total Edges
        res_edges = await self.db.execute(select(func.count(GraphEdgeModel.id)).filter(GraphEdgeModel.snapshot_id == sid))
        total_edges = res_edges.scalar() or 0
        
        # 3. Average degree
        avg_degree = (total_edges / total_nodes) if total_nodes > 0 else 0.0
        
        # 4. Connected components (disjoint subgraphs)
        # Fetch all edges to walk the graph
        res_all_edges = await self.db.execute(
            select(GraphEdgeModel.source_node_id, GraphEdgeModel.target_node_id)
            .filter(GraphEdgeModel.snapshot_id == sid)
        )
        edges = res_all_edges.all()
        
        res_all_nodes = await self.db.execute(
            select(GraphNodeModel.id).filter(GraphNodeModel.snapshot_id == sid)
        )
        node_ids = {str(n) for n in res_all_nodes.scalars().all()}
        
        connected_components = self._calculate_connected_components(node_ids, edges)
        
        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "average_degree": round(avg_degree, 2),
            "connected_components": connected_components
        }

    def _calculate_connected_components(self, node_ids: Set[str], edges: List[Any]) -> int:
        if not node_ids:
            return 0
            
        # Build adjacency list
        adj: Dict[str, List[str]] = {nid: [] for nid in node_ids}
        for edge in edges:
            src, tgt = str(edge[0]), str(edge[1])
            if src in adj and tgt in adj:
                adj[src].append(tgt)
                adj[tgt].append(src)
                
        visited: Set[str] = set()
        components = 0
        
        for nid in node_ids:
            if nid not in visited:
                components += 1
                # BFS
                queue = [nid]
                visited.add(nid)
                while queue:
                    curr = queue.pop(0)
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                            
        return components
