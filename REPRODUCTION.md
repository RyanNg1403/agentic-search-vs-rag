# Experiment Reproduction Guide

This guide provides detailed instructions to reproduce the RAG vs Agentic Search experiment from scratch.

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- ByteRover CLI (`brv`) installed and authenticated
- OpenAI API key (for RAG embeddings)
- Git

## Setup Instructions

### 1. Clone Repository and Codebase

```bash
git clone <this-repo>
cd agentic-search-vs-rag

# Clone the target codebase
git clone https://github.com/google-gemini/gemini-cli.git
```

### 2. Configure ByteRover

Initialize ByteRover in the gemini-cli directory:

```bash
cd gemini-cli
brv init
```

Copy the pre-curated context tree (recommended for reproducibility):

```bash
# From the repository root
cp -r context-tree gemini-cli/.brv/context-tree
cd gemini-cli
```

Verify ByteRover works:

```bash
brv query "Where is OAuth2 implemented?"
```

**Optional: Manual Curation** (skip if using pre-curated tree)

If you want to curate from scratch:

```bash
# Login to ByteRover (required once)
brv login

# Curate knowledge (example)
brv curate "OAuth2 authentication is implemented in packages/core/src/code_assist/oauth2.ts. You must use this module for Google OAuth flows."
```

For detailed ByteRover configuration, see: https://docs.byterover.dev/quickstart

### 3. Configure OpenAI API Key

Create a `.env` file in the repository root:

```bash
cd ..  # Back to repo root
echo "OPENAI_API_KEY=sk-your-api-key-here" > .env
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Recommended:** Use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Start Qdrant Vector Database

```bash
docker-compose up -d
```

Verify Qdrant is running:
```bash
curl http://localhost:6333/health
```

## Running the Experiment

### Option 1: Automated (Recommended)

Run the entire experiment automatically:

```bash
./run_experiment.sh
```

This will:
1. Index the codebase with RAG
2. Run evaluation with both RAG and Agentic Search
3. Generate comparison reports
4. Save all results to `results/`

### Option 2: Manual Step-by-Step

#### Step 1: Run RAG Pipeline

```bash
python rag_pipeline.py \
  --codebase ./gemini-cli \
  --questions ./questions.json \
  --output ./results/rag_results.json \
  --top-k 5
```

**What happens:**
- Collects ~1300+ code files from gemini-cli
- Embeds each file using OpenAI `text-embedding-3-small`
- Indexes embeddings into Qdrant
- For each of 30 questions, retrieves top-5 most similar files
- Calculates IoU, precision, recall, and token usage
- Saves results to `results/rag_results.json`

**Time:** 10-15 minutes
**Cost:** ~$0.30 (OpenAI API)

To skip re-indexing on subsequent runs:
```bash
python rag_pipeline.py --eval-only --output ./results/rag_results.json
```

#### Step 2: Run Agentic Search Pipeline

```bash
python agentic_pipeline.py \
  --codebase ./gemini-cli \
  --questions ./questions.json \
  --output ./results/agentic_results.json \
  --max-files 10
```

**What happens:**
- For each question, runs `brv query` with strict formatting prompts
- Extracts file paths from ByteRover's response
- Counts tokens in the entire response
- Calculates IoU, precision, recall
- Saves results to `results/agentic_results.json`

**Time:** 10-20 minutes

#### Step 3: Compare Results

```bash
python compare_results.py \
  --rag-results ./results/rag_results.json \
  --agentic-results ./results/agentic_results.json \
  --markdown-report ./results/comparison_report.md \
  --json-summary ./results/comparison_summary.json
```

**Output files:**
- `results/comparison_report.md` - Human-readable markdown report
- `results/comparison_summary.json` - Structured JSON summary

#### Step 4: Generate Visualizations

```bash
python visualize_results.py \
  --comparison-summary ./results/comparison_summary.json \
  --output-dir ./results
```

**Output:** 5 PNG charts in `results/`

## Understanding the Results

### Metrics Explained

**IoU (Intersection over Union)**
- Measures retrieval accuracy
- Formula: `|retrieved ∩ ground_truth| / |retrieved ∪ ground_truth|`
- Range: 0.0 (no overlap) to 1.0 (perfect match)
- Higher is better

**Token Usage**
- RAG: Sum of tokens in all retrieved file contents
- Agentic: Tokens in the entire brv query response (answer + file paths)
- Lower is more efficient

**Precision**
- What fraction of retrieved files are relevant?
- Formula: `|retrieved ∩ ground_truth| / |retrieved|`
- Higher is better

**Recall**
- What fraction of relevant files were retrieved?
- Formula: `|retrieved ∩ ground_truth| / |ground_truth|`
- Higher is better

## Troubleshooting

### Qdrant Issues

```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Check logs
docker logs qdrant-rag-experiment

# Restart
docker-compose restart
```

### ByteRover Issues

```bash
# Verify brv is installed
brv --help

# Check if initialized
ls gemini-cli/.brv

# Re-login if needed
brv login
```

### OpenAI API Issues

The RAG pipeline makes ~1300+ API calls for indexing and 30 for evaluation.

If you hit rate limits:
- Use `--index-only` to index first, then `--eval-only` later
- Or use a paid OpenAI account with higher limits

### Python Dependencies

If matplotlib fails to install:
```bash
# macOS
brew install python-tk

# Ubuntu/Debian
sudo apt-get install python3-tk
```

## Advanced Usage

### Custom Questions

Edit `questions.json` and add your own questions:

```json
{
  "id": "q31",
  "type": "direct",
  "question": "Your question here?",
  "ground_truth": [
    "path/to/relevant/file1.ts",
    "path/to/relevant/file2.ts"
  ]
}
```

### Different Parameters

```bash
# RAG with different top-k
python rag_pipeline.py --top-k 10 --output results/rag_k10.json

# Agentic with different max files
python agentic_pipeline.py --max-files 15 --output results/agentic_15.json
```

## Cleanup

```bash
# Stop Qdrant
docker-compose down

# Remove all data
docker-compose down -v
rm -rf qdrant_storage/

# Clean results
rm -rf results/
```

## Support

For issues related to:
- **ByteRover CLI:** https://docs.byterover.dev
- **This experiment:** Open an issue in this repository
