#!/usr/bin/env python3
"""
Agentic Search Pipeline using ByteRover
Uses brv query commands to retrieve relevant files
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Set
import tiktoken
from tqdm import tqdm


class AgenticPipeline:
    def __init__(
        self,
        codebase_path: str,
        max_files: int = 10
    ):
        self.codebase_path = Path(codebase_path)
        self.max_files = max_files

        # Initialize tokenizer for token counting
        try:
            self.token_counter = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            print(f"Warning: Could not load tiktoken: {e}")
            self.token_counter = None

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.token_counter:
            return len(self.token_counter.encode(text))
        else:
            # Fallback: approximate 4 chars per token
            return len(text) // 4

    def run_brv_query(self, question: str) -> str:
        """Run brv query command and return the response"""
        # Craft a prompt that enforces strict file path listing
        enhanced_query = f"""{question}

CRITICAL INSTRUCTIONS - YOU MUST FOLLOW THESE EXACTLY:

1. Answer the question using knowledge from the context tree
2. List ALL relevant SOURCE CODE file paths (up to {self.max_files} files maximum)
3. ONLY include actual source code files (packages/, scripts/, schemas/, etc.)
4. NEVER include .brv/context-tree/ files - these are NOT source code
5. Format EVERY file path on a new line starting with "FILE:" prefix

REQUIRED FORMAT (copy this exactly):
FILE: packages/core/src/example.ts
FILE: packages/cli/src/components/App.tsx
FILE: scripts/build.js

EXAMPLE QUESTION: "Where is OAuth2 implemented?"
EXAMPLE RESPONSE:
OAuth2 authentication is implemented in the code_assist module using Google's OAuth2Client library.

FILE: packages/core/src/code_assist/oauth2.ts
FILE: packages/core/src/config/config.ts

DO NOT include .brv/ paths. Only list actual source code files."""

        try:
            # Run brv query in the codebase directory
            result = subprocess.run(
                ["brv", "query", enhanced_query],
                cwd=str(self.codebase_path),
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                print(f"Error running brv query: {result.stderr}")
                return ""

            return result.stdout
        except subprocess.TimeoutExpired:
            print("brv query timed out")
            return ""
        except Exception as e:
            print(f"Error running brv query: {e}")
            return ""

    def extract_file_paths(self, response: str) -> List[str]:
        """Extract file paths from brv query response"""
        file_paths = []

        # Method 1: Look for lines starting with "FILE:"
        file_pattern = re.compile(r'^FILE:\s*(.+)$', re.MULTILINE)
        matches = file_pattern.findall(response)
        file_paths.extend([m.strip() for m in matches])

        # Method 2: Look for common path patterns if no FILE: markers found
        if not file_paths:
            # Match paths like packages/core/src/file.ts
            path_pattern = re.compile(
                r'\b((?:packages|scripts|docs|integration-tests|schemas)/[a-zA-Z0-9_\-/\.]+\.[a-zA-Z]{2,4})\b'
            )
            matches = path_pattern.findall(response)
            file_paths.extend(matches)

        # Method 3: Look for markdown code blocks with file paths
        if not file_paths:
            code_block_pattern = re.compile(r'`([^`]+\.[a-zA-Z]{2,4})`')
            matches = code_block_pattern.findall(response)
            # Filter to only include paths with slashes
            file_paths.extend([m for m in matches if '/' in m])

        # Remove duplicates while preserving order and filter out .brv paths
        seen = set()
        unique_paths = []
        for path in file_paths:
            # Normalize path
            normalized = path.strip().replace('\\', '/')
            # Filter out .brv context tree files (only keep source code files)
            if normalized and normalized not in seen and not normalized.startswith('.brv/'):
                seen.add(normalized)
                unique_paths.append(normalized)

        # Limit to max_files
        return unique_paths[:self.max_files]

    def read_file_content(self, file_path: str) -> str:
        """Read content of a file for token counting"""
        try:
            full_path = self.codebase_path / file_path
            if full_path.exists() and full_path.is_file():
                return full_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        return ""

    def run_evaluation(self, questions_file: str, output_file: str):
        """Run evaluation on questions and save results"""
        print(f"Loading questions from {questions_file}...")
        with open(questions_file, 'r') as f:
            questions_data = json.load(f)

        questions = questions_data["questions"]
        results = []

        print(f"Processing {len(questions)} questions...")
        for question in tqdm(questions, desc="Evaluating questions"):
            # Run brv query
            response = self.run_brv_query(question["question"])

            if not response:
                print(f"Warning: No response for question {question['id']}")
                results.append({
                    "question_id": question["id"],
                    "question": question["question"],
                    "type": question["type"],
                    "ground_truth": question["ground_truth"],
                    "retrieved": [],
                    "response": "",
                    "metrics": {
                        "iou": 0.0,
                        "token_usage": 0,
                        "precision": 0.0,
                        "recall": 0.0
                    }
                })
                continue

            # Extract file paths from response
            retrieved_paths = self.extract_file_paths(response)

            # Count tokens in the entire response
            response_tokens = self.count_tokens(response)

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
                "response": response,
                "metrics": {
                    "iou": iou_score,
                    "token_usage": response_tokens,
                    "precision": intersection / len(retrieved_set) if retrieved_set else 0,
                    "recall": intersection / len(ground_truth) if ground_truth else 0
                }
            }
            results.append(result)

            # Print summary for this question
            print(f"\nQ{question['id']}: IoU={iou_score:.3f}, "
                  f"Tokens={response_tokens}, "
                  f"Retrieved={len(retrieved_paths)} files")

        # Calculate aggregate metrics
        avg_iou = sum(r["metrics"]["iou"] for r in results) / len(results) if results else 0
        avg_tokens = sum(r["metrics"]["token_usage"] for r in results) / len(results) if results else 0
        avg_precision = sum(r["metrics"]["precision"] for r in results) / len(results) if results else 0
        avg_recall = sum(r["metrics"]["recall"] for r in results) / len(results) if results else 0

        output_data = {
            "approach": "Agentic Search (ByteRover)",
            "tool": "brv query",
            "max_files": self.max_files,
            "aggregate_metrics": {
                "avg_iou": avg_iou,
                "avg_token_usage": avg_tokens,
                "avg_precision": avg_precision,
                "avg_recall": avg_recall
            },
            "results": results
        }

        print(f"\nSaving results to {output_file}...")
        # Create results directory if it doesn't exist
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        print("\n=== Agentic Search Pipeline Results ===")
        print(f"Average IoU: {avg_iou:.3f}")
        print(f"Average Token Usage: {avg_tokens:.0f}")
        print(f"Average Precision: {avg_precision:.3f}")
        print(f"Average Recall: {avg_recall:.3f}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Agentic Search Pipeline using ByteRover")
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
        default="./results/agentic_results.json",
        help="Path to output results JSON file"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=10,
        help="Maximum number of files to retrieve per question"
    )

    args = parser.parse_args()

    # Verify brv is available
    try:
        subprocess.run(["brv", "--help"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: 'brv' command not found. Please ensure ByteRover CLI is installed.")
        return 1

    # Verify codebase directory exists
    if not Path(args.codebase).exists():
        print(f"Error: Codebase directory not found: {args.codebase}")
        return 1

    # Verify brv is initialized in codebase
    brv_dir = Path(args.codebase) / ".brv"
    if not brv_dir.exists():
        print(f"Error: ByteRover not initialized in {args.codebase}. Run 'brv init' first.")
        return 1

    pipeline = AgenticPipeline(
        codebase_path=args.codebase,
        max_files=args.max_files
    )

    pipeline.run_evaluation(args.questions, args.output)
    return 0


if __name__ == "__main__":
    exit(main())
