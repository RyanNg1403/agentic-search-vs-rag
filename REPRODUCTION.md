# Experiment Reproduction Guide

Complete step-by-step instructions to reproduce the RAG vs Agentic Search experiment.

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- ByteRover CLI (`brv`) - Install from https://docs.byterover.dev/quickstart
- OpenAI API key
- Git

## Setup Instructions

### 1. Clone Repository and Codebase

```bash
git clone https://github.com/RyanNg1403/agentic-search-vs-rag.git
cd agentic-search-vs-rag

# Clone the target codebase
git clone https://github.com/google-gemini/gemini-cli.git
```

### 2. Configure ByteRover

Initialize ByteRover in the gemini-cli directory:

```bash
cd gemini-cli
brv init
brv login  # Follow authentication prompts
```

Copy the pre-curated context tree (recommended for reproducibility):

```bash
cd ..  # Back to repo root
cp -r context-tree gemini-cli/.brv/context-tree
```

Verify ByteRover works:

```bash
cd gemini-cli
brv query "Where is OAuth2 implemented?"
cd ..
```

### 3. Configure OpenAI API Key

Create a `.env` file in the repository root:

```bash
echo "OPENAI_API_KEY=sk-your-api-key-here" > .env
```

### 4. Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Start Qdrant Vector Database

```bash
docker-compose up -d

# Verify it's running
curl http://localhost:6333/health
```

## Running the Experiment

### Option 1: Automated (Recommended)

Run everything with a single command:

```bash
./run_experiment.sh
```

This executes all 7 steps automatically:
1. Check prerequisites
2. Start Qdrant
3. Install dependencies
4. Run RAG pipeline (~15 min)
5. Run Agentic pipeline (~15 min)
6. Compare results
7. Generate visualizations

Results saved to `results/` directory.

### Option 2: Manual Step-by-Step

#### Step 1: Run RAG Pipeline

```bash
python rag_pipeline.py \
  --codebase ./gemini-cli \
  --questions ./questions.json \
  --output ./results/rag_results.json \
  --top-k 5
```

**Time:** ~15 minutes | **Cost:** ~$0.30 (OpenAI API)

#### Step 2: Run Agentic Search Pipeline

```bash
python agentic_pipeline.py \
  --codebase ./gemini-cli \
  --questions ./questions.json \
  --output ./results/agentic_results.json \
  --max-files 10
```

**Time:** ~15 minutes

#### Step 3: Compare Results

```bash
python compare_results.py \
  --rag-results ./results/rag_results.json \
  --agentic-results ./results/agentic_results.json \
  --markdown-report ./results/comparison_report.md \
  --json-summary ./results/comparison_summary.json
```

#### Step 4: Generate Visualizations

```bash
python visualize_results.py \
  --comparison-summary ./results/comparison_summary.json \
  --output-dir ./results
```

## View Results

```bash
# View markdown report
cat results/comparison_report.md

# View JSON summary
cat results/comparison_summary.json

# Open visualizations directory
open results/  # macOS
xdg-open results/  # Linux
```

## Cleanup

```bash
# Stop Qdrant
docker-compose down

# Remove all experiment data
docker-compose down -v
rm -rf qdrant_storage/ results/
```

## Support

- **ByteRover Documentation:** https://docs.byterover.dev
- **Issues:** Open an issue in this repository
