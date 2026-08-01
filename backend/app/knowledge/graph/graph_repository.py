import uuid
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from backend.app.adapters.models.graph_node_model import GraphNodeModel
from backend.app.adapters.models.graph_edge_model import GraphEdgeModel

class GraphRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_nodes(self, nodes: List[GraphNodeModel]) -> None:
        for node in nodes:
            self.db.add(node)
        await self.db.flush()

    async def add_edges(self, edges: List[GraphEdgeModel]) -> None:
        for edge in edges:
            self.db.add(edge)
        await self.db.flush()

    async def get_node(self, node_id: uuid.UUID) -> Optional[GraphNodeModel]:
        result = await self.db.execute(select(GraphNodeModel).filter(GraphNodeModel.id == node_id))
        return result.scalars().first()

    async def get_snapshot_nodes(self, snapshot_id: uuid.UUID) -> List[GraphNodeModel]:
        result = await self.db.execute(select(GraphNodeModel).filter(GraphNodeModel.snapshot_id == snapshot_id))
        return list(result.scalars().all())

    async def get_snapshot_edges(self, snapshot_id: uuid.UUID) -> List[GraphEdgeModel]:
        result = await self.db.execute(select(GraphEdgeModel).filter(GraphEdgeModel.snapshot_id == snapshot_id))
        return list(result.scalars().all())

    async def get_node_edges(self, node_id: uuid.UUID) -> List[GraphEdgeModel]:
        result = await self.db.execute(
            select(GraphEdgeModel)
            .filter(or_(GraphEdgeModel.source_node_id == node_id, GraphEdgeModel.target_node_id == node_id))
        )
        return list(result.scalars().all())
