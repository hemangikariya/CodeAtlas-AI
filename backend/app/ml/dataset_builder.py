import os
import csv
import random
import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger("codeatlas.ml")


class DatasetBuilder:
    """
    Constructs datasets for ML training from indexed repository feature stores.
    Supports CSV exports, train/val/test partitions, feature normalization, and 
    synthetic seed generation for cold-starts and testing.
    """

    FEATURE_COLS = [
        "total_files", "total_classes", "total_functions", "lines_of_code",
        "avg_func_len", "avg_class_size", "comment_ratio", "folder_depth",
        "import_count", "dependency_count", "pct_python", "pct_javascript",
        "pct_typescript", "pct_other", "graph_nodes", "graph_edges",
        "graph_density", "avg_graph_degree", "connected_components",
        "graph_centrality", "dependency_density", "cyclomatic_complexity",
        "long_methods", "large_classes", "dead_code", "duplicate_code",
        "code_smells"
    ]

    @staticmethod
    def generate_labels(row: Dict[str, float]) -> Dict[str, float]:
        """
        Generates baseline labels heuristically from features.
        NOTE: Synthetic labels are only used for cold-start demonstration and testing.
        """
        loc = row.get("lines_of_code", 0.0)
        complexity = row.get("cyclomatic_complexity", 0.0)
        smells = row.get("code_smells", 0.0)
        comments = row.get("comment_ratio", 0.0)
        files = max(1.0, row.get("total_files", 1.0))
        dup = row.get("duplicate_code", 0.0)
        dep_density = row.get("dependency_density", 0.0)

        # 1. Maintainability score (0 - 100)
        maintainability = 100.0 - 0.2 * (complexity / files) - 0.5 * smells + 30.0 * comments - 15.0 * dup
        maintainability = max(10.0, min(100.0, maintainability))

        # 2. Bug Risk score (0 - 100) and label (0 or 1)
        bug_score = 5.0 * (smells / files) + 15.0 * (complexity / (files * 2.0)) + 40.0 * dup + 20.0 * dep_density
        bug_score = max(0.0, min(100.0, bug_score))
        bug_risk = 1.0 if bug_score > 35.0 else 0.0

        # 3. Code Complexity score (0 - 100)
        complexity_score = 10.0 * (complexity / files) + 0.5 * row.get("avg_func_len", 0.0) + 15.0 * row.get("large_classes", 0.0)
        complexity_score = max(0.0, min(100.0, complexity_score))

        # 4. Repository Health (0 - 100)
        health = 0.4 * maintainability + 0.3 * (100.0 - complexity_score) + 0.3 * (100.0 - bug_score)
        health = max(10.0, min(100.0, health))

        return {
            "maintainability": maintainability,
            "bug_risk": bug_risk,
            "bug_score": bug_score,
            "complexity": complexity_score,
            "health": health
        }

    @classmethod
    def generate_synthetic_seed(cls, num_samples: int = 150) -> pd.DataFrame:
        """
        Generates a synthetic dataset of repository feature vectors and labels.
        Used for cold-start demo runs and validation checks.
        """
        np.random.seed(42)
        random.seed(42)
        data = []

        for i in range(num_samples):
            # Form feature metrics correlation
            total_files = float(random.randint(5, 120))
            lines_of_code = total_files * float(random.randint(50, 400))
            total_classes = total_files * float(np.random.choice([0.1, 0.2, 0.5]))
            total_functions = total_files * float(random.randint(2, 10))

            avg_func_len = float(random.randint(5, 45))
            avg_class_size = float(random.randint(1, 4))
            comment_ratio = float(np.random.uniform(0.05, 0.45))
            folder_depth = float(random.randint(2, 6))
            
            dependency_count = total_files * float(np.random.uniform(1.0, 4.0))
            import_count = dependency_count * float(np.random.uniform(0.1, 0.5))

            # Languages
            langs = np.random.dirichlet(np.ones(4))
            pct_python = float(langs[0])
            pct_javascript = float(langs[1])
            pct_typescript = float(langs[2])
            pct_other = float(langs[3])

            # Graph metrics
            graph_nodes = total_files + total_classes + total_functions
            graph_edges = dependency_count * 1.5
            graph_density = graph_edges / max(1.0, graph_nodes * (graph_nodes - 1))
            avg_graph_degree = (2.0 * graph_edges) / max(1.0, graph_nodes)
            connected_components = float(random.randint(1, 5))
            graph_centrality = float(np.random.uniform(0.05, 0.6))
            dependency_density = dependency_count / max(1.0, total_files * (total_files - 1))

            # Code quality issues
            cyclomatic_complexity = total_files * float(np.random.uniform(1.5, 6.0))
            long_methods = total_functions * float(np.random.choice([0.02, 0.05, 0.1]))
            large_classes = total_classes * float(np.random.choice([0.01, 0.04, 0.08]))
            dead_code = import_count * float(np.random.uniform(0.05, 0.3))
            duplicate_code = float(np.random.uniform(0.0, 0.45))
            code_smells = long_methods + large_classes + dead_code

            row = {
                "total_files": total_files,
                "total_classes": total_classes,
                "total_functions": total_functions,
                "lines_of_code": lines_of_code,
                "avg_func_len": avg_func_len,
                "avg_class_size": avg_class_size,
                "comment_ratio": comment_ratio,
                "folder_depth": folder_depth,
                "import_count": import_count,
                "dependency_count": dependency_count,
                "pct_python": pct_python,
                "pct_javascript": pct_javascript,
                "pct_typescript": pct_typescript,
                "pct_other": pct_other,
                "graph_nodes": graph_nodes,
                "graph_edges": graph_edges,
                "graph_density": graph_density,
                "avg_graph_degree": avg_graph_degree,
                "connected_components": connected_components,
                "graph_centrality": graph_centrality,
                "dependency_density": dependency_density,
                "cyclomatic_complexity": cyclomatic_complexity,
                "long_methods": long_methods,
                "large_classes": large_classes,
                "dead_code": dead_code,
                "duplicate_code": duplicate_code,
                "code_smells": code_smells
            }

            labels = cls.generate_labels(row)
            row.update(labels)
            data.append(row)

        return pd.DataFrame(data)

    @classmethod
    def train_val_test_split(
        cls, df: pd.DataFrame, train_pct: float = 0.7, val_pct: float = 0.15
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Splits dataset DataFrame into train, validation, and test subsets.
        """
        shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
        n = len(shuffled)
        
        n_train = int(n * train_pct)
        n_val = int(n * val_pct)
        
        train = shuffled.iloc[:n_train]
        val = shuffled.iloc[n_train:n_train + n_val]
        test = shuffled.iloc[n_train + n_val:]
        
        return train, val, test

    @staticmethod
    def export_csv(df: pd.DataFrame, filepath: str) -> None:
        """
        Writes dataframe contents to a target CSV file.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df.to_csv(filepath, index=False)
