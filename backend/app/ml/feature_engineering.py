import math
import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# DB models
from backend.app.adapters.models.file_model import FileModel
from backend.app.adapters.models.code_chunk_model import CodeChunkModel
from backend.app.adapters.models.dependency_model import DependencyModel
from backend.app.adapters.models.graph_node_model import GraphNodeModel
from backend.app.adapters.models.graph_edge_model import GraphEdgeModel

logger = logging.getLogger("codeatlas.ml")


class FeatureExtractor:
    """
    Extracts high-fidelity static analysis, repository structure, and knowledge graph 
    features from database snapshots for ML inference and training.
    """

    @staticmethod
    async def extract_features(db: AsyncSession, snapshot_id: str) -> Dict[str, Any]:
        import uuid
        if isinstance(snapshot_id, str):
            snapshot_id = uuid.UUID(snapshot_id)
        try:
            # 1. Retrieve snapshot DB records
            files_q = await db.execute(select(FileModel).where(FileModel.snapshot_id == snapshot_id))
            files = files_q.scalars().all()

            chunks_q = await db.execute(
                select(CodeChunkModel)
                .join(FileModel, FileModel.id == CodeChunkModel.file_id)
                .where(FileModel.snapshot_id == snapshot_id)
            )
            chunks = chunks_q.scalars().all()

            deps_q = await db.execute(select(DependencyModel).where(DependencyModel.snapshot_id == snapshot_id))
            deps = deps_q.scalars().all()

            nodes_q = await db.execute(select(GraphNodeModel).where(GraphNodeModel.snapshot_id == snapshot_id))
            nodes = nodes_q.scalars().all()

            edges_q = await db.execute(select(GraphEdgeModel).where(GraphEdgeModel.snapshot_id == snapshot_id))
            edges = edges_q.scalars().all()

            # 2. Compute Repository Metrics
            total_files = len(files)
            
            classes = [c for c in chunks if c.type in ["CLASS", "INTERFACE", "ENUM"]]
            functions = [c for c in chunks if c.type in ["FUNCTION", "METHOD"]]
            total_classes = len(classes)
            total_functions = len(functions)

            lines_of_code = 0
            comment_lines = 0
            max_depth = 0
            cyclomatic_complexity = total_files  # Base complexity of 1 per file
            duplicate_lines = 0

            # Language distribution count
            lang_counts = {"python": 0, "javascript": 0, "typescript": 0, "other": 0}

            seen_contents = set()
            for f in files:
                content = f.content_chunk or ""
                flines = content.splitlines()
                lines_of_code += len(flines)

                # Heuristic Cyclomatic Complexity
                for line in flines:
                    stripped = line.strip()
                    # Increment on control flow structures
                    if stripped.startswith("if ") or stripped.startswith("if(") or \
                       stripped.startswith("elif ") or stripped.startswith("elif(") or \
                       stripped.startswith("while ") or stripped.startswith("while(") or \
                       stripped.startswith("for ") or stripped.startswith("for(") or \
                       stripped.startswith("except ") or stripped.startswith("catch ") or \
                       " && " in line or " || " in line or " and " in line or " or " in line:
                        cyclomatic_complexity += 1

                    # Comment heuristics
                    if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
                        comment_lines += 1

                # Path depth metric
                parts = [p for p in f.path.replace("\\", "/").split("/") if p]
                max_depth = max(max_depth, len(parts))

                # Language counts
                ext = f.name.split(".")[-1].lower() if "." in f.name else ""
                if ext in ["py"]:
                    lang_counts["python"] += 1
                elif ext in ["js", "jsx"]:
                    lang_counts["javascript"] += 1
                elif ext in ["ts", "tsx"]:
                    lang_counts["typescript"] += 1
                else:
                    lang_counts["other"] += 1

                # Duplicate code heuristic: match raw file content chunks
                content_hash = hash(content)
                if content_hash in seen_contents:
                    duplicate_lines += len(flines)
                else:
                    seen_contents.add(content_hash)

            comment_ratio = comment_lines / max(1, lines_of_code)
            
            # Average lengths
            avg_func_len = 0
            if total_functions > 0:
                func_lines = sum([c.end_line - c.start_line + 1 for c in functions])
                avg_func_len = func_lines / total_functions

            avg_class_size = 0
            if total_classes > 0:
                avg_class_size = len(chunks) / total_classes

            # Folder depth
            folder_depth = max_depth

            # Dependency and import counts
            import_count = len([d for d in deps if d.type == "EXTERNAL"])
            dependency_count = len(deps)

            # Convert language distribution to ratio features
            pct_python = lang_counts["python"] / max(1, total_files)
            pct_javascript = lang_counts["javascript"] / max(1, total_files)
            pct_typescript = lang_counts["typescript"] / max(1, total_files)
            pct_other = lang_counts["other"] / max(1, total_files)

            # 3. Knowledge Layer Graph Features
            graph_nodes = len(nodes)
            graph_edges = len(edges)

            graph_density = 0.0
            if graph_nodes > 1:
                graph_density = graph_edges / (graph_nodes * (graph_nodes - 1))

            dependency_density = 0.0
            if total_files > 1:
                dependency_density = dependency_count / (total_files * (total_files - 1))

            # DFS to find connected components in the knowledge graph
            adj = {n.id: [] for n in nodes}
            # Add undirected edges
            node_id_map = {n.id: n for n in nodes}
            for e in edges:
                if e.source_node_id in adj and e.target_node_id in adj:
                    adj[e.source_node_id].append(e.target_node_id)
                    adj[e.target_node_id].append(e.source_node_id)

            visited = set()
            connected_components = 0
            degree_sum = 0
            max_degree_cent = 0.0

            for nid in adj:
                deg = len(adj[nid])
                degree_sum += deg
                if graph_nodes > 1:
                    max_degree_cent = max(max_degree_cent, deg / (graph_nodes - 1))

                if nid not in visited:
                    connected_components += 1
                    # Traverse component
                    q = [nid]
                    visited.add(nid)
                    while q:
                        curr = q.pop(0)
                        for neighbor in adj[curr]:
                            if neighbor not in visited:
                                visited.add(neighbor)
                                q.append(neighbor)

            avg_graph_degree = degree_sum / max(1, graph_nodes)
            graph_centrality = max_degree_cent

            # 4. Static Analysis Code Smells
            long_methods = len([c for c in functions if (c.end_line - c.start_line + 1) > 50])
            large_classes = len([c for c in classes if (c.end_line - c.start_line + 1) > 200])

            # Heuristic dead code (unused imports)
            # Find all imported symbols, check if they are in files
            dead_code = 0
            for d in deps:
                # If target is imported externally but not used in file content
                target_sym = d.target.split(".")[-1]
                found = False
                for f in files:
                    if target_sym in f.content_chunk and d.source not in f.path:
                        found = True
                        break
                if not found and d.type == "EXTERNAL":
                    dead_code += 1

            code_smells = long_methods + large_classes + dead_code

            # Duplicate score ratio
            duplicate_code = duplicate_lines / max(1, lines_of_code)

            # Compile raw feature dictionary
            features = {
                "total_files": float(total_files),
                "total_classes": float(total_classes),
                "total_functions": float(total_functions),
                "lines_of_code": float(lines_of_code),
                "avg_func_len": float(avg_func_len),
                "avg_class_size": float(avg_class_size),
                "comment_ratio": float(comment_ratio),
                "folder_depth": float(folder_depth),
                "import_count": float(import_count),
                "dependency_count": float(dependency_count),
                "pct_python": float(pct_python),
                "pct_javascript": float(pct_javascript),
                "pct_typescript": float(pct_typescript),
                "pct_other": float(pct_other),
                "graph_nodes": float(graph_nodes),
                "graph_edges": float(graph_edges),
                "graph_density": float(graph_density),
                "avg_graph_degree": float(avg_graph_degree),
                "connected_components": float(connected_components),
                "graph_centrality": float(graph_centrality),
                "dependency_density": float(dependency_density),
                "cyclomatic_complexity": float(cyclomatic_complexity),
                "long_methods": float(long_methods),
                "large_classes": float(large_classes),
                "dead_code": float(dead_code),
                "duplicate_code": float(duplicate_code),
                "code_smells": float(code_smells)
            }
            return features

        except Exception as e:
            logger.error(f"Error extracting features for snapshot {snapshot_id}: {str(e)}")
            raise e
