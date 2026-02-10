#!/bin/bash
# Start vLLM Monitoring Stack
# This script launches Prometheus and Grafana for vLLM observability
#
# Usage:
#   ./scripts/start_monitoring.sh          # Start monitoring
#   ./scripts/start_monitoring.sh stop     # Stop monitoring
#   ./scripts/start_monitoring.sh restart  # Restart monitoring
#   ./scripts/start_monitoring.sh status   # Check status

set -eu  # Exit on error and unset variables

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/observability/docker-compose.yml"

# Function to print colored output
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

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
}

# Function to check if Docker Compose is available
check_docker_compose() {
    if docker compose version &> /dev/null; then
        DOCKER_COMPOSE="docker compose"
    elif command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        print_error "Docker Compose is not installed. Please install Docker Compose."
        exit 1
    fi
}

# Function to check if vLLM server is running
check_vllm_server() {
    print_info "Checking if vLLM server is running..."

    if curl -s http://localhost:8000/health &> /dev/null; then
        print_success "vLLM server is running at http://localhost:8000"

        # Check if metrics are enabled
        if curl -s http://localhost:8000/metrics | grep -q "vllm:"; then
            print_success "Metrics endpoint is accessible"
            return 0
        else
            print_warning "Metrics endpoint may not be enabled. Check that enable_metrics: true in config.yaml"
            return 1
        fi
    else
        print_warning "vLLM server does not appear to be running at http://localhost:8000"
        print_warning "Start the vLLM server first with: python serving/launch.py"
        return 1
    fi
}

# Function to start monitoring
start_monitoring() {
    print_info "Starting vLLM monitoring stack..."

    check_docker
    check_docker_compose

    cd "$PROJECT_ROOT"

    # Start containers
    if $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d 2>&1; then
        print_success "Monitoring stack started successfully!"
        echo ""
        echo "Services:"
        echo "  - Prometheus: http://localhost:9090"
        echo "  - Grafana:    http://localhost:3000 (admin/admin)"
        echo ""
        echo "Commands:"
        echo "  - View logs:  $DOCKER_COMPOSE -f $COMPOSE_FILE logs -f"
        echo "  - Stop:       ./scripts/start_monitoring.sh stop"
        echo ""
    else
        print_error "Failed to start monitoring stack"
        exit 1
    fi
}

# Function to stop monitoring
stop_monitoring() {
    print_info "Stopping vLLM monitoring stack..."

    cd "$PROJECT_ROOT"

    if $DOCKER_COMPOSE -f "$COMPOSE_FILE" down 2>&1; then
        print_success "Monitoring stack stopped"
    else
        print_error "Failed to stop monitoring stack"
        exit 1
    fi
}

# Function to restart monitoring
restart_monitoring() {
    print_info "Restarting vLLM monitoring stack..."
    stop_monitoring
    sleep 2
    start_monitoring
}

# Function to show status
show_status() {
    print_info "Monitoring stack status:"
    echo ""

    cd "$PROJECT_ROOT"

    if $DOCKER_COMPOSE -f "$COMPOSE_FILE" ps 2>&1; then
        echo ""
        print_info "Checking service health..."
        echo ""

        # Check Prometheus
        if curl -s http://localhost:9090/-/healthy &> /dev/null; then
            print_success "Prometheus is healthy"
        else
            print_warning "Prometheus may not be ready"
        fi

        # Check Grafana
        if curl -s http://localhost:3000/api/health &> /dev/null; then
            print_success "Grafana is healthy"
        else
            print_warning "Grafana may not be ready"
        fi

        # Check vLLM metrics
        check_vllm_server || true
    else
        print_warning "Monitoring stack is not running"
    fi
}

# Main script logic
case "${1:-start}" in
    start)
        start_monitoring
        ;;
    stop)
        stop_monitoring
        ;;
    restart)
        restart_monitoring
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
