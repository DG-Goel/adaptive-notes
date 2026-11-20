"""
Retrieval Quality Benchmark

Compares four retrieval configurations:
A. Dense-only (vector search)
B. BM25-only (sparse search)
C. Hybrid (dense + BM25 with RRF fusion)
D. Hybrid + cross-encoder reranking

Metrics computed:
- Recall@K: % of relevant documents retrieved
- MRR (Mean Reciprocal Rank): Position of first relevant doc
- Precision@K: % of retrieved docs that are relevant
- NDCG@K: Normalized Discounted Cumulative Gain
- Average retrieval time
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Tuple
import logging

from src.core.retrieval_pipeline import RetrievalPipeline, get_retrieval_pipeline
from src.core.vector_store import get_vector_store
from src.services.ingestion.pipeline import IngestionPipeline
from src.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RetrievalBenchmark:
    """Benchmark retrieval configurations."""
    
    def __init__(self, top_k: int = 5):
        """
        Initialize benchmark.
        
        Args:
            top_k: Number of results to retrieve and evaluate
        """
        self.top_k = top_k
        
        # Initialize retrieval pipeline (uses singletons internally)
        self.retrieval_pipeline = get_retrieval_pipeline()
        
        # Get vector store for helpers
        self.vector_store = get_vector_store()
        
        # Load documents into retrieval systems
        self._ingest_documents()
    
    def _ingest_documents(self):
        """Ingest sample documents into all retrieval systems."""
        logger.info("Ingesting documents...")
        
        # Get sample documents
        docs_dir = Path("tests/fixtures/sample_documents")
        file_paths = list(docs_dir.glob("*.md")) + list(docs_dir.glob("*.txt"))
        
        if not file_paths:
            raise FileNotFoundError(f"No documents found in {docs_dir}")
        
        logger.info(f"Found {len(file_paths)} documents")
        
        # Ingest into vector store (also populates BM25 via pipeline)
        pipeline = IngestionPipeline()
        result = pipeline.ingest([str(p) for p in file_paths])
        
        logger.info(f"Ingestion complete: {result.documents_processed} docs, {result.chunks_created} chunks")
    
    def retrieve_dense_only(self, query: str) -> Tuple[List[Dict], float]:
        """
        Retrieve using dense vectors only.
        
        Args:
            query: Search query
            
        Returns:
            Tuple of (results, retrieval_time)
        """
        start = time.time()
        
        results = self.retrieval_pipeline.retrieve(
            query=query,
            top_k=self.top_k,
            method="dense",
            use_reranking=False
        )
        
        duration = time.time() - start
        return results, duration
    
    def retrieve_bm25_only(self, query: str) -> Tuple[List[Dict], float]:
        """
        Retrieve using BM25 only.
        
        Args:
            query: Search query
            
        Returns:
            Tuple of (results, retrieval_time)
        """
        start = time.time()
        
        results = self.retrieval_pipeline.retrieve(
            query=query,
            top_k=self.top_k,
            method="bm25",
            use_reranking=False
        )
        
        duration = time.time() - start
        return results, duration
    
    def retrieve_hybrid(self, query: str) -> Tuple[List[Dict], float]:
        """
        Retrieve using hybrid (dense + BM25 with RRF).
        
        Args:
            query: Search query
            
        Returns:
            Tuple of (results, retrieval_time)
        """
        start = time.time()
        
        results = self.retrieval_pipeline.retrieve(
            query=query,
            top_k=self.top_k,
            method="hybrid",
            use_reranking=False
        )
        
        duration = time.time() - start
        return results, duration
    
    def retrieve_hybrid_rerank(self, query: str) -> Tuple[List[Dict], float]:
        """
        Retrieve using hybrid + cross-encoder reranking.
        
        Args:
            query: Search query
            
        Returns:
            Tuple of (results, retrieval_time)
        """
        start = time.time()
        
        results = self.retrieval_pipeline.retrieve(
            query=query,
            top_k=self.top_k,
            method="hybrid",
            use_reranking=True
        )
        
        duration = time.time() - start
        return results, duration
    
    def compute_recall_at_k(
        self,
        retrieved_ids: List[str],
        relevant_ids: List[str]
    ) -> float:
        """
        Compute Recall@K.
        
        Args:
            retrieved_ids: IDs of retrieved chunks
            relevant_ids: IDs of relevant chunks
            
        Returns:
            Recall score (0.0 to 1.0)
        """
        if not relevant_ids:
            return 1.0  # No relevant docs means perfect recall
        
        retrieved_set = set(retrieved_ids)
        relevant_set = set(relevant_ids)
        
        hits = len(retrieved_set & relevant_set)
        return hits / len(relevant_set)
    
    def compute_precision_at_k(
        self,
        retrieved_ids: List[str],
        relevant_ids: List[str]
    ) -> float:
        """
        Compute Precision@K.
        
        Args:
            retrieved_ids: IDs of retrieved chunks
            relevant_ids: IDs of relevant chunks
            
        Returns:
            Precision score (0.0 to 1.0)
        """
        if not retrieved_ids:
            return 0.0
        
        retrieved_set = set(retrieved_ids)
        relevant_set = set(relevant_ids)
        
        hits = len(retrieved_set & relevant_set)
        return hits / len(retrieved_ids)
    
    def compute_mrr(
        self,
        retrieved_ids: List[str],
        relevant_ids: List[str]
    ) -> float:
        """
        Compute Mean Reciprocal Rank.
        
        Args:
            retrieved_ids: IDs of retrieved chunks (in order)
            relevant_ids: IDs of relevant chunks
            
        Returns:
            MRR score (0.0 to 1.0)
        """
        relevant_set = set(relevant_ids)
        
        for rank, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in relevant_set:
                return 1.0 / rank
        
        return 0.0
    
    def compute_ndcg_at_k(
        self,
        retrieved_ids: List[str],
        relevant_ids: List[str]
    ) -> float:
        """
        Compute Normalized Discounted Cumulative Gain.
        
        Args:
            retrieved_ids: IDs of retrieved chunks (in order)
            relevant_ids: IDs of relevant chunks
            
        Returns:
            NDCG score (0.0 to 1.0)
        """
        relevant_set = set(relevant_ids)
        
        # DCG: sum of relevance / log2(rank + 1)
        dcg = 0.0
        for rank, doc_id in enumerate(retrieved_ids, start=1):
            relevance = 1.0 if doc_id in relevant_set else 0.0
            dcg += relevance / (rank + 1)  # Simple log approximation
        
        # IDCG: best possible DCG
        idcg = 0.0
        for rank in range(1, min(len(relevant_ids), len(retrieved_ids)) + 1):
            idcg += 1.0 / (rank + 1)
        
        if idcg == 0.0:
            return 0.0
        
        return dcg / idcg
    
    def evaluate_query(
        self,
        question_data: Dict,
        config_name: str,
        retrieve_fn
    ) -> Dict:
        """
        Evaluate a single query with a retrieval configuration.
        
        Args:
            question_data: Question data from evaluation dataset
            config_name: Name of configuration
            retrieve_fn: Retrieval function to use
            
        Returns:
            Evaluation metrics dictionary
        """
        query = question_data["question"]
        
        # Retrieve
        results, duration = retrieve_fn(query)
        
        # Extract retrieved IDs (RetrievalResult objects)
        retrieved_ids = [r.chunk_id for r in results]
        
        # For MVP: match based on document and section keywords
        # In production, you'd have explicit chunk IDs in the evaluation dataset
        relevant_ids = self._find_relevant_chunks(question_data)
        
        # Compute metrics
        metrics = {
            "question_id": question_data["id"],
            "config": config_name,
            "recall_at_k": self.compute_recall_at_k(retrieved_ids, relevant_ids),
            "precision_at_k": self.compute_precision_at_k(retrieved_ids, relevant_ids),
            "mrr": self.compute_mrr(retrieved_ids, relevant_ids),
            "ndcg_at_k": self.compute_ndcg_at_k(retrieved_ids, relevant_ids),
            "retrieval_time": duration,
            "num_retrieved": len(results),
            "num_relevant": len(relevant_ids),
            "retrieved_ids": retrieved_ids[:3]  # Top 3 for inspection
        }
        
        return metrics
    
    def _find_relevant_chunks(self, question_data: Dict) -> List[str]:
        """
        Find relevant chunk IDs based on question metadata.
        
        This is a heuristic for MVP. In production, evaluation dataset
        would include explicit chunk IDs.
        
        Args:
            question_data: Question data
            
        Returns:
            List of relevant chunk IDs
        """
        # Get all chunks from vector store
        all_chunks = self.vector_store.get_all_chunks()
        
        # Filter by document
        doc_name = question_data.get("document", "")
        relevant_sections = question_data.get("relevant_sections", [])
        keywords = question_data.get("keywords", [])
        
        relevant_ids = []
        
        for chunk in all_chunks:
            # Match by document source
            chunk_source = chunk.get("metadata", {}).get("source", "")
            if doc_name not in chunk_source:
                continue
            
            chunk_text = chunk.get("text", "").lower()
            chunk_section = chunk.get("metadata", {}).get("section_title", "").lower()
            
            # Match by section
            section_match = any(
                section.lower() in chunk_section or section.lower() in chunk_text
                for section in relevant_sections
            )
            
            # Match by keywords
            keyword_match = sum(
                1 for kw in keywords
                if kw.lower() in chunk_text
            )
            
            # Consider relevant if section matches or multiple keywords match
            if section_match or keyword_match >= 2:
                chunk_id = chunk.get("id", chunk.get("chunk_id", ""))
                if chunk_id:
                    relevant_ids.append(chunk_id)
        
        return relevant_ids
    
    def run_benchmark(
        self,
        evaluation_file: str = "tests/evaluation/evaluation_dataset.json"
    ) -> Dict:
        """
        Run complete benchmark on evaluation dataset.
        
        Args:
            evaluation_file: Path to evaluation JSON file
            
        Returns:
            Complete benchmark results
        """
        logger.info(f"Loading evaluation dataset from {evaluation_file}")
        
        with open(evaluation_file, 'r', encoding='utf-8') as f:
            eval_data = json.load(f)
        
        questions = eval_data["questions"]
        logger.info(f"Loaded {len(questions)} evaluation questions")
        
        # Configurations to test
        configs = {
            "A_dense_only": self.retrieve_dense_only,
            "B_bm25_only": self.retrieve_bm25_only,
            "C_hybrid": self.retrieve_hybrid,
            "D_hybrid_rerank": self.retrieve_hybrid_rerank
        }
        
        # Run evaluations
        all_results = []
        
        for config_name, retrieve_fn in configs.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"Evaluating configuration: {config_name}")
            logger.info(f"{'='*60}")
            
            config_results = []
            
            for i, question_data in enumerate(questions, 1):
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{len(questions)} questions")
                
                metrics = self.evaluate_query(
                    question_data=question_data,
                    config_name=config_name,
                    retrieve_fn=retrieve_fn
                )
                
                config_results.append(metrics)
            
            all_results.extend(config_results)
            
            # Compute aggregate metrics for this config
            self._print_config_summary(config_name, config_results)
        
        # Save detailed results
        output_file = "tests/evaluation/benchmark_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "top_k": self.top_k,
                    "num_questions": len(questions),
                    "configurations": list(configs.keys())
                },
                "results": all_results
            }, f, indent=2)
        
        logger.info(f"\nDetailed results saved to: {output_file}")
        
        # Generate summary report
        self._generate_summary_report(all_results, configs.keys())
        
        return all_results
    
    def _print_config_summary(self, config_name: str, results: List[Dict]):
        """Print summary statistics for a configuration."""
        if not results:
            return
        
        avg_recall = sum(r["recall_at_k"] for r in results) / len(results)
        avg_precision = sum(r["precision_at_k"] for r in results) / len(results)
        avg_mrr = sum(r["mrr"] for r in results) / len(results)
        avg_ndcg = sum(r["ndcg_at_k"] for r in results) / len(results)
        avg_time = sum(r["retrieval_time"] for r in results) / len(results)
        
        logger.info(f"\nSummary for {config_name}:")
        logger.info(f"  Recall@{self.top_k}:    {avg_recall:.3f}")
        logger.info(f"  Precision@{self.top_k}: {avg_precision:.3f}")
        logger.info(f"  MRR:          {avg_mrr:.3f}")
        logger.info(f"  NDCG@{self.top_k}:      {avg_ndcg:.3f}")
        logger.info(f"  Avg Time:     {avg_time*1000:.1f}ms")
    
    def _generate_summary_report(self, all_results: List[Dict], config_names: List[str]):
        """Generate markdown summary report."""
        report_file = "tests/evaluation/BENCHMARK_REPORT.md"
        
        # Group results by config
        results_by_config = {}
        for result in all_results:
            config = result["config"]
            if config not in results_by_config:
                results_by_config[config] = []
            results_by_config[config].append(result)
        
        # Compute aggregate metrics
        metrics_table = []
        for config in config_names:
            results = results_by_config.get(config, [])
            if not results:
                continue
            
            avg_recall = sum(r["recall_at_k"] for r in results) / len(results)
            avg_precision = sum(r["precision_at_k"] for r in results) / len(results)
            avg_mrr = sum(r["mrr"] for r in results) / len(results)
            avg_ndcg = sum(r["ndcg_at_k"] for r in results) / len(results)
            avg_time = sum(r["retrieval_time"] for r in results) / len(results)
            
            metrics_table.append({
                "config": config,
                "recall": avg_recall,
                "precision": avg_precision,
                "mrr": avg_mrr,
                "ndcg": avg_ndcg,
                "time_ms": avg_time * 1000
            })
        
        # Write report
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Retrieval Quality Benchmark Report\n\n")
            f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Evaluation Questions:** {len(all_results) // len(config_names)}\n\n")
            f.write(f"**Top-K:** {self.top_k}\n\n")
            
            f.write("## Configurations Tested\n\n")
            f.write("- **A_dense_only**: Vector search only\n")
            f.write("- **B_bm25_only**: BM25 sparse search only\n")
            f.write("- **C_hybrid**: Dense + BM25 with RRF fusion\n")
            f.write("- **D_hybrid_rerank**: Hybrid + cross-encoder reranking\n\n")
            
            f.write("## Overall Results\n\n")
            f.write("| Configuration | Recall@5 | Precision@5 | MRR | NDCG@5 | Avg Time (ms) |\n")
            f.write("|--------------|----------|-------------|-----|--------|---------------|\n")
            
            for row in metrics_table:
                f.write(f"| {row['config']} | {row['recall']:.3f} | {row['precision']:.3f} | "
                       f"{row['mrr']:.3f} | {row['ndcg']:.3f} | {row['time_ms']:.1f} |\n")
            
            f.write("\n## Key Findings\n\n")
            
            # Determine best config for each metric
            best_recall = max(metrics_table, key=lambda x: x['recall'])
            best_precision = max(metrics_table, key=lambda x: x['precision'])
            best_mrr = max(metrics_table, key=lambda x: x['mrr'])
            best_ndcg = max(metrics_table, key=lambda x: x['ndcg'])
            fastest = min(metrics_table, key=lambda x: x['time_ms'])
            
            f.write(f"- **Best Recall@5:** {best_recall['config']} ({best_recall['recall']:.3f})\n")
            f.write(f"- **Best Precision@5:** {best_precision['config']} ({best_precision['precision']:.3f})\n")
            f.write(f"- **Best MRR:** {best_mrr['config']} ({best_mrr['mrr']:.3f})\n")
            f.write(f"- **Best NDCG@5:** {best_ndcg['config']} ({best_ndcg['ndcg']:.3f})\n")
            f.write(f"- **Fastest:** {fastest['config']} ({fastest['time_ms']:.1f}ms)\n\n")
            
            f.write("## Interpretation\n\n")
            f.write("- **Recall@K**: Percentage of relevant documents retrieved (higher is better)\n")
            f.write("- **Precision@K**: Percentage of retrieved documents that are relevant (higher is better)\n")
            f.write("- **MRR**: Mean reciprocal rank of first relevant result (higher is better, 1.0 is perfect)\n")
            f.write("- **NDCG@K**: Normalized discounted cumulative gain (accounts for ranking, higher is better)\n")
            f.write("- **Avg Time**: Average retrieval latency in milliseconds\n\n")
            
            f.write("## Detailed Results\n\n")
            f.write("See `benchmark_results.json` for per-question detailed metrics.\n")
        
        logger.info(f"Summary report saved to: {report_file}")


def main():
    """Run retrieval benchmark."""
    logger.info("Starting Retrieval Quality Benchmark")
    logger.info("=" * 70)
    
    benchmark = RetrievalBenchmark(top_k=5)
    results = benchmark.run_benchmark()
    
    logger.info("\n" + "=" * 70)
    logger.info("Benchmark Complete!")
    logger.info("See tests/evaluation/BENCHMARK_REPORT.md for summary")
    logger.info("See tests/evaluation/benchmark_results.json for detailed results")


if __name__ == "__main__":
    main()
