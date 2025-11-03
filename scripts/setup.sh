#!/bin/bash

################################################################################
# HerdLinx Raspberry Pi Backend - Setup Script
#
# One-time setup script to prepare the Raspberry Pi for running HerdLinx
#
# Usage:
#   ./scripts/setup.sh
#
# This script:
#   - Installs system dependencies
#   - Creates virtual environment
#   - Installs Python dependencies
#   - Generates SSL certificates
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

print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  HerdLinx Raspberry Pi Backend - Setup${NC}"
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
        print_error "This setup script is designed for Raspberry Pi (Linux)"
        echo "Detected OS: $OSTYPE"
        exit 1
    fi

    print_success "Linux OS detected"
}

check_sudo() {
    print_step "Checking permissions..."

    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root (not recommended)"
    else
        print_warning "This script will need sudo for some operations"
    fi
}

update_system() {
    print_step "Updating system packages..."

    sudo apt-get update > /dev/null 2>&1
    sudo apt-get upgrade -y > /dev/null 2>&1

    print_success "System packages updated"
}

install_dependencies() {
    print_step "Installing system dependencies..."

    echo "Installing: python3, python3-pip, python3-venv, git, openssl..."

    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        git \
        openssl \
        build-essential \
        libssl-dev \
        > /dev/null 2>&1

    print_success "System dependencies installed"
}

create_project_structure() {
    print_step "Creating project structure..."

    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/office_app/certs"

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

generate_certs() {
    print_step "Generating SSL certificates..."

    cd "$PROJECT_ROOT"
    source venv/bin/activate

    python3 office_app/generate_certs.py

    print_success "SSL certificates generated"
}

create_env_file() {
    print_step "Creating environment configuration..."

    if [ -f "$PROJECT_ROOT/.env" ]; then
        print_warning ".env file already exists, skipping"
        return
    fi

    # Generate keys
    API_KEY="hxb_$(openssl rand -hex 20)"
    JWT_SECRET=$(openssl rand -hex 32)

    cat > "$PROJECT_ROOT/.env" << EOF
# HerdLinx Raspberry Pi Backend Configuration
IS_PI_BACKEND=True
FLASK_ENV=development
SQLALCHEMY_DATABASE_URI=sqlite:///office_app/office_app.db
PI_API_KEY=$API_KEY
JWT_SECRET=$JWT_SECRET
PORT=5001
HOST=0.0.0.0
LOG_LEVEL=INFO
DEBUG=False
EOF

    chmod 600 "$PROJECT_ROOT/.env"

    print_success ".env file created"
    echo ""
    echo -e "${YELLOW}Your API Key:${NC}"
    echo "  $API_KEY"
    echo ""
    echo "Keep this key safe! You'll need it for Server UI configuration."
    echo ""
}

make_scripts_executable() {
    print_step "Making scripts executable..."

    chmod +x "$SCRIPT_DIR/start.sh"
    chmod +x "$SCRIPT_DIR/setup.sh"

    print_success "Scripts are executable"
}

summary() {
    print_step "Setup complete!"
    echo ""
    echo -e "${GREEN}Next Steps:${NC}"
    echo ""
    echo "1. Start the application:"
    echo "   cd $PROJECT_ROOT"
    echo "   ./scripts/start.sh"
    echo ""
    echo "2. For development mode:"
    echo "   ./scripts/start.sh --dev"
    echo ""
    echo "3. For production mode:"
    echo "   ./scripts/start.sh --prod"
    echo ""
    echo -e "${GREEN}Configuration:${NC}"
    echo "  API Key file:  $PROJECT_ROOT/.env"
    echo "  Certificates:  $PROJECT_ROOT/office_app/certs/"
    echo "  Database:      $PROJECT_ROOT/office_app/office_app.db"
    echo "  Logs:          $PROJECT_ROOT/logs/"
    echo ""
    echo -e "${GREEN}Access:${NC}"
    echo "  API URL: https://$(hostname -I | awk '{print $1}'):5001"
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
    generate_certs
    create_env_file
    make_scripts_executable
    summary
}

main
