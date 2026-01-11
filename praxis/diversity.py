"""Diversity analysis using clustering and embeddings for quality validation."""

from __future__ import annotations

import random
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import orjson
import structlog
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.decomposition import PCA

from praxis.config import get_config

logger = structlog.get_logger()


class DiversityAnalyzer:
    """
    Analyzes task diversity using embeddings and clustering.

    Features:
    - Sentence embeddings for semantic similarity
    - K-means clustering for diversity measurement
    - Automatic cluster labeling
    - Coverage scoring across domains
    """

    def __init__(self, embedding_model: str | None = None) -> None:
        config = get_config()
        self.embedding_model_name = embedding_model or config.embedding_model
        self._model = None

    def _get_model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.embedding_model_name)
                logger.info("embedding_model_loaded", model=self.embedding_model_name)
            except ImportError:
                logger.warning("sentence_transformers not available, using fallback")
                self._model = "fallback"
        return self._model

    def load_tasks(
        self,
        output_dir: Path,
        sample_size: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Load tasks from output directory.

        Args:
            output_dir: Directory containing task JSONL files
            sample_size: Maximum number of tasks to load (for memory efficiency)

        Returns:
            List of task dictionaries
        """
        tasks = []
        task_files = sorted(output_dir.glob("tasks_*.jsonl"))

        for task_file in task_files:
            with open(task_file, "rb") as f:
                for line in f:
                    tasks.append(orjson.loads(line))

                    if sample_size and len(tasks) >= sample_size:
                        break

            if sample_size and len(tasks) >= sample_size:
                break

        # Random sample if we have more than needed
        if sample_size and len(tasks) > sample_size:
            tasks = random.sample(tasks, sample_size)

        logger.info("tasks_loaded", count=len(tasks))
        return tasks

    def compute_embeddings(
        self,
        tasks: list[dict[str, Any]],
        batch_size: int = 64,
    ) -> np.ndarray:
        """
        Compute embeddings for tasks.

        Uses the task name, completion criteria, and context for embedding.
        """
        model = self._get_model()

        # Build text representations
        texts = []
        for task in tasks:
            parts = [task.get("name", "")]

            completion = task.get("completion", {})
            parts.append(completion.get("precondition", ""))
            parts.append(completion.get("postcondition", ""))

            parts.append(task.get("context", ""))

            # Join non-empty parts
            text = " ".join(p for p in parts if p)
            texts.append(text)

        if model == "fallback":
            # Fallback: use simple TF-IDF-like embeddings
            return self._fallback_embeddings(texts)

        # Use sentence transformer
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 1000,
            convert_to_numpy=True,
        )

        logger.info("embeddings_computed", shape=embeddings.shape)
        return embeddings

    def _fallback_embeddings(self, texts: list[str]) -> np.ndarray:
        """Simple fallback embedding using word hashing."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD

        vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
        tfidf = vectorizer.fit_transform(texts)

        # Reduce dimensionality
        n_components = min(256, tfidf.shape[1] - 1, tfidf.shape[0] - 1)
        if n_components < 2:
            # Not enough data for SVD
            return np.random.randn(len(texts), 64).astype(np.float32)

        svd = TruncatedSVD(n_components=n_components)
        embeddings = svd.fit_transform(tfidf)

        return embeddings.astype(np.float32)

    def cluster(
        self,
        embeddings: np.ndarray,
        n_clusters: int = 50,
        max_iter: int = 300,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """
        Cluster embeddings and compute diversity metrics.

        Args:
            embeddings: Task embeddings
            n_clusters: Number of clusters
            max_iter: Maximum iterations for K-means

        Returns:
            Tuple of (cluster labels, metrics dict)
        """
        n_samples = embeddings.shape[0]
        n_clusters = min(n_clusters, n_samples - 1)

        if n_clusters < 2:
            logger.warning("not_enough_samples_for_clustering")
            return np.zeros(n_samples, dtype=int), {"error": "not enough samples"}

        # Use MiniBatchKMeans for large datasets
        if n_samples > 10000:
            clusterer = MiniBatchKMeans(
                n_clusters=n_clusters,
                max_iter=max_iter,
                batch_size=1024,
                random_state=42,
            )
        else:
            clusterer = KMeans(
                n_clusters=n_clusters,
                max_iter=max_iter,
                n_init=10,
                random_state=42,
            )

        labels = clusterer.fit_predict(embeddings)

        # Compute metrics
        metrics = self._compute_metrics(embeddings, labels, clusterer)

        logger.info(
            "clustering_complete",
            n_clusters=n_clusters,
            silhouette=metrics["silhouette_score"],
        )

        return labels, metrics

    def _compute_metrics(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray,
        clusterer: KMeans | MiniBatchKMeans,
    ) -> dict[str, Any]:
        """Compute clustering quality metrics."""
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

        if n_clusters < 2:
            return {
                "silhouette_score": 0.0,
                "calinski_harabasz": 0.0,
                "davies_bouldin": 0.0,
                "coverage_score": 0.0,
                "n_clusters": n_clusters,
            }

        # Core metrics
        silhouette = silhouette_score(embeddings, labels, sample_size=min(5000, len(labels)))
        calinski = calinski_harabasz_score(embeddings, labels)
        davies = davies_bouldin_score(embeddings, labels)

        # Cluster sizes
        cluster_sizes = dict(Counter(labels))

        # Coverage score: how evenly distributed are clusters
        sizes = list(cluster_sizes.values())
        ideal_size = len(labels) / n_clusters
        coverage = 1.0 - np.std(sizes) / ideal_size if ideal_size > 0 else 0.0

        return {
            "silhouette_score": float(silhouette),
            "calinski_harabasz": float(calinski),
            "davies_bouldin": float(davies),
            "coverage_score": float(max(0.0, min(1.0, coverage))),
            "n_clusters": n_clusters,
            "cluster_sizes": cluster_sizes,
            "cluster_centers": clusterer.cluster_centers_.tolist(),
        }

    def label_clusters(
        self,
        tasks: list[dict[str, Any]],
        labels: np.ndarray,
    ) -> dict[int, str]:
        """
        Generate descriptive labels for each cluster.

        Uses the most common verbs and tags in each cluster.
        """
        cluster_tasks: dict[int, list[dict[str, Any]]] = {}

        for task, label in zip(tasks, labels):
            if label not in cluster_tasks:
                cluster_tasks[label] = []
            cluster_tasks[label].append(task)

        cluster_labels = {}

        for cluster_id, cluster_task_list in cluster_tasks.items():
            # Extract verbs (first word of task names)
            verbs = []
            for task in cluster_task_list:
                name = task.get("name", "")
                if name:
                    verbs.append(name.split()[0].lower())

            # Extract tags
            all_tags = []
            for task in cluster_task_list:
                all_tags.extend(task.get("tags", []))

            # Most common verb and tag
            verb_counts = Counter(verbs)
            tag_counts = Counter(all_tags)

            top_verb = verb_counts.most_common(1)[0][0] if verb_counts else "unknown"
            top_tag = tag_counts.most_common(1)[0][0] if tag_counts else ""

            # Create label
            if top_tag:
                label = f"{top_verb} ({top_tag})"
            else:
                label = top_verb

            cluster_labels[cluster_id] = label

        return cluster_labels

    def analyze_domain_coverage(
        self,
        tasks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Analyze coverage across task domains.

        Returns metrics on how well different domains are represented.
        """
        # Extract categories from task metadata
        domains: dict[str, int] = {}
        verb_categories: dict[str, int] = {}
        noun_categories: dict[str, int] = {}

        for task in tasks:
            provenance = task.get("provenance", {})

            # Domain from persona
            persona_domain = provenance.get("persona_domain", "unknown")
            domains[persona_domain] = domains.get(persona_domain, 0) + 1

            # Verb category if available
            verb_cat = provenance.get("verb_category", "unknown")
            verb_categories[verb_cat] = verb_categories.get(verb_cat, 0) + 1

            # Noun category if available
            noun_cat = provenance.get("noun_category", "unknown")
            noun_categories[noun_cat] = noun_categories.get(noun_cat, 0) + 1

        # Calculate coverage scores
        def entropy_score(counts: dict[str, int]) -> float:
            """Calculate normalized entropy as coverage score."""
            total = sum(counts.values())
            if total == 0 or len(counts) <= 1:
                return 0.0

            probs = [c / total for c in counts.values()]
            entropy = -sum(p * np.log2(p) for p in probs if p > 0)
            max_entropy = np.log2(len(counts))

            return float(entropy / max_entropy) if max_entropy > 0 else 0.0

        return {
            "domains": domains,
            "verb_categories": verb_categories,
            "noun_categories": noun_categories,
            "domain_coverage_score": entropy_score(domains),
            "verb_coverage_score": entropy_score(verb_categories),
            "noun_coverage_score": entropy_score(noun_categories),
            "total_tasks": len(tasks),
        }

    def find_gaps(
        self,
        tasks: list[dict[str, Any]],
        embeddings: np.ndarray,
        labels: np.ndarray,
    ) -> list[dict[str, Any]]:
        """
        Identify potential gaps in task coverage.

        Finds underrepresented clusters and suggests areas for expansion.
        """
        cluster_sizes = Counter(labels)
        mean_size = np.mean(list(cluster_sizes.values()))
        std_size = np.std(list(cluster_sizes.values()))

        # Find small clusters (potential gaps)
        threshold = max(1, mean_size - std_size)
        small_clusters = [
            cluster_id for cluster_id, size in cluster_sizes.items()
            if size < threshold
        ]

        gaps = []
        for cluster_id in small_clusters:
            # Get representative tasks from this cluster
            cluster_tasks = [
                task for task, label in zip(tasks, labels)
                if label == cluster_id
            ]

            if cluster_tasks:
                # Get sample task names
                sample_names = [t.get("name", "") for t in cluster_tasks[:5]]

                gaps.append({
                    "cluster_id": int(cluster_id),
                    "size": cluster_sizes[cluster_id],
                    "sample_tasks": sample_names,
                    "suggestion": f"Add more tasks similar to: {sample_names[0]}",
                })

        return sorted(gaps, key=lambda x: x["size"])

    def validate_diversity(
        self,
        tasks: list[dict[str, Any]],
        min_silhouette: float = 0.1,
        min_coverage: float = 0.5,
    ) -> dict[str, Any]:
        """
        Comprehensive diversity validation.

        Args:
            tasks: List of tasks to validate
            min_silhouette: Minimum acceptable silhouette score
            min_coverage: Minimum acceptable coverage score

        Returns:
            Validation results with pass/fail status
        """
        if len(tasks) < 10:
            return {
                "valid": False,
                "reason": "Not enough tasks for diversity analysis",
                "task_count": len(tasks),
            }

        # Compute embeddings
        embeddings = self.compute_embeddings(tasks)

        # Cluster
        n_clusters = min(50, len(tasks) // 10)
        labels, metrics = self.cluster(embeddings, n_clusters=n_clusters)

        # Label clusters
        cluster_labels = self.label_clusters(tasks, labels)
        metrics["cluster_labels"] = cluster_labels

        # Domain coverage
        domain_metrics = self.analyze_domain_coverage(tasks)

        # Find gaps
        gaps = self.find_gaps(tasks, embeddings, labels)

        # Validation
        silhouette_ok = metrics["silhouette_score"] >= min_silhouette
        coverage_ok = metrics["coverage_score"] >= min_coverage
        domain_ok = domain_metrics["domain_coverage_score"] >= min_coverage

        valid = silhouette_ok and coverage_ok and domain_ok

        reasons = []
        if not silhouette_ok:
            reasons.append(f"Low silhouette score: {metrics['silhouette_score']:.3f}")
        if not coverage_ok:
            reasons.append(f"Low cluster coverage: {metrics['coverage_score']:.3f}")
        if not domain_ok:
            reasons.append(f"Low domain coverage: {domain_metrics['domain_coverage_score']:.3f}")

        return {
            "valid": valid,
            "reason": "; ".join(reasons) if reasons else "All checks passed",
            "metrics": metrics,
            "domain_coverage": domain_metrics,
            "gaps": gaps[:10],  # Top 10 gaps
            "recommendations": self._generate_recommendations(metrics, domain_metrics, gaps),
        }

    def _generate_recommendations(
        self,
        metrics: dict[str, Any],
        domain_metrics: dict[str, Any],
        gaps: list[dict[str, Any]],
    ) -> list[str]:
        """Generate recommendations for improving diversity."""
        recommendations = []

        # Check silhouette score
        if metrics["silhouette_score"] < 0.1:
            recommendations.append(
                "Tasks are not well-separated. Consider generating more distinct task types."
            )

        # Check coverage
        if metrics["coverage_score"] < 0.5:
            recommendations.append(
                "Cluster sizes are uneven. Focus on underrepresented categories."
            )

        # Check domain coverage
        domains = domain_metrics["domains"]
        if len(domains) < 5:
            recommendations.append(
                "Limited domain coverage. Add tasks from more domains: "
                "industrial, healthcare, maintenance, etc."
            )

        # Specific domain gaps
        expected_domains = [
            "industrial", "municipality", "maintenance", "healthcare",
            "domestic", "office", "agriculture", "construction",
        ]
        missing_domains = [d for d in expected_domains if d not in domains]
        if missing_domains:
            recommendations.append(
                f"Missing domains: {', '.join(missing_domains[:5])}"
            )

        # Gap-specific recommendations
        if gaps:
            top_gap = gaps[0]
            recommendations.append(
                f"Expand small cluster: {top_gap['suggestion']}"
            )

        return recommendations


def quick_diversity_check(
    output_dir: Path,
    sample_size: int = 1000,
) -> dict[str, Any]:
    """
    Quick diversity check for generated tasks.

    Convenience function for CLI usage.
    """
    analyzer = DiversityAnalyzer()
    tasks = analyzer.load_tasks(output_dir, sample_size=sample_size)
    return analyzer.validate_diversity(tasks)
