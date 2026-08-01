import uuid
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.adapters.models.graph_node_model import GraphNodeModel
from backend.app.adapters.models.graph_edge_model import GraphEdgeModel
from backend.app.adapters.models.folder_model import FolderModel
from backend.app.adapters.models.file_model import FileModel
from backend.app.adapters.models.code_chunk_model import CodeChunkModel
from backend.app.adapters.models.dependency_model import DependencyModel
from backend.app.adapters.models.snapshot_model import SnapshotModel
from backend.app.adapters.models.repository_model import RepositoryModel

from backend.app.knowledge.graph.graph_types import NodeType, EdgeType
from backend.app.knowledge.graph.graph_repository import GraphRepository

class GraphBuilder:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.graph_repo = GraphRepository(db)

    async def build_graph(self, snapshot_id: str) -> None:
        sid = uuid.UUID(snapshot_id)
        
        # 1. Fetch snapshot details
        snap_res = await self.db.execute(select(SnapshotModel).filter(SnapshotModel.id == sid))
        snap = snap_res.scalars().first()
        if not snap:
            return
            
        repo_res = await self.db.execute(select(RepositoryModel).filter(RepositoryModel.id == snap.repository_id))
        repo = repo_res.scalars().first()
        
        nodes: List[GraphNodeModel] = []
        edges: List[GraphEdgeModel] = []
        
        node_map: Dict[str, GraphNodeModel] = {} # entity_id/path -> NodeModel
        
        # 2. Create REPOSITORY Node
        repo_node = GraphNodeModel(
            id=uuid.uuid4(),
            snapshot_id=sid,
            entity_id=repo.id,
            name=repo.name,
            type=NodeType.REPOSITORY.value,
            properties={"url": repo.url or ""}
        )
        nodes.append(repo_node)
        
        # 3. Create SNAPSHOT Node
        snap_node = GraphNodeModel(
            id=uuid.uuid4(),
            snapshot_id=sid,
            entity_id=snap.id,
            name=f"snapshot_{snap.version}",
            type=NodeType.SNAPSHOT.value,
            properties={"branch": snap.branch or "", "commit_sha": snap.commit_sha or ""}
        )
        nodes.append(snap_node)
        
        # Link Repo to Snapshot (CONTAINS)
        edges.append(GraphEdgeModel(
            id=uuid.uuid4(),
            snapshot_id=sid,
            source_node_id=repo_node.id,
            target_node_id=snap_node.id,
            type=EdgeType.CONTAINS.value,
            properties={}
        ))

        # 4. Create FOLDER Nodes
        folder_res = await self.db.execute(select(FolderModel).filter(FolderModel.snapshot_id == sid))
        db_folders = folder_res.scalars().all()
        for folder in db_folders:
            f_node = GraphNodeModel(
                id=uuid.uuid4(),
                snapshot_id=sid,
                entity_id=folder.id,
                name=folder.name,
                type=NodeType.FOLDER.value,
                properties={"path": folder.path}
            )
            nodes.append(f_node)
            node_map[str(folder.id)] = f_node
            node_map[folder.path] = f_node
            
        # Link folders (CONTAINS parent -> child)
        for folder in db_folders:
            if folder.parent_folder_id:
                parent_node = node_map.get(str(folder.parent_folder_id))
                child_node = node_map.get(str(folder.id))
                if parent_node and child_node:
                    edges.append(GraphEdgeModel(
                        id=uuid.uuid4(),
                        snapshot_id=sid,
                        source_node_id=parent_node.id,
                        target_node_id=child_node.id,
                        type=EdgeType.CONTAINS.value,
                        properties={}
                    ))
            else:
                # Link Snapshot to Root Folder
                child_node = node_map.get(str(folder.id))
                if child_node:
                    edges.append(GraphEdgeModel(
                        id=uuid.uuid4(),
                        snapshot_id=sid,
                        source_node_id=snap_node.id,
                        target_node_id=child_node.id,
                        type=EdgeType.CONTAINS.value,
                        properties={}
                    ))

        # 5. Create FILE Nodes
        file_res = await self.db.execute(select(FileModel).filter(FileModel.snapshot_id == sid))
        db_files = file_res.scalars().all()
        file_ids = [f.id for f in db_files]
        
        for file in db_files:
            type_val = NodeType.FILE.value
            if file.name.lower() == "readme.md" or file.name.lower().endswith(".md"):
                type_val = NodeType.CONFIG_FILE.value  # treat documentation/readme as config/meta
            elif file.name.lower() in ["package.json", "requirements.txt", "setup.py", "pyproject.toml", "alembic.ini"]:
                type_val = NodeType.CONFIG_FILE.value
                
            f_node = GraphNodeModel(
                id=uuid.uuid4(),
                snapshot_id=sid,
                entity_id=file.id,
                name=file.name,
                type=type_val,
                properties={"path": file.path}
            )
            nodes.append(f_node)
            node_map[str(file.id)] = f_node
            node_map[file.path] = f_node
            
            # Link Folder containing File (CONTAINS)
            if file.folder_id:
                folder_node = node_map.get(str(file.folder_id))
                if folder_node:
                    edges.append(GraphEdgeModel(
                        id=uuid.uuid4(),
                        snapshot_id=sid,
                        source_node_id=folder_node.id,
                        target_node_id=f_node.id,
                        type=EdgeType.CONTAINS.value,
                        properties={}
                    ))
            else:
                # Link Snapshot directly to file
                edges.append(GraphEdgeModel(
                    id=uuid.uuid4(),
                    snapshot_id=sid,
                    source_node_id=snap_node.id,
                    target_node_id=f_node.id,
                    type=EdgeType.CONTAINS.value,
                    properties={}
                ))

        # 6. Create Chunks Nodes (CLASS, METHOD, FUNCTION, etc.)
        if file_ids:
            chunk_res = await self.db.execute(select(CodeChunkModel).filter(CodeChunkModel.file_id.in_(file_ids)))
            db_chunks = chunk_res.scalars().all()
            
            # We map chunks to entities
            for chunk in db_chunks:
                # Convert chunk type to NodeType
                chunk_type_map = {
                    "CLASS": NodeType.CLASS.value,
                    "METHOD": NodeType.METHOD.value,
                    "FUNCTION": NodeType.FUNCTION.value,
                    "INTERFACE": NodeType.INTERFACE.value,
                    "ENUM": NodeType.ENUM.value,
                    "README": NodeType.CONFIG_FILE.value,
                    "CONFIG": NodeType.CONFIG_FILE.value
                }
                ntype = chunk_type_map.get(chunk.type, NodeType.FUNCTION.value)
                
                ch_node = GraphNodeModel(
                    id=uuid.uuid4(),
                    snapshot_id=sid,
                    entity_id=chunk.id,
                    name=chunk.name,
                    type=ntype,
                    properties={"start_line": chunk.start_line, "end_line": chunk.end_line}
                )
                nodes.append(ch_node)
                node_map[str(chunk.id)] = ch_node
                
                # Fetch parent file node
                file_node = node_map.get(str(chunk.file_id))
                if file_node:
                    # Link File containing symbol (DEFINES)
                    edges.append(GraphEdgeModel(
                        id=uuid.uuid4(),
                        snapshot_id=sid,
                        source_node_id=file_node.id,
                        target_node_id=ch_node.id,
                        type=EdgeType.DEFINES.value,
                        properties={}
                    ))
                    
            # Link Class DEFINES Method
            # Loop over method chunks and link to class chunks
            class_nodes = {n.name: n for n in nodes if n.type == NodeType.CLASS.value}
            for chunk in db_chunks:
                if chunk.type == "METHOD":
                    class_name = chunk.metadata_json.get("class") if chunk.metadata_json else None
                    if class_name and class_name in class_nodes:
                        c_node = class_nodes[class_name]
                        m_node = node_map.get(str(chunk.id))
                        if c_node and m_node:
                            edges.append(GraphEdgeModel(
                                id=uuid.uuid4(),
                                snapshot_id=sid,
                                source_node_id=c_node.id,
                                target_node_id=m_node.id,
                                type=EdgeType.DEFINES.value,
                                properties={}
                            ))

        # 7. Create DEPENDENCY and IMPORTS Edges
        dep_res = await self.db.execute(select(DependencyModel).filter(DependencyModel.snapshot_id == sid))
        db_deps = dep_res.scalars().all()
        for dep in db_deps:
            source_file_node = node_map.get(dep.source)
            target_file_node = node_map.get(dep.target)
            
            if source_file_node and target_file_node:
                # Add IMPORTS edge
                edges.append(GraphEdgeModel(
                    id=uuid.uuid4(),
                    snapshot_id=sid,
                    source_node_id=source_file_node.id,
                    target_node_id=target_file_node.id,
                    type=EdgeType.IMPORTS.value if dep.type == "INTERNAL" else EdgeType.DEPENDS_ON.value,
                    properties={}
                ))
            elif source_file_node:
                # Target is external package (we can create a transient external node or link to Snap)
                ext_node = GraphNodeModel(
                    id=uuid.uuid4(),
                    snapshot_id=sid,
                    name=dep.target,
                    type=NodeType.CONFIG_FILE.value, # external configuration / dependency package
                    properties={"external": True}
                )
                nodes.append(ext_node)
                edges.append(GraphEdgeModel(
                    id=uuid.uuid4(),
                    snapshot_id=sid,
                    source_node_id=source_file_node.id,
                    target_node_id=ext_node.id,
                    type=EdgeType.DEPENDS_ON.value,
                    properties={}
                ))

        # 8. Persist nodes & edges
        await self.graph_repo.add_nodes(nodes)
        await self.graph_repo.add_edges(edges)
