#!/bin/bash

################################################################################
# HerdLinx Server UI - Startup Script
#
# Usage:
#   ./scripts/start-server.sh                 # Start with defaults
#   ./scripts/start-server.sh --dev           # Start in development mode
#   ./scripts/start-server.sh --prod          # Start in production mode
#   ./scripts/start-server.sh --help          # Show help
#
# This script handles:
#   - Environment setup
#   - Virtual environment activation
#   - Dependency installation
#   - Application startup
#
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/venv"
LOG_DIR="$PROJECT_ROOT/logs"

# Mode (dev or prod)
MODE="${1:-default}"

# Functions
print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  HerdLinx Server UI Startup${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
}

print_step() {
    echo -e "\n${GREEN}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_help() {
    cat << EOF

${BLUE}HerdLinx Server UI Startup Script${NC}

${GREEN}Usage:${NC}
  $0 [options]

${GREEN}Options:${NC}
  --dev               Start in development mode (debug logging)
  --prod              Start in production mode (minimal logging)
  --help              Show this help message

${GREEN}Environment Variables:${NC}
  IS_SERVER_UI        Set to True (auto-set by script)
  REMOTE_PI_HOST      Pi backend IP address (from .env)
  REMOTE_PI_PORT      Pi backend port (default: 5001)
  PI_API_KEY          API key for Pi authentication (from .env)
  DB_SYNC_INTERVAL    Sync interval in seconds (default: 10)

${GREEN}First Run:${NC}
  1. Script checks for virtual environment
  2. Creates venv if needed
  3. Installs dependencies
  4. Creates .env file with configuration
  5. Starts the application

${GREEN}Subsequent Runs:${NC}
  Just run: $0

${GREEN}Examples:${NC}
  # Start with defaults
  ./scripts/start-server.sh

  # Start in development mode
  ./scripts/start-server.sh --dev

  # Start in production mode
  ./scripts/start-server.sh --prod

EOF
}

check_dependencies() {
    print_step "Checking system dependencies..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        echo "Install with: apt-get install python3 (Linux) or python.org (Windows)"
        exit 1
    fi
    print_success "Python 3 found: $(python3 --version)"

    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed"
        echo "Install with: apt-get install python3-pip (Linux) or python.org (Windows)"
        exit 1
    fi
    print_success "pip3 found"
}

setup_virtual_environment() {
    print_step "Setting up virtual environment..."

    if [ ! -d "$VENV_DIR" ]; then
        print_warning "Virtual environment not found, creating..."
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi

    # Activate virtual environment
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    elif [ -f "$VENV_DIR/Scripts/activate" ]; then
        source "$VENV_DIR/Scripts/activate"
    else
        print_error "Cannot find activate script"
        exit 1
    fi
    print_success "Virtual environment activated"
}

install_dependencies() {
    print_step "Installing dependencies..."

    if [ ! -f "$PROJECT_ROOT/requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi

    pip install --upgrade pip setuptools wheel > /dev/null 2>&1
    pip install -r "$PROJECT_ROOT/requirements.txt"

    print_success "Dependencies installed"
}

setup_environment() {
    print_step "Setting up environment configuration..."

    if [ -f "$PROJECT_ROOT/.env" ]; then
        print_success ".env file already exists"
        return
    fi

    print_warning ".env file not found, creating..."

    cat > "$PROJECT_ROOT/.env" << EOF
# HerdLinx Server UI Configuration
IS_SERVER_UI=True
FLASK_ENV=development

# Database
SQLALCHEMY_DATABASE_URI=sqlite:///office_app/office_app.db

# Pi Backend Connection
REMOTE_PI_HOST=192.168.1.100
REMOTE_PI_PORT=5001
PI_API_KEY=hxb_your_api_key_here
USE_SSL_FOR_PI=True
USE_SELF_SIGNED_CERT=True

# Sync Configuration
DB_SYNC_INTERVAL=10

# Server
PORT=5000
HOST=0.0.0.0

# Logging
LOG_LEVEL=INFO

# Debug
DEBUG=False
EOF

    print_success ".env file created"
    echo ""
    echo -e "${YELLOW}Important:${NC} Edit .env and set:"
    echo "  - REMOTE_PI_HOST: Your Raspberry Pi's IP address"
    echo "  - PI_API_KEY: API key from Pi backend (from setup.sh output)"
    echo ""
}

create_logs_directory() {
    print_step "Setting up logs directory..."

    mkdir -p "$LOG_DIR"
    print_success "Logs directory ready: $LOG_DIR"
}

start_application() {
    print_step "Starting HerdLinx Server UI..."
    echo ""

    # Activate virtual environment
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    elif [ -f "$VENV_DIR/Scripts/activate" ]; then
        source "$VENV_DIR/Scripts/activate"
    fi

    # Set environment variables from .env if it exists
    if [ -f "$PROJECT_ROOT/.env" ]; then
        export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
    fi

    # Set mode-specific variables
    case "$MODE" in
        --dev)
            export FLASK_ENV=development
            export DEBUG=True
            export LOG_LEVEL=DEBUG
            print_step "Starting in DEVELOPMENT mode (debug enabled)"
            ;;
        --prod)
            export FLASK_ENV=production
            export DEBUG=False
            export LOG_LEVEL=WARNING
            print_step "Starting in PRODUCTION mode"
            ;;
        --help)
            print_help
            exit 0
            ;;
        *)
            # Default mode
            if [ -z "$FLASK_ENV" ]; then
                export FLASK_ENV=development
                export LOG_LEVEL=INFO
            fi
            ;;
    esac

    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}HerdLinx Server UI is starting...${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "📍 Server:       http://localhost:5000"
    echo "👤 Default User: admin"
    echo "🔑 Default Pass: admin"
    echo "📦 Database:     $PROJECT_ROOT/office_app/office_app.db"
    echo "📋 Logs:         $LOG_DIR"
    echo "🔧 Mode:         $FLASK_ENV"
    echo ""
    echo "Press Ctrl+C to stop"
    echo ""

    # Start the application
    cd "$PROJECT_ROOT"
    python -m office_app.run
}

main() {
    print_header

    # Check for help flag early
    if [ "$MODE" == "--help" ]; then
        print_help
        exit 0
    fi

    check_dependencies
    setup_virtual_environment
    install_dependencies
    setup_environment
    create_logs_directory
    start_application
}

# Run main function
main
