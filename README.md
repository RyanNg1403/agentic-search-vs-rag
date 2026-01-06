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

## License

MIT License
