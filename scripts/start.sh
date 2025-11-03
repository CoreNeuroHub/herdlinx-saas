#!/bin/bash

################################################################################
# HerdLinx Raspberry Pi Backend - Startup Script
#
# Usage:
#   ./scripts/start.sh                 # Start with defaults
#   ./scripts/start.sh --dev           # Start in development mode
#   ./scripts/start.sh --prod          # Start in production mode
#   ./scripts/start.sh --help          # Show help
#
# This script handles:
#   - Environment setup
#   - Certificate generation
#   - Dependency checking
#   - Database initialization
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
CERTS_DIR="$PROJECT_ROOT/office_app/certs"

# Mode (dev or prod)
MODE="${1:-default}"

# Functions
print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  HerdLinx Raspberry Pi Backend Startup${NC}"
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

${BLUE}HerdLinx Raspberry Pi Backend Startup Script${NC}

${GREEN}Usage:${NC}
  $0 [options]

${GREEN}Options:${NC}
  --dev               Start in development mode (debug logging, hot reload)
  --prod              Start in production mode (minimal logging)
  --help              Show this help message

${GREEN}Environment Variables:${NC}
  IS_PI_BACKEND       Set to True (auto-set by script)
  PI_API_KEY          API key for authentication (generated if not set)
  FLASK_ENV           Flask environment (development/production)
  LOG_LEVEL           Logging level (DEBUG/INFO/WARNING)
  PORT                Port to run on (default: 5001)

${GREEN}First Run:${NC}
  1. Script checks for virtual environment
  2. Creates venv if needed
  3. Installs dependencies
  4. Generates SSL certificates
  5. Creates .env file with configuration
  6. Starts the application

${GREEN}Subsequent Runs:${NC}
  Just run: $0

${GREEN}Examples:${NC}
  # Start with defaults
  ./scripts/start.sh

  # Start in development mode
  ./scripts/start.sh --dev

  # Start in production mode
  ./scripts/start.sh --prod

EOF
}

check_dependencies() {
    print_step "Checking system dependencies..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        echo "Install with: sudo apt-get install python3"
        exit 1
    fi
    print_success "Python 3 found: $(python3 --version)"

    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed"
        echo "Install with: sudo apt-get install python3-pip"
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
    source "$VENV_DIR/bin/activate"
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

generate_certificates() {
    print_step "Checking SSL certificates..."

    if [ -f "$CERTS_DIR/server.crt" ] && [ -f "$CERTS_DIR/server.key" ]; then
        print_success "SSL certificates already exist"
        return
    fi

    print_warning "SSL certificates not found, generating..."

    mkdir -p "$CERTS_DIR"

    # Try using openssl first
    if command -v openssl &> /dev/null; then
        openssl req -x509 -newkey rsa:2048 \
            -keyout "$CERTS_DIR/server.key" \
            -out "$CERTS_DIR/server.crt" \
            -days 365 -nodes \
            -subj "/C=US/ST=State/L=City/O=HerdLinx/CN=herdlinx-pi.local" \
            2>/dev/null
        print_success "SSL certificates generated with OpenSSL"
        return
    fi

    # Fallback to Python
    print_warning "OpenSSL not found, using Python cryptography..."
    python3 "$PROJECT_ROOT/office_app/generate_certs.py"

    if [ -f "$CERTS_DIR/server.crt" ] && [ -f "$CERTS_DIR/server.key" ]; then
        print_success "SSL certificates generated"
    else
        print_error "Failed to generate SSL certificates"
        exit 1
    fi
}

setup_environment() {
    print_step "Setting up environment configuration..."

    if [ -f "$PROJECT_ROOT/.env" ]; then
        print_success ".env file already exists"
        return
    fi

    print_warning ".env file not found, creating..."

    # Generate a random API key if not provided
    if [ -z "$PI_API_KEY" ]; then
        PI_API_KEY="hxb_$(openssl rand -hex 20 2>/dev/null || python3 -c 'import secrets; print(secrets.token_hex(20))')"
    fi

    cat > "$PROJECT_ROOT/.env" << EOF
# HerdLinx Raspberry Pi Backend Configuration
# Generated at $(date)

# Application Mode
IS_PI_BACKEND=True
FLASK_ENV=development

# Database
SQLALCHEMY_DATABASE_URI=sqlite:///office_app/office_app.db

# Security
PI_API_KEY=$PI_API_KEY
JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || python3 -c 'import secrets; print(secrets.token_hex(32))')

# Server
PORT=5001
HOST=0.0.0.0

# Logging
LOG_LEVEL=INFO

# LoRa Processing
LORA_PROCESSING_INTERVAL=5

# Debug
DEBUG=False
EOF

    print_success ".env file created"
    echo ""
    echo -e "${YELLOW}Important:${NC} Your API key is:"
    echo -e "  ${BLUE}$PI_API_KEY${NC}"
    echo ""
    echo "Save this key! You'll need it to configure the Server UI."
    echo ""
}

create_logs_directory() {
    print_step "Setting up logs directory..."

    mkdir -p "$LOG_DIR"
    print_success "Logs directory ready: $LOG_DIR"
}

check_port() {
    print_step "Checking if port 5001 is available..."

    if command -v lsof &> /dev/null; then
        if lsof -i :5001 > /dev/null 2>&1; then
            print_warning "Port 5001 is already in use"
            echo "Current process using port 5001:"
            lsof -i :5001
            echo ""
            read -p "Continue anyway? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_error "Startup cancelled"
                exit 1
            fi
        else
            print_success "Port 5001 is available"
        fi
    else
        print_warning "lsof not found, skipping port check"
    fi
}

start_application() {
    print_step "Starting HerdLinx Raspberry Pi Backend..."
    echo ""

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

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
    echo -e "${GREEN}HerdLinx Raspberry Pi Backend is starting...${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "📍 API Server:      https://$(hostname -I | awk '{print $1}'):5001"
    echo "🔐 API Key:         ${PI_API_KEY:0:8}...${PI_API_KEY: -8}"
    echo "📦 Database:        $PROJECT_ROOT/office_app/office_app.db"
    echo "📋 Logs:            $LOG_DIR"
    echo "🔧 Mode:            $FLASK_ENV"
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
    generate_certificates
    setup_environment
    create_logs_directory
    check_port
    start_application
}

# Run main function
main
