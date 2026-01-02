#!/usr/bin/env python3
"""
RAG Pipeline for Code Question Answering
Uses Qdrant vector database with OpenAI text-embedding-3-small
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
import tiktoken
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Load environment variables
load_dotenv()


class RAGPipeline:
    def __init__(
        self,
        codebase_path: str,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "gemini_cli_code",
        model_name: str = "text-embedding-3-small",
        top_k: int = 10
    ):
        self.codebase_path = Path(codebase_path)
        self.collection_name = collection_name
        self.top_k = top_k
        self.model_name = model_name
        self.embedding_dim = 1536  # text-embedding-3-small dimension

        # Initialize Qdrant client
        print(f"Connecting to Qdrant at {qdrant_host}:{qdrant_port}...")
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)

        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.openai_client = OpenAI(api_key=api_key)
        print(f"Using OpenAI embedding model: {model_name}")

        # Initialize tokenizer for token counting
        try:
            self.token_counter = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            print(f"Warning: Could not load tiktoken: {e}")
            self.token_counter = None

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        if self.token_counter:
            return len(self.token_counter.encode(text))
        else:
            # Fallback: approximate 4 chars per token
            return len(text) // 4

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a given text using OpenAI API"""
        # OpenAI has a max input of ~8191 tokens for embeddings
        # Truncate if needed
        if self.token_counter:
            tokens = self.token_counter.encode(text)
            if len(tokens) > 8191:
                text = self.token_counter.decode(tokens[:8191])

        response = self.openai_client.embeddings.create(
            input=text,
            model=self.model_name
        )

        return response.data[0].embedding

    def collect_code_files(self) -> List[Dict[str, str]]:
        """Collect code and config files from codebase using extension allowlist"""
        # Only index these file types
        allowed_extensions = {
            '.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs',  # Code
            '.json', '.toml', '.yaml', '.yml',              # Config
            '.sh'                                            # Scripts
        }

        # Skip these directories for performance
        ignore_dirs = {
            "node_modules", ".git", "dist", "build", ".next", ".cache",
            "__pycache__", "coverage", ".vscode", ".idea", "qdrant_storage",
            ".brv"
        }

        code_files = []
        print(f"Collecting code files from {self.codebase_path}...")

        for file_path in self.codebase_path.rglob("*"):
            # Skip directories
            if file_path.is_dir():
                continue

            # Skip ignored directories
            if any(ignored in file_path.parts for ignored in ignore_dirs):
                continue

            # Only include allowed extensions
            if file_path.suffix not in allowed_extensions:
                continue

            # Try to read as text file
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                relative_path = str(file_path.relative_to(self.codebase_path))

                code_files.append({
                    "path": relative_path,
                    "content": content
                })
            except Exception as e:
                # Skip files that can't be read
                continue

        print(f"Collected {len(code_files)} code files")
        return code_files

    def create_collection(self):
        """Create or recreate Qdrant collection"""
        print(f"Creating collection: {self.collection_name}...")

        # Delete collection if exists
        try:
            self.qdrant_client.delete_collection(collection_name=self.collection_name)
            print("Deleted existing collection")
        except:
            pass

        # Create new collection
        self.qdrant_client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE)
        )
        print("Collection created successfully")

    def index_codebase(self):
        """Index all code files into Qdrant"""
        code_files = self.collect_code_files()

        if not code_files:
            raise ValueError("No code files found to index")

        self.create_collection()

        print(f"Indexing {len(code_files)} files...")
        batch_size = 10
        points = []

        for idx, file_info in enumerate(tqdm(code_files, desc="Embedding files")):
            try:
                # Create embedding
                embedding = self.embed_text(file_info["content"])

                # Create point
                point = PointStruct(
                    id=idx,
                    vector=embedding,
                    payload={
                        "path": file_info["path"],
                        "content": file_info["content"][:1000],  # Store preview
                        "full_content": file_info["content"]  # Store full content for token counting
                    }
                )
                points.append(point)

                # Upload in batches
                if len(points) >= batch_size:
                    self.qdrant_client.upsert(
                        collection_name=self.collection_name,
                        points=points
                    )
                    points = []
            except Exception as e:
                print(f"Error indexing {file_info['path']}: {e}")
                continue

        # Upload remaining points
        if points:
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )

        print("Indexing complete!")

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve top-k files for a query"""
        query_embedding = self.embed_text(query)

        results = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=self.top_k
        ).points

        retrieved_files = []
        for result in results:
            retrieved_files.append({
                "path": result.payload["path"],
                "score": result.score,
                "content": result.payload["full_content"]
            })

        return retrieved_files

    def run_evaluation(self, questions_file: str, output_file: str):
        """Run evaluation on questions and save results"""
        print(f"Loading questions from {questions_file}...")
        with open(questions_file, 'r') as f:
            questions_data = json.load(f)

        questions = questions_data["questions"]
        results = []

        print(f"Processing {len(questions)} questions...")
        for question in tqdm(questions, desc="Evaluating questions"):
            # Retrieve relevant files
            retrieved = self.retrieve(question["question"])
            retrieved_paths = [r["path"] for r in retrieved]

            # Calculate token usage (sum of all retrieved file contents)
            total_tokens = sum(
                self.count_tokens(r["content"])
                for r in retrieved
            )

            # Calculate intersection over union metric
            ground_truth = set(question["ground_truth"])
            retrieved_set = set(retrieved_paths)

            intersection = len(ground_truth & retrieved_set)
            union = len(ground_truth | retrieved_set)
            iou_score = intersection / union if union > 0 else 0

            result = {
                "question_id": question["id"],
                "question": question["question"],
                "type": question["type"],
                "ground_truth": question["ground_truth"],
                "retrieved": retrieved_paths,
                "metrics": {
                    "iou": iou_score,
                    "token_usage": total_tokens,
                    "precision": intersection / len(retrieved_set) if retrieved_set else 0,
                    "recall": intersection / len(ground_truth) if ground_truth else 0
                }
            }
            results.append(result)

        # Calculate aggregate metrics
        avg_iou = sum(r["metrics"]["iou"] for r in results) / len(results)
        avg_tokens = sum(r["metrics"]["token_usage"] for r in results) / len(results)
        avg_precision = sum(r["metrics"]["precision"] for r in results) / len(results)
        avg_recall = sum(r["metrics"]["recall"] for r in results) / len(results)

        output_data = {
            "approach": "RAG",
            "model": self.model_name,
            "top_k": self.top_k,
            "aggregate_metrics": {
                "avg_iou": avg_iou,
                "avg_token_usage": avg_tokens,
                "avg_precision": avg_precision,
                "avg_recall": avg_recall
            },
            "results": results
        }

        print(f"Saving results to {output_file}...")
        # Create results directory if it doesn't exist
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        print("\n=== RAG Pipeline Results ===")
        print(f"Average IoU: {avg_iou:.3f}")
        print(f"Average Token Usage: {avg_tokens:.0f}")
        print(f"Average Precision: {avg_precision:.3f}")
        print(f"Average Recall: {avg_recall:.3f}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="RAG Pipeline for Code Question Answering")
    parser.add_argument(
        "--codebase",
        type=str,
        default="./gemini-cli",
        help="Path to codebase directory"
    )
    parser.add_argument(
        "--questions",
        type=str,
        default="./questions.json",
        help="Path to questions JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./results/rag_results.json",
        help="Path to output results JSON file"
    )
    parser.add_argument(
        "--index-only",
        action="store_true",
        help="Only index the codebase, don't run evaluation"
    )
    parser.add_argument(
        "--eval-only",
        action="store_true",
        help="Only run evaluation, assume codebase is already indexed"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of top results to retrieve"
    )

    args = parser.parse_args()

    pipeline = RAGPipeline(
        codebase_path=args.codebase,
        top_k=args.top_k
    )

    if not args.eval_only:
        pipeline.index_codebase()

    if not args.index_only:
        pipeline.run_evaluation(args.questions, args.output)


if __name__ == "__main__":
    main()
