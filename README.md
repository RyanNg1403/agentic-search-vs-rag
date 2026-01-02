# RAG vs Agentic Search: Experimental Validation

This repository contains a reproducible experiment comparing traditional **Vector-based RAG** with **Agentic Search** (context trees) for code retrieval tasks.

## The Problem with RAG for Code

Most coding agents use vector embeddings and similarity search to retrieve context. This works well for natural language but fails for code because:

1. **Code is a graph, not "bag of words"** - Dependencies matter more than keyword similarity
2. **Context dilution** - Retrieving `AuthController.ts`, `AuthTests.ts`, `Old_Auth_Backup.ts`, and `Auth_v2_migration.ts` just because they all mention "authentication" floods the context with noise
3. **High recall ≠ High precision** - Getting 50 "maybe useful" files doesn't help the agent; it confuses it

## Our Approach: Context Trees + Agentic Search

Instead of flat vector similarity, we structure knowledge as **context trees**:

1. **Intent-based traversal** - Agent understands what you need (e.g., "add column to User table")
2. **Dependency-aware** - Follows import graphs, not keyword matches
3. **Pruning irrelevant branches** - `frontend/` is pruned if task is database-only

**Result:** 3 highly relevant files instead of 50 "similar" ones.

## Experimental Results

We tested both approaches on the [gemini-cli](https://github.com/google-gemini/gemini-cli) codebase (~1300 files) with 30 carefully designed questions across 4 categories: direct queries, dependency queries, feature queries, and refactoring scenarios.

### Token Efficiency

**Metric:** Total tokens in retrieved context that would be fed to the LLM.
- **RAG:** Sum of tokens in all retrieved file contents
- **Agentic:** Tokens in the entire `brv query` response (answer + file paths)

![Token Usage Comparison](visualizations/token_usage_comparison.png)

**Agentic Search uses 99% fewer tokens.** RAG retrieves entire file contents for 5 files per query (~8,775 tokens). Agentic Search returns only the answer + file paths (~72 tokens), dramatically reducing context size.

### Precision

**Metric:** What fraction of retrieved files are actually relevant?

```
Precision = |Retrieved ∩ Ground Truth| / |Retrieved|
```

![Precision Comparison](visualizations/precision_comparison.png)

**Agentic Search achieves 2.2× higher precision.** RAG's similarity-based retrieval includes many irrelevant files. Agentic Search uses intent understanding to filter out noise.

### Recall

**Metric:** What fraction of relevant files were successfully retrieved?

```
Recall = |Retrieved ∩ Ground Truth| / |Ground Truth|
```

![Recall Comparison](visualizations/recall_comparison.png)

**RAG has slightly higher recall** because it always returns 5 files. However, irrelevant retrieved files dilute agent context and increase hallucination risk.

### IoU (Intersection over Union)

**Metric:** Balances precision and recall by measuring overlap relative to total distinct files.

```
IoU = |Retrieved ∩ Ground Truth| / |Retrieved ∪ Ground Truth|
```

![IoU Score Comparison](visualizations/iou_comparison.png)

**Agentic Search achieves 2× better IoU.** This metric balances precision and recall - Agentic Search retrieves exactly the right files, not just "more files."

## Key Findings

| Metric | RAG | Agentic Search | Improvement |
|--------|-----|----------------|-------------|
| **Token Usage** | 8,775 | 72 | **-99.2%** |
| **Precision** | 0.053 | 0.117 | **+118.7%** |
| **Recall** | 0.108 | 0.097 | -9.3% |
| **IoU** | 0.036 | 0.073 | **+106.4%** |

**Takeaway:** Agentic Search uses 99% fewer tokens while achieving 2× better IoU and precision. RAG's slightly higher recall comes from always returning 5 files, but irrelevant retrievals dilute context and increase hallucination risk.

## Reproduce the Experiment

See [REPRODUCTION.md](REPRODUCTION.md) for detailed setup and reproduction instructions.

## Repository Structure

```

├── README.md                      # This file
├── REPRODUCTION.md                # Detailed reproduction guide
├── questions.json                 # 30 evaluation questions with ground truth
├── context-tree/                  # Pre-curated ByteRover knowledge base
├── rag_pipeline.py                # RAG implementation (OpenAI embeddings + Qdrant)
├── agentic_pipeline.py            # Agentic search implementation (brv query)
├── compare_results.py             # Comparison and metrics calculation
├── visualize_results.py           # Generate comparison charts
├── results/                       # Experiment outputs (gitignored)
│   ├── rag_results.json
│   ├── agentic_results.json
│   ├── comparison_report.md
│   └── *.png
└── gemini-cli/                    # Target codebase (clone separately)
```


## License

MIT License
