#!/bin/bash

################################################################################
# HerdLinx Server UI - Setup Script
#
# One-time setup script to prepare the Server for running HerdLinx Server UI
#
# Usage:
#   ./scripts/setup-server.sh
#   ./scripts/setup-server.sh --skip-update    # Skip system package update
#   ./scripts/setup-server.sh --help           # Show help
#
# This script:
#   - Installs system dependencies
#   - Creates virtual environment
#   - Installs Python dependencies
#   - Creates configuration files
#
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse command line arguments
SKIP_UPDATE=false
for arg in "$@"; do
    case $arg in
        --skip-update)
            SKIP_UPDATE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --skip-update    Skip system package update (faster setup)"
            echo "  --help           Show this help message"
            exit 0
            ;;
    esac
done

print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  HerdLinx Server UI - Setup${NC}"
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

check_os() {
    print_step "Checking OS..."

    if [[ ! "$OSTYPE" =~ linux-gnu ]]; then
        print_error "This setup script is designed for Linux servers"
        echo "Detected OS: $OSTYPE"
        echo "For Windows, use Windows subsystem or run Python directly"
        exit 1
    fi

    print_success "Linux OS detected"
}

check_sudo() {
    print_step "Checking permissions..."

    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root (not recommended)"
    else
        print_warning "This script will need sudo for system operations"
    fi
}

update_system() {
    if [ "$SKIP_UPDATE" = true ]; then
        print_step "Skipping system package update (--skip-update flag set)"
        return
    fi

    print_step "Updating system packages..."

    sudo apt-get update > /dev/null 2>&1
    sudo apt-get upgrade -y > /dev/null 2>&1

    print_success "System packages updated"
}

install_dependencies() {
    print_step "Installing system dependencies..."

    echo "Installing: python3, python3-pip, python3-venv, git..."

    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        git \
        > /dev/null 2>&1

    print_success "System dependencies installed"
}

create_project_structure() {
    print_step "Creating project structure..."

    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/office_app/templates"
    mkdir -p "$PROJECT_ROOT/office_app/static"

    print_success "Project structure created"
}

setup_venv() {
    print_step "Creating virtual environment..."

    cd "$PROJECT_ROOT"

    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
    else
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
}

install_python_deps() {
    print_step "Installing Python dependencies..."

    cd "$PROJECT_ROOT"
    source venv/bin/activate

    pip install --upgrade pip setuptools wheel > /dev/null 2>&1
    pip install -r requirements.txt

    print_success "Python dependencies installed"
}

create_env_file() {
    print_step "Creating environment configuration..."

    if [ -f "$PROJECT_ROOT/.env" ]; then
        print_warning ".env file already exists, skipping"
        return
    fi

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

    chmod 600 "$PROJECT_ROOT/.env"

    print_success ".env file created"
    echo ""
    echo -e "${YELLOW}Important:${NC} Edit .env and configure:"
    echo "  - REMOTE_PI_HOST: Your Raspberry Pi's IP address"
    echo "  - PI_API_KEY: API key from Pi backend (from ./scripts/setup.sh output)"
    echo ""
}

make_scripts_executable() {
    print_step "Making scripts executable..."

    chmod +x "$SCRIPT_DIR/start-server.sh"
    chmod +x "$SCRIPT_DIR/setup-server.sh"

    print_success "Scripts are executable"
}

summary() {
    print_step "Setup complete!"
    echo ""
    echo -e "${GREEN}Next Steps:${NC}"
    echo ""
    echo "1. Edit the .env file with your Pi backend details:"
    echo "   nano $PROJECT_ROOT/.env"
    echo ""
    echo "2. Start the Server UI:"
    echo "   cd $PROJECT_ROOT"
    echo "   ./scripts/start-server.sh"
    echo ""
    echo "3. For development mode:"
    echo "   ./scripts/start-server.sh --dev"
    echo ""
    echo "4. For production mode:"
    echo "   ./scripts/start-server.sh --prod"
    echo ""
    echo -e "${GREEN}Configuration:${NC}"
    echo "  Config file:   $PROJECT_ROOT/.env"
    echo "  Database:      $PROJECT_ROOT/office_app/office_app.db"
    echo "  Logs:          $PROJECT_ROOT/logs/"
    echo ""
    echo -e "${GREEN}Access:${NC}"
    echo "  Web Server:    http://localhost:5000"
    echo "  Username:      admin"
    echo "  Password:      admin"
    echo ""
}

main() {
    print_header

    check_os
    check_sudo
    update_system
    install_dependencies
    create_project_structure
    setup_venv
    install_python_deps
    create_env_file
    make_scripts_executable
    summary
}

main
