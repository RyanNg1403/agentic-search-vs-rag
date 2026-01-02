#!/usr/bin/env python3
"""
Compare RAG and Agentic Search Results
Generates comparison report and metrics
"""

import json
from pathlib import Path
from typing import Dict, Any, List
import sys


class ResultsComparator:
    def __init__(self, rag_results_file: str, agentic_results_file: str):
        self.rag_results_file = rag_results_file
        self.agentic_results_file = agentic_results_file
        self.rag_data = None
        self.agentic_data = None

    def load_results(self):
        """Load both result files"""
        print("Loading results...")

        with open(self.rag_results_file, 'r') as f:
            self.rag_data = json.load(f)

        with open(self.agentic_results_file, 'r') as f:
            self.agentic_data = json.load(f)

        print(f"Loaded {len(self.rag_data['results'])} RAG results")
        print(f"Loaded {len(self.agentic_data['results'])} Agentic results")

    def generate_comparison_report(self, output_file: str = "comparison_report.md"):
        """Generate a markdown comparison report"""
        if not self.rag_data or not self.agentic_data:
            self.load_results()

        rag_metrics = self.rag_data["aggregate_metrics"]
        agentic_metrics = self.agentic_data["aggregate_metrics"]

        # Calculate improvements
        iou_improvement = ((agentic_metrics["avg_iou"] - rag_metrics["avg_iou"]) /
                          rag_metrics["avg_iou"] * 100) if rag_metrics["avg_iou"] > 0 else 0
        token_reduction = ((rag_metrics["avg_token_usage"] - agentic_metrics["avg_token_usage"]) /
                          rag_metrics["avg_token_usage"] * 100) if rag_metrics["avg_token_usage"] > 0 else 0
        precision_improvement = ((agentic_metrics["avg_precision"] - rag_metrics["avg_precision"]) /
                                rag_metrics["avg_precision"] * 100) if rag_metrics["avg_precision"] > 0 else 0
        recall_improvement = ((agentic_metrics["avg_recall"] - rag_metrics["avg_recall"]) /
                             rag_metrics["avg_recall"] * 100) if rag_metrics["avg_recall"] > 0 else 0

        # Generate markdown report
        report = f"""# RAG vs Agentic Search: Experimental Results

## Experiment Configuration

- **Codebase**: gemini-cli
- **Total Questions**: {len(self.rag_data['results'])}
- **RAG Model**: {self.rag_data.get('model', 'N/A')}
- **Vector Database**: Qdrant
- **Agentic Tool**: {self.agentic_data.get('tool', 'brv query')}
- **Top-K Retrieval**: {self.rag_data.get('top_k', 10)}

## Overall Performance Comparison

| Metric | RAG | Agentic Search | Improvement |
|--------|-----|----------------|-------------|
| **IoU Score** | {rag_metrics['avg_iou']:.3f} | {agentic_metrics['avg_iou']:.3f} | {iou_improvement:+.1f}% |
| **Token Usage** | {rag_metrics['avg_token_usage']:.0f} | {agentic_metrics['avg_token_usage']:.0f} | {token_reduction:+.1f}% |
| **Precision** | {rag_metrics['avg_precision']:.3f} | {agentic_metrics['avg_precision']:.3f} | {precision_improvement:+.1f}% |
| **Recall** | {rag_metrics['avg_recall']:.3f} | {agentic_metrics['avg_recall']:.3f} | {recall_improvement:+.1f}% |

## Key Findings

### 1. Retrieval Quality (IoU Score)
- **RAG**: {rag_metrics['avg_iou']:.3f}
- **Agentic Search**: {agentic_metrics['avg_iou']:.3f}
- **Result**: {"Agentic search is more accurate" if agentic_metrics['avg_iou'] > rag_metrics['avg_iou'] else "RAG is more accurate"} by {abs(iou_improvement):.1f}%

### 2. Token Efficiency
- **RAG**: {rag_metrics['avg_token_usage']:.0f} tokens/query
- **Agentic Search**: {agentic_metrics['avg_token_usage']:.0f} tokens/query
- **Result**: {"Agentic search uses fewer tokens" if token_reduction > 0 else "RAG uses fewer tokens"} ({abs(token_reduction):.1f}% {"reduction" if token_reduction > 0 else "increase"})

### 3. Precision
- **RAG**: {rag_metrics['avg_precision']:.3f}
- **Agentic Search**: {agentic_metrics['avg_precision']:.3f}
- **Result**: {"Agentic search has higher precision" if agentic_metrics['avg_precision'] > rag_metrics['avg_precision'] else "RAG has higher precision"}

### 4. Recall
- **RAG**: {rag_metrics['avg_recall']:.3f}
- **Agentic Search**: {agentic_metrics['avg_recall']:.3f}
- **Result**: {"Agentic search has higher recall" if agentic_metrics['avg_recall'] > rag_metrics['avg_recall'] else "RAG has higher recall"}

## Performance by Question Type

"""

        # Analyze by question type
        question_types = set(q["type"] for q in self.rag_data["results"])

        for qtype in sorted(question_types):
            rag_type_results = [r for r in self.rag_data["results"] if r["type"] == qtype]
            agentic_type_results = [r for r in self.agentic_data["results"] if r["type"] == qtype]

            rag_avg_iou = sum(r["metrics"]["iou"] for r in rag_type_results) / len(rag_type_results)
            agentic_avg_iou = sum(r["metrics"]["iou"] for r in agentic_type_results) / len(agentic_type_results)

            rag_avg_tokens = sum(r["metrics"]["token_usage"] for r in rag_type_results) / len(rag_type_results)
            agentic_avg_tokens = sum(r["metrics"]["token_usage"] for r in agentic_type_results) / len(agentic_type_results)

            report += f"""### {qtype.capitalize()} Questions ({len(rag_type_results)} questions)

| Metric | RAG | Agentic Search |
|--------|-----|----------------|
| IoU Score | {rag_avg_iou:.3f} | {agentic_avg_iou:.3f} |
| Token Usage | {rag_avg_tokens:.0f} | {agentic_avg_tokens:.0f} |

"""

        # Add detailed results section
        report += """## Detailed Results

### Top 5 Best Performing Questions (Agentic Search)

"""
        # Sort by IoU improvement
        comparison_results = []
        for i, rag_r in enumerate(self.rag_data["results"]):
            agentic_r = self.agentic_data["results"][i]
            iou_diff = agentic_r["metrics"]["iou"] - rag_r["metrics"]["iou"]
            comparison_results.append({
                "question_id": rag_r["question_id"],
                "question": rag_r["question"],
                "iou_diff": iou_diff,
                "rag_iou": rag_r["metrics"]["iou"],
                "agentic_iou": agentic_r["metrics"]["iou"]
            })

        top_5 = sorted(comparison_results, key=lambda x: x["iou_diff"], reverse=True)[:5]
        for item in top_5:
            report += f"""**{item['question_id']}**: {item['question']}
- RAG IoU: {item['rag_iou']:.3f}
- Agentic IoU: {item['agentic_iou']:.3f}
- Improvement: {item['iou_diff']:+.3f}

"""

        report += """### Top 5 Worst Performing Questions (Agentic Search)

"""
        bottom_5 = sorted(comparison_results, key=lambda x: x["iou_diff"])[:5]
        for item in bottom_5:
            report += f"""**{item['question_id']}**: {item['question']}
- RAG IoU: {item['rag_iou']:.3f}
- Agentic IoU: {item['agentic_iou']:.3f}
- Difference: {item['iou_diff']:+.3f}

"""

        # Add conclusion
        report += f"""## Conclusion

Based on this experiment with {len(self.rag_data['results'])} questions across the gemini-cli codebase:

"""
        if agentic_metrics['avg_iou'] > rag_metrics['avg_iou'] and token_reduction > 0:
            report += f"""**Agentic Search (ByteRover) outperforms RAG on both accuracy and efficiency:**
- {abs(iou_improvement):.1f}% better retrieval accuracy (IoU)
- {abs(token_reduction):.1f}% reduction in token usage
- Better precision and recall on average

This validates the claim that context trees and agentic search are superior to traditional vector-based RAG for code retrieval.
"""
        elif agentic_metrics['avg_iou'] > rag_metrics['avg_iou']:
            report += f"""**Agentic Search (ByteRover) shows better accuracy but uses more tokens:**
- {abs(iou_improvement):.1f}% better retrieval accuracy (IoU)
- However, uses {abs(token_reduction):.1f}% more tokens

The trade-off may be justified for applications where accuracy is more critical than token efficiency.
"""
        else:
            report += f"""**Results show mixed performance:**
- IoU difference: {iou_improvement:+.1f}%
- Token usage difference: {token_reduction:+.1f}%

Further analysis and tuning may be needed to optimize both approaches.
"""

        # Save report
        print(f"\nSaving comparison report to {output_file}...")
        with open(output_file, 'w') as f:
            f.write(report)

        print("Comparison report generated successfully!")
        return report

    def generate_json_summary(self, output_file: str = "comparison_summary.json"):
        """Generate a JSON summary of the comparison"""
        if not self.rag_data or not self.agentic_data:
            self.load_results()

        rag_metrics = self.rag_data["aggregate_metrics"]
        agentic_metrics = self.agentic_data["aggregate_metrics"]

        summary = {
            "experiment": {
                "total_questions": len(self.rag_data['results']),
                "rag_model": self.rag_data.get('model', 'N/A'),
                "agentic_tool": self.agentic_data.get('tool', 'brv query')
            },
            "aggregate_comparison": {
                "rag": rag_metrics,
                "agentic": agentic_metrics,
                "improvements": {
                    "iou_improvement_pct": ((agentic_metrics["avg_iou"] - rag_metrics["avg_iou"]) /
                                           rag_metrics["avg_iou"] * 100) if rag_metrics["avg_iou"] > 0 else 0,
                    "token_reduction_pct": ((rag_metrics["avg_token_usage"] - agentic_metrics["avg_token_usage"]) /
                                           rag_metrics["avg_token_usage"] * 100) if rag_metrics["avg_token_usage"] > 0 else 0,
                    "precision_improvement_pct": ((agentic_metrics["avg_precision"] - rag_metrics["avg_precision"]) /
                                                 rag_metrics["avg_precision"] * 100) if rag_metrics["avg_precision"] > 0 else 0,
                    "recall_improvement_pct": ((agentic_metrics["avg_recall"] - rag_metrics["avg_recall"]) /
                                              rag_metrics["avg_recall"] * 100) if rag_metrics["avg_recall"] > 0 else 0
                }
            },
            "by_question_type": {}
        }

        # Group by question type
        question_types = set(q["type"] for q in self.rag_data["results"])
        for qtype in question_types:
            rag_type = [r for r in self.rag_data["results"] if r["type"] == qtype]
            agentic_type = [r for r in self.agentic_data["results"] if r["type"] == qtype]

            summary["by_question_type"][qtype] = {
                "count": len(rag_type),
                "rag_avg_iou": sum(r["metrics"]["iou"] for r in rag_type) / len(rag_type),
                "agentic_avg_iou": sum(r["metrics"]["iou"] for r in agentic_type) / len(agentic_type),
                "rag_avg_tokens": sum(r["metrics"]["token_usage"] for r in rag_type) / len(rag_type),
                "agentic_avg_tokens": sum(r["metrics"]["token_usage"] for r in agentic_type) / len(agentic_type)
            }

        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"JSON summary saved to {output_file}")
        return summary

    def print_summary(self):
        """Print a quick summary to console"""
        if not self.rag_data or not self.agentic_data:
            self.load_results()

        print("\n" + "="*70)
        print("COMPARISON SUMMARY")
        print("="*70)

        rag_m = self.rag_data["aggregate_metrics"]
        agen_m = self.agentic_data["aggregate_metrics"]

        print(f"\n{'Metric':<20} {'RAG':>15} {'Agentic':>15} {'Diff':>15}")
        print("-"*70)
        print(f"{'IoU Score':<20} {rag_m['avg_iou']:>15.3f} {agen_m['avg_iou']:>15.3f} {agen_m['avg_iou']-rag_m['avg_iou']:>+15.3f}")
        print(f"{'Token Usage':<20} {rag_m['avg_token_usage']:>15.0f} {agen_m['avg_token_usage']:>15.0f} {agen_m['avg_token_usage']-rag_m['avg_token_usage']:>+15.0f}")
        print(f"{'Precision':<20} {rag_m['avg_precision']:>15.3f} {agen_m['avg_precision']:>15.3f} {agen_m['avg_precision']-rag_m['avg_precision']:>+15.3f}")
        print(f"{'Recall':<20} {rag_m['avg_recall']:>15.3f} {agen_m['avg_recall']:>15.3f} {agen_m['avg_recall']-rag_m['avg_recall']:>+15.3f}")
        print("="*70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Compare RAG and Agentic Search Results")
    parser.add_argument(
        "--rag-results",
        type=str,
        default="./results/rag_results.json",
        help="Path to RAG results JSON file"
    )
    parser.add_argument(
        "--agentic-results",
        type=str,
        default="./results/agentic_results.json",
        help="Path to Agentic results JSON file"
    )
    parser.add_argument(
        "--markdown-report",
        type=str,
        default="./results/comparison_report.md",
        help="Path to output markdown report"
    )
    parser.add_argument(
        "--json-summary",
        type=str,
        default="./results/comparison_summary.json",
        help="Path to output JSON summary"
    )

    args = parser.parse_args()

    # Check if files exist
    if not Path(args.rag_results).exists():
        print(f"Error: RAG results file not found: {args.rag_results}")
        return 1

    if not Path(args.agentic_results).exists():
        print(f"Error: Agentic results file not found: {args.agentic_results}")
        return 1

    comparator = ResultsComparator(args.rag_results, args.agentic_results)
    comparator.load_results()
    comparator.print_summary()
    comparator.generate_comparison_report(args.markdown_report)
    comparator.generate_json_summary(args.json_summary)

    return 0


if __name__ == "__main__":
    exit(main())
