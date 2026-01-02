#!/bin/bash

# RAG vs Agentic Search Experiment Runner
# This script automates the entire experimental pipeline

set -e  # Exit on error

echo "========================================="
echo "RAG vs Agentic Search Experiment"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
CODEBASE_PATH="./gemini-cli"
QUESTIONS_FILE="./questions.json"
RESULTS_DIR="./results"
RAG_OUTPUT="$RESULTS_DIR/rag_results.json"
AGENTIC_OUTPUT="$RESULTS_DIR/agentic_results.json"
COMPARISON_REPORT="$RESULTS_DIR/comparison_report.md"
COMPARISON_JSON="$RESULTS_DIR/comparison_summary.json"
TOP_K=5
MAX_FILES=10

# Create results directory if it doesn't exist
mkdir -p "$RESULTS_DIR"

# Step 1: Check prerequisites
echo -e "${BLUE}[1/7] Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: docker not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

# Check brv
if ! command -v brv &> /dev/null; then
    echo -e "${RED}Error: brv (ByteRover CLI) not found${NC}"
    echo "Please install ByteRover CLI first"
    exit 1
fi
echo -e "${GREEN}✓ ByteRover CLI found${NC}"

# Check if gemini-cli exists
if [ ! -d "$CODEBASE_PATH" ]; then
    echo -e "${RED}Error: Codebase not found at $CODEBASE_PATH${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Codebase found${NC}"

# Check if brv is initialized
if [ ! -d "$CODEBASE_PATH/.brv" ]; then
    echo -e "${RED}Error: ByteRover not initialized in $CODEBASE_PATH${NC}"
    echo "Please run 'cd $CODEBASE_PATH && brv init' first"
    exit 1
fi
echo -e "${GREEN}✓ ByteRover initialized${NC}"

# Check if questions file exists
if [ ! -f "$QUESTIONS_FILE" ]; then
    echo -e "${RED}Error: Questions file not found at $QUESTIONS_FILE${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Questions file found${NC}"

echo ""

# Step 2: Start Qdrant
echo -e "${BLUE}[2/7] Starting Qdrant vector database...${NC}"

docker-compose up -d

# Wait for Qdrant to be healthy
echo "Waiting for Qdrant to be ready..."
max_retries=30
retry_count=0
while [ $retry_count -lt $max_retries ]; do
    if curl -s http://localhost:6333/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Qdrant is ready${NC}"
        break
    fi
    retry_count=$((retry_count + 1))
    if [ $retry_count -eq $max_retries ]; then
        echo -e "${RED}Error: Qdrant failed to start${NC}"
        docker-compose logs qdrant
        exit 1
    fi
    sleep 2
done

echo ""

# Step 3: Install Python dependencies
echo -e "${BLUE}[3/7] Installing Python dependencies...${NC}"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

pip install -q -r requirements.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 4: Run RAG Pipeline
echo -e "${BLUE}[4/7] Running RAG Pipeline...${NC}"
echo "This may take 10-15 minutes (indexing ~1300 files with OpenAI embeddings)"
echo ""

python rag_pipeline.py \
    --codebase "$CODEBASE_PATH" \
    --questions "$QUESTIONS_FILE" \
    --output "$RAG_OUTPUT" \
    --top-k "$TOP_K"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ RAG pipeline completed${NC}"
else
    echo -e "${RED}✗ RAG pipeline failed${NC}"
    exit 1
fi

echo ""

# Step 5: Run Agentic Search Pipeline
echo -e "${BLUE}[5/7] Running Agentic Search Pipeline...${NC}"
echo "This may take 10-20 minutes depending on brv query response times"
echo ""

python agentic_pipeline.py \
    --codebase "$CODEBASE_PATH" \
    --questions "$QUESTIONS_FILE" \
    --output "$AGENTIC_OUTPUT" \
    --max-files "$MAX_FILES"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Agentic search pipeline completed${NC}"
else
    echo -e "${RED}✗ Agentic search pipeline failed${NC}"
    exit 1
fi

echo ""

# Step 6: Compare Results
echo -e "${BLUE}[6/7] Comparing results and generating reports...${NC}"

python compare_results.py \
    --rag-results "$RAG_OUTPUT" \
    --agentic-results "$AGENTIC_OUTPUT" \
    --markdown-report "$COMPARISON_REPORT" \
    --json-summary "$COMPARISON_JSON"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Comparison completed${NC}"
else
    echo -e "${RED}✗ Comparison failed${NC}"
    exit 1
fi

echo ""

# Step 7: Generate Visualizations
echo -e "${BLUE}[7/7] Generating visualization charts...${NC}"

python visualize_results.py \
    --comparison-summary "$COMPARISON_JSON" \
    --output-dir "$RESULTS_DIR"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Visualizations generated${NC}"
else
    echo -e "${RED}✗ Visualization generation failed${NC}"
    exit 1
fi

echo ""
echo "========================================="
echo -e "${GREEN}Experiment completed successfully!${NC}"
echo "========================================="
echo ""
echo "Output files:"
echo "  - RAG results:         $RAG_OUTPUT"
echo "  - Agentic results:     $AGENTIC_OUTPUT"
echo "  - Comparison report:   $COMPARISON_REPORT"
echo "  - Comparison summary:  $COMPARISON_JSON"
echo "  - Visualizations:      $RESULTS_DIR/*.png (5 charts)"
echo ""
echo "View the comparison report:"
echo "  cat $COMPARISON_REPORT"
echo ""
echo "View visualizations:"
echo "  open $RESULTS_DIR/  # Opens results directory"
echo ""

# Cleanup option
echo -e "${YELLOW}To stop Qdrant:${NC}"
echo "  docker-compose down"
echo ""
echo -e "${YELLOW}To clean up and re-run:${NC}"
echo "  docker-compose down -v  # Removes Qdrant data"
echo "  rm -rf $RESULTS_DIR"
echo "  ./run_experiment.sh"
echo ""
