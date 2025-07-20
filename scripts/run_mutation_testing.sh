#!/bin/bash

# Simple Cosmic Ray Mutation Testing Script
# Runs mutation testing on the 'ask' module with sensible defaults

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Simple cleanup
cleanup() {
    if [[ $? -ne 0 ]]; then
        log_error "Mutation testing failed"
    fi
    # Clean up temp files
    rm -f mutation_session.sqlite
}
trap cleanup EXIT

main() {
    log_info "Running mutation testing on 'ask' module..."

    # Check dependencies
    if ! command -v uv &> /dev/null; then
        log_error "uv is required but not installed"
        exit 1
    fi

    # Install cosmic-ray if needed
    if ! uv run cosmic-ray --help &> /dev/null; then
        log_info "Installing cosmic-ray..."
        uv add cosmic-ray
    fi

    # Run baseline test
    log_info "Running baseline tests..."
    if ! uv run cosmic-ray --verbosity=INFO baseline mutation_testing.toml; then
        log_error "Baseline tests failed! Fix your tests first."
        exit 1
    fi

    # Initialize session
    log_info "Initializing mutation session..."
    uv run cosmic-ray --verbosity=INFO init mutation_testing.toml mutation_session.sqlite
    uv run cr-filter-pragma mutation_session.sqlite

    # Show what we're testing
    total_mutations=$(uv run cr-report mutation_session.sqlite 2>/dev/null | grep "total jobs:" | cut -d: -f2 | tr -d ' ')
    log_info "Found $total_mutations mutations to test"

    # Run mutation testing
    log_info "Running mutation testing (this may take a while)..."
    uv run cosmic-ray --verbosity=INFO exec mutation_testing.toml mutation_session.sqlite

    # Generate reports
    log_info "Generating reports..."
    mkdir -p mutation_reports
    uv run cr-report mutation_session.sqlite > mutation_reports/report.txt
    uv run cr-html mutation_session.sqlite > mutation_reports/report.html

    # Show summary
    log_success "Mutation testing complete!"
    echo ""
    echo "Reports generated:"
    echo "  - mutation_reports/report.txt (text summary)"
    echo "  - mutation_reports/report.html (interactive report)"
    echo ""

    # Show final stats
    uv run cr-report mutation_session.sqlite | tail -3
}

main "$@"
