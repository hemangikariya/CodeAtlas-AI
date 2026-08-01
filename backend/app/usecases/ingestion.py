import os
import shutil
import zipfile
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import uuid

from backend.app.adapters.repositories.repository_repository import RepositoryRepository
from backend.app.adapters.repositories.snapshot_repository import SnapshotRepository
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.domain.ingestion import (
    RepositorySnapshot, Folder, File, CodeChunk, Dependency, DetectedLanguage
)
from backend.app.parsers.parser_manager import settings_parser_manager
from backend.app.events.event_types import (
    RepositoryExtractedEvent, RepositoryParsedEvent, 
    MetadataExtractedEvent, ChunkGenerationCompletedEvent, SnapshotCompletedEvent
)
from backend.app.events.dispatcher import event_dispatcher

class IngestRepositoryUseCase:
    def __init__(self, repo_repo: RepositoryRepository, snap_repo: SnapshotRepository):
        self.repo_repo = repo_repo
        self.snap_repo = snap_repo

    async def execute(self, snapshot_id: str, zip_file_path: Optional[str] = None, local_dir_path: Optional[str] = None) -> RepositorySnapshot:
        logger.info(f"Starting repository ingestion usecase for snapshot ID: {snapshot_id}")
        
        # 1. Update status to EXTRACTING
        snapshot = await self.snap_repo.update_snapshot_status(snapshot_id, "EXTRACTING")
        if not snapshot:
            raise ValueError(f"Snapshot with ID {snapshot_id} does not exist.")
            
        extract_dir = os.path.join(settings.STORAGE_DIR, "extracts", snapshot_id)
        os.makedirs(extract_dir, exist_ok=True)
        
        # 2. Extract ZIP archive or Copy Local directory
        try:
            if zip_file_path:
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                logger.info(f"Extracted zip archive to: {extract_dir}")
            elif local_dir_path:
                if os.path.exists(extract_dir):
                    shutil.rmtree(extract_dir)
                shutil.copytree(local_dir_path, extract_dir)
                logger.info(f"Copied local folder to: {extract_dir}")
            else:
                raise ValueError("No ingestion payload path provided.")
            await event_dispatcher.dispatch(RepositoryExtractedEvent(snapshot_id=snapshot_id, extract_path=extract_dir))
        except Exception as e:
            logger.error(f"Failed to extract zip archive: {str(e)}")
            await self.snap_repo.update_snapshot_status(snapshot_id, "FAILED")
            raise

        # 3. Detect languages & count lines of code
        await self.snap_repo.update_snapshot_status(snapshot_id, "PARSING")
        detected_languages = self._detect_languages(extract_dir, snapshot_id)
        
        # 4. Traverse files, generate AST parsing, chunks, and metadata
        folders: List[Folder] = []
        files: List[File] = []
        chunks: List[CodeChunk] = []
        dependencies: List[Dependency] = []
        
        # Folder map to track parents
        folder_paths_map: Dict[str, Folder] = {}
        
        # Walk directory
        for root, dirs, filenames in os.walk(extract_dir):
            # Create folder entries
            rel_root_path = os.path.relpath(root, extract_dir)
            if rel_root_path == ".":
                rel_root_path = ""
                
            if rel_root_path:
                folder_name = os.path.basename(root)
                parent_path = os.path.dirname(rel_root_path)
                parent_folder = folder_paths_map.get(parent_path)
                
                folder = Folder(
                    snapshot_id=snapshot_id,
                    name=folder_name,
                    path=rel_root_path,
                    parent_folder_id=folder_name if parent_folder else None
                )
                folders.append(folder)
                folder_paths_map[rel_root_path] = folder

            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_file_path = os.path.relpath(file_path, extract_dir)
                
                # Skip hidden directories like .git
                if any(part.startswith('.') for part in rel_file_path.split(os.sep)):
                    continue
                    
                # Read content
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception as e:
                    logger.warning(f"Skipped reading file {rel_file_path}: {str(e)}")
                    continue
                
                # Determine folder association
                file_parent_dir = os.path.dirname(rel_file_path)
                parent_folder = folder_paths_map.get(file_parent_dir)
                
                # Create File domain instance
                file_id = str(uuid.uuid4())
                file_domain = File(
                    id=file_id,
                    snapshot_id=snapshot_id,
                    folder_id=parent_folder.id if parent_folder else None,
                    name=filename,
                    path=rel_file_path,
                    content_chunk=content
                )
                files.append(file_domain)
                
                # Parse AST
                parse_results = settings_parser_manager.parse_file(content, rel_file_path)
                
                # Add chunks
                for parse_chunk in parse_results["chunks"]:
                    chunk = CodeChunk(
                        id=str(uuid.uuid4()),
                        file_id=file_id,
                        name=parse_chunk["name"],
                        type=parse_chunk["type"],
                        content=parse_chunk["content"],
                        start_line=parse_chunk["start_line"],
                        end_line=parse_chunk["end_line"],
                        metadata=parse_chunk["metadata"]
                    )
                    chunks.append(chunk)

                # Track file imports for dependency analysis
                for imp in parse_results["imports"]:
                    # Create temporary dependencies to analyze later
                    dependencies.append(Dependency(
                        snapshot_id=snapshot_id,
                        source=rel_file_path,
                        target=imp["raw"],
                        type="INTERNAL" # resolve in step 5
                    ))

        await event_dispatcher.dispatch(RepositoryParsedEvent(snapshot_id=snapshot_id, files_count=len(files)))
        
        # 5. Resolve dependencies (Internal vs. External)
        resolved_dependencies = self._resolve_dependencies(dependencies, files, snapshot_id)
        
        # 6. Persist structured metadata to database
        await self.snap_repo.update_snapshot_status(snapshot_id, "INDEXING")
        await self.snap_repo.save_indexing_results(
            snapshot_id=snapshot_id,
            folders=folders,
            files=files,
            chunks=chunks,
            deps=resolved_dependencies,
            langs=detected_languages
        )
        
        # 7. Cleanup extracted folder workspace
        try:
            shutil.rmtree(extract_dir)
            logger.info(f"Cleaned up temporary extraction workspace: {extract_dir}")
        except Exception as e:
            logger.warning(f"Could not clean up directory {extract_dir}: {str(e)}")

        # 8. Complete Ingestion Status
        completed_snap = await self.snap_repo.update_snapshot_status(snapshot_id, "COMPLETED")
        await event_dispatcher.dispatch(SnapshotCompletedEvent(snapshot_id=snapshot_id, status="COMPLETED"))
        
        return completed_snap

    def _detect_languages(self, extract_dir: str, snapshot_id: str) -> List[DetectedLanguage]:
        stats = {} # lang -> {"files": 0, "lines": 0}
        total_lines = 0
        
        extension_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".jsx": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript"
        }
        
        for root, _, filenames in os.walk(extract_dir):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                lang = extension_map.get(ext)
                if not lang:
                    continue
                    
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, extract_dir)
                if any(part.startswith('.') for part in rel_path.split(os.sep)):
                    continue
                    
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = len(f.read().splitlines())
                except Exception:
                    lines = 0
                    
                if lang not in stats:
                    stats[lang] = {"files": 0, "lines": 0}
                stats[lang]["files"] += 1
                stats[lang]["lines"] += lines
                total_lines += lines

        results = []
        for lang, val in stats.items():
            percentage = (val["lines"] / total_lines * 100) if total_lines > 0 else 0.0
            results.append(DetectedLanguage(
                snapshot_id=snapshot_id,
                language=lang,
                file_count=val["files"],
                line_count=val["lines"],
                percentage=round(percentage, 2)
            ))
            
        # Add fallback default if no supported languages found
        if not results:
            results.append(DetectedLanguage(
                snapshot_id=snapshot_id,
                language="Unknown",
                file_count=0,
                line_count=0,
                percentage=100.0
            ))
        return results

    def _resolve_dependencies(self, deps: List[Dependency], files: List[File], snapshot_id: str) -> List[Dependency]:
        import re
        file_paths = {f.path for f in files}
        resolved = []
        
        for dep in deps:
            is_internal = False
            
            # Extract target inside quotes (common in JS/TS import statements)
            quotes_match = re.findall(r"['\"](.*?)['\"]", dep.target)
            if quotes_match:
                module_path = quotes_match[0]
            else:
                # Python imports: e.g. "from app.models import User" -> target is "app.models"
                target_clean = dep.target.replace("import", "").replace("from", "").strip()
                module_path = target_clean.split()[0] if target_clean else dep.target

            # Normalize relative path structures
            module_path_clean = module_path.lstrip("./").lstrip("../").replace(".", "/")
            if module_path_clean.endswith("/py"):
                module_path_clean = module_path_clean[:-3] + ".py"
            elif module_path_clean.endswith("/js"):
                module_path_clean = module_path_clean[:-3] + ".js"

            for path in file_paths:
                # Check for substring match (e.g. "math_utils" in "math_utils.py")
                if module_path_clean in path or path.endswith(module_path_clean) or path.startswith(module_path_clean):
                    is_internal = True
                    dep.target = path
                    break
                    
            dep.type = "INTERNAL" if is_internal else "EXTERNAL"
            resolved.append(dep)
            
        return resolved
