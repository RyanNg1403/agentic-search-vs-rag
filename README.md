# RAG vs Agentic Search: Experimental Validation

A reproducible experiment comparing traditional vector-based RAG with **Agentic Search** (context trees) for code retrieval tasks.

## Overview

Most coding agents use vector embeddings and similarity search to retrieve code context. This works well for natural language but fails for code because **code is a graph, not a "bag of words."**

This experiment validates that context trees with agentic search dramatically outperform traditional RAG for code understanding tasks.

**Key Results:**
- 🚀 **99% fewer tokens** used per query
- ✅ **2× better retrieval accuracy** (IoU score)
- 🎯 **2.2× higher precision** in finding relevant files

## Quick Links

- 📊 **[Detailed Results & Analysis](RESULTS.md)** - Complete experimental findings with visualizations
- 🔬 **[Reproduction Guide](REPRODUCTION.md)** - Step-by-step instructions to reproduce the experiment
- 🌐 **[ByteRover](https://www.byterover.dev/?source=rdgemini1)** - The agentic search tool used in this experiment
- 📝 **Blog Post** - _(Coming soon)_ Full write-up of our findings

## What's Inside

This repository provides:
- 30 carefully designed evaluation questions with ground truth
- Complete RAG pipeline (OpenAI embeddings + Qdrant)
- Complete Agentic Search pipeline (ByteRover CLI)
- Automated comparison and visualization scripts
- Pre-curated context tree for reproducibility

## Repository Structure

```
.
├── README.md                      # This file
├── RESULTS.md                     # Detailed experimental findings
├── REPRODUCTION.md                # Reproduction guide
├── questions.json                 # 30 evaluation questions
├── context-tree/                  # Pre-curated knowledge base
├── rag_pipeline.py                # RAG implementation
├── agentic_pipeline.py            # Agentic search implementation
├── compare_results.py             # Metrics calculation
├── visualize_results.py           # Chart generation
└── gemini-cli/                    # Target codebase (clone separately)
```

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/RyanNg1403/agentic-search-vs-rag.git
cd agentic-search-vs-rag

# 2. Run automated experiment
./run_experiment.sh
```

See [REPRODUCTION.md](REPRODUCTION.md) for detailed instructions.

## Citation

```
RAG for code is broken because Code is a Graph, not a "Bag of Words."
ByteRover, 2025
```

## License

MIT License
