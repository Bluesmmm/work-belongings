#!/bin/bash
# vLLM Benchmark Runner
#
# One-click script to run load tests against vLLM server.
# This script handles server health checks, test execution, and report generation.
#
# Usage:
#   ./scripts/run_benchmark.sh
#   ./scripts/run_benchmark.sh --repeat 3
#   ./scripts/run_benchmark.sh --config custom.yaml --concurrency 20

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
REPEAT=1
CONFIG="benchmark/config/default.yaml"
CONCURRENCY=""
NUM_REQUESTS=""
OUTPUT_DIR=""
NO_MONITORING=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --repeat)
            REPEAT="$2"
            shift 2
            ;;
        --config)
            CONFIG="$2"
            shift 2
            ;;
        --concurrency)
            CONCURRENCY="$2"
            shift 2
            ;;
        --num-requests)
            NUM_REQUESTS="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --no-monitoring)
            NO_MONITORING=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --repeat N              Run benchmark N times (default: 1)"
            echo "  --config FILE           Use custom config file"
            echo "  --concurrency N         Override concurrency level"
            echo "  --num-requests N        Override number of requests"
            echo "  --output DIR            Custom output directory"
            echo "  --no-monitoring         Skip monitoring stack check"
            echo ""
            echo "Example:"
            echo "  $0 --repeat 3 --concurrency 20"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if config file exists
if [ ! -f "$CONFIG" ]; then
    print_error "Config file not found: $CONFIG"
    exit 1
fi

# Extract server URL from config
SERVER_URL=$(grep -A1 "base_url:" "$CONFIG" | tail -1 | sed 's/.*: "\(.*\)"/\1/' | sed 's/^[[:space:]]*//')

print_info "=== vLLM Benchmark Runner ==="
print_info "Config: $CONFIG"
print_info "Server URL: $SERVER_URL"
print_info "Repeat: $REPEAT"
echo ""

# Function to check server health
check_server_health() {
    print_info "Checking server health..."

    # Use httpx or curl for health check
    if command -v curl &> /dev/null; then
        if curl -f -s "$SERVER_URL/models" > /dev/null 2>&1; then
            print_success "Server is healthy"
            return 0
        fi
    elif command -v python3 &> /dev/null; then
        if python3 -c "import httpx; httpx.get('$SERVER_URL/models')" 2>/dev/null; then
            print_success "Server is healthy"
            return 0
        fi
    else
        print_warning "Cannot verify server health (curl/python3 not found)"
        return 0
    fi

    print_error "Server health check failed!"
    print_warning "Make sure the vLLM server is running:"
    echo "  python serving/launch.py"
    echo "  Or use: ./scripts/dev.sh"
    return 1
}

# Check monitoring stack (optional)
if [ "$NO_MONITORING" = false ]; then
    print_info "Checking monitoring stack..."

    if command -v curl &> /dev/null; then
        if curl -f -s "http://localhost:9090/-/healthy" > /dev/null 2>&1; then
            print_success "Prometheus is running"
        else
            print_warning "Prometheus is not running. Start with:"
            echo "  ./scripts/start_monitoring.sh"
        fi
    fi
fi

# Health check
if ! check_server_health; then
    print_error "Aborting benchmark"
    exit 1
fi

echo ""

# Build command
CMD="python benchmark/load_test.py --config $CONFIG"

if [ -n "$CONCURRENCY" ]; then
    CMD="$CMD --concurrency $CONCURRENCY"
fi

if [ -n "$NUM_REQUESTS" ]; then
    CMD="$CMD --num-requests $NUM_REQUESTS"
fi

if [ -n "$OUTPUT_DIR" ]; then
    CMD="$CMD --output $OUTPUT_DIR"
fi

# Run benchmark(s)
for i in $(seq 1 $REPEAT); do
    if [ $REPEAT -gt 1 ]; then
        print_info "=== Run $i of $REPEAT ==="
    fi

    if $CMD; then
        print_success "Benchmark run $i completed"
    else
        print_error "Benchmark run $i failed"
        exit 1
    fi

    if [ $i -lt $REPEAT ]; then
        print_info "Waiting 5 seconds before next run..."
        sleep 5
    fi
done

print_success "=== All benchmarks completed successfully ==="

# Show latest report
REPORT_DIR=$(grep -A2 "output_dir:" "$CONFIG" | tail -1 | sed 's/.*: "\(.*\)"/\1/' | sed 's/^[[:space:]]*//')
if [ -z "$REPORT_DIR" ]; then
    REPORT_DIR="benchmark/reports"
fi

if [ -n "$OUTPUT_DIR" ]; then
    REPORT_DIR="$OUTPUT_DIR"
fi

LATEST_JSON=$(ls -t "$REPORT_DIR"/benchmark_*.json 2>/dev/null | head -1)

if [ -n "$LATEST_JSON" ]; then
    print_info "Latest report: $LATEST_JSON"
    print_info "View results:"
    echo "  cat $LATEST_JSON"
fi

exit 0
