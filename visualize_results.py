#!/usr/bin/env python3
"""
Visualize RAG vs Agentic Search Comparison Results
Creates bar plots comparing token usage, precision, recall, and IoU
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def load_comparison_data(comparison_file: str):
    """Load comparison summary JSON"""
    with open(comparison_file, 'r') as f:
        return json.load(f)


def create_comparison_plots(data: dict, output_dir: str = "./results"):
    """Create 4 comparison plots and save as PNG"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Extract metrics
    rag_metrics = data["aggregate_comparison"]["rag"]
    agentic_metrics = data["aggregate_comparison"]["agentic"]

    # Set style
    plt.style.use('seaborn-v0_8-darkgrid')
    colors = ['#3498db', '#e74c3c']  # Blue for RAG, Red for Agentic

    # Common figure settings
    fig_width = 10
    fig_height = 6

    # 1. Token Usage Comparison
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    approaches = ['RAG', 'Agentic Search']
    token_values = [rag_metrics['avg_token_usage'], agentic_metrics['avg_token_usage']]

    bars = ax.bar(approaches, token_values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

    # Add value labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom', fontsize=14, fontweight='bold')

    ax.set_ylabel('Average Token Usage', fontsize=14, fontweight='bold')
    ax.set_title('Token Usage Comparison: RAG vs Agentic Search', fontsize=16, fontweight='bold', pad=20)
    ax.grid(axis='y', alpha=0.3)

    # Add improvement annotation
    improvement = data["aggregate_comparison"]["improvements"]["token_reduction_pct"]
    ax.text(0.75, 0.95, f'Token Reduction: {improvement:+.1f}%',
            transform=ax.transAxes, ha='center', va='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path / 'token_usage_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {output_path / 'token_usage_comparison.png'}")

    # 2. Precision Comparison
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    precision_values = [rag_metrics['avg_precision'], agentic_metrics['avg_precision']]

    bars = ax.bar(approaches, precision_values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}',
                ha='center', va='bottom', fontsize=14, fontweight='bold')

    ax.set_ylabel('Average Precision', fontsize=14, fontweight='bold')
    ax.set_title('Precision Comparison: RAG vs Agentic Search', fontsize=16, fontweight='bold', pad=20)
    ax.set_ylim(0, max(precision_values) * 1.25)
    ax.grid(axis='y', alpha=0.3)

    improvement = data["aggregate_comparison"]["improvements"]["precision_improvement_pct"]
    ax.text(0.5, 0.95, f'Precision Improvement: {improvement:+.1f}%',
            transform=ax.transAxes, ha='center', va='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path / 'precision_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {output_path / 'precision_comparison.png'}")

    # 3. Recall Comparison
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    recall_values = [rag_metrics['avg_recall'], agentic_metrics['avg_recall']]

    bars = ax.bar(approaches, recall_values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}',
                ha='center', va='bottom', fontsize=14, fontweight='bold')

    ax.set_ylabel('Average Recall', fontsize=14, fontweight='bold')
    ax.set_title('Recall Comparison: RAG vs Agentic Search', fontsize=16, fontweight='bold', pad=20)
    ax.set_ylim(0, max(recall_values) * 1.25)
    ax.grid(axis='y', alpha=0.3)

    improvement = data["aggregate_comparison"]["improvements"]["recall_improvement_pct"]
    ax.text(0.5, 0.95, f'Recall Improvement: {improvement:+.1f}%',
            transform=ax.transAxes, ha='center', va='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path / 'recall_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {output_path / 'recall_comparison.png'}")

    # 4. IoU Comparison
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    iou_values = [rag_metrics['avg_iou'], agentic_metrics['avg_iou']]

    bars = ax.bar(approaches, iou_values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}',
                ha='center', va='bottom', fontsize=14, fontweight='bold')

    ax.set_ylabel('Average IoU Score', fontsize=14, fontweight='bold')
    ax.set_title('IoU Score Comparison: RAG vs Agentic Search', fontsize=16, fontweight='bold', pad=20)
    ax.set_ylim(0, max(iou_values) * 1.25)
    ax.grid(axis='y', alpha=0.3)

    improvement = data["aggregate_comparison"]["improvements"]["iou_improvement_pct"]
    ax.text(0.5, 0.95, f'IoU Improvement: {improvement:+.1f}%',
            transform=ax.transAxes, ha='center', va='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path / 'iou_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {output_path / 'iou_comparison.png'}")

    # 5. Bonus: All Metrics Combined (4 subplots in one figure)
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('RAG vs Agentic Search: Complete Comparison', fontsize=18, fontweight='bold')

    metrics = [
        ('Token Usage', [rag_metrics['avg_token_usage'], agentic_metrics['avg_token_usage']],
         'token_reduction_pct', False),
        ('Precision', precision_values, 'precision_improvement_pct', True),
        ('Recall', recall_values, 'recall_improvement_pct', True),
        ('IoU Score', iou_values, 'iou_improvement_pct', True)
    ]

    for idx, (metric_name, values, improvement_key, use_ylim) in enumerate(metrics):
        row = idx // 2
        col = idx % 2
        ax = axes[row, col]

        bars = ax.bar(approaches, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            if metric_name == 'Token Usage':
                label = f'{int(height):,}'
            else:
                label = f'{height:.3f}'
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    label, ha='center', va='bottom', fontsize=12, fontweight='bold')

        ax.set_ylabel(f'Average {metric_name}', fontsize=12, fontweight='bold')
        ax.set_title(metric_name, fontsize=14, fontweight='bold', pad=10)
        if use_ylim:
            ax.set_ylim(0, max(values) * 1.25)
        ax.grid(axis='y', alpha=0.3)

        # Add improvement
        improvement = data["aggregate_comparison"]["improvements"][improvement_key]
        improvement_text = f'{improvement:+.1f}%'
        ax.text(0.5, 0.95, improvement_text,
                transform=ax.transAxes, ha='center', va='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path / 'all_metrics_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {output_path / 'all_metrics_comparison.png'}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Visualize RAG vs Agentic Search Results")
    parser.add_argument(
        "--comparison-summary",
        type=str,
        default="./results/comparison_summary.json",
        help="Path to comparison summary JSON file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./visualizations",
        help="Directory to save visualization PNG files"
    )

    args = parser.parse_args()

    # Check if comparison file exists
    if not Path(args.comparison_summary).exists():
        print(f"Error: Comparison summary file not found: {args.comparison_summary}")
        print("Please run compare_results.py first to generate the summary.")
        return 1

    print("Loading comparison data...")
    data = load_comparison_data(args.comparison_summary)

    print("\nGenerating visualizations...")
    create_comparison_plots(data, args.output_dir)

    print("\n" + "="*60)
    print("Visualizations created successfully!")
    print("="*60)
    print(f"\nOutput directory: {args.output_dir}/")
    print("\nGenerated plots:")
    print("  1. token_usage_comparison.png")
    print("  2. precision_comparison.png")
    print("  3. recall_comparison.png")
    print("  4. iou_comparison.png")
    print("  5. all_metrics_comparison.png (bonus)")
    print("\n")

    return 0


if __name__ == "__main__":
    exit(main())
