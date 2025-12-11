#!/bin/bash

# HerdLinx SAAS Setup Script
# This script sets up the SAAS environment and dependencies automatically
# Usage: bash setup.sh

set -e  # Exit on error

echo "=================================================="
echo "HerdLinx SAAS Setup"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on correct directory
if [ ! -f "run.py" ]; then
    echo -e "${RED}Error: run.py not found. Please run this script from the saas directory.${NC}"
    echo "Usage: cd saas && bash setup.sh"
    exit 1
fi

echo -e "${YELLOW}Step 1: Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi
python_version=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✓ Python $python_version found${NC}"

echo ""
echo -e "${YELLOW}Step 2: Creating Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

echo ""
echo -e "${YELLOW}Step 3: Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel -q
echo -e "${GREEN}✓ pip upgraded${NC}"

echo ""
echo -e "${YELLOW}Step 4: Installing Python dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}Error: requirements.txt not found${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 5: Checking .env file...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}Creating .env from .env.example${NC}"
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created${NC}"
        echo ""
        echo -e "${YELLOW}IMPORTANT: Edit .env file with your MongoDB credentials:${NC}"
        echo "  nano .env"
        echo ""
        echo "Update these values:"
        echo "  MONGODB_URI=mongodb+srv://herdlinx_app:Tr0p1c@lRa1nB0w#2024!@herdlinx-cluster-abc.mongodb.net/..."
        echo "  SECRET_KEY=[generate with: python -c \"import secrets; print(secrets.token_hex(32))\"]"
        echo ""
    else
        echo -e "${RED}Error: .env.example not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

echo ""
echo -e "${YELLOW}Step 6: Creating logs directory...${NC}"
mkdir -p logs
echo -e "${GREEN}✓ Logs directory created${NC}"

echo ""
echo -e "${YELLOW}Step 7: Testing MongoDB connection...${NC}"
python3 << 'PYMONGO_TEST'
import sys
try:
    from pymongo import MongoClient
    from dotenv import load_dotenv
    import os

    load_dotenv()

    uri = os.getenv('MONGODB_URI')
    if not uri or 'example.com' in uri:
        print("⚠ MongoDB URI not configured or still has placeholder values")
        print("Please update .env file with your MongoDB credentials")
        sys.exit(1)

    print("Testing MongoDB connection...")
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ismaster')
    print("✓ MongoDB connection successful!")

except Exception as e:
    print(f"⚠ MongoDB connection failed: {e}")
    print("This is expected if MongoDB is not accessible from your current location.")
    print("Update .env with correct credentials and try again.")
    sys.exit(1)
PYMONGO_TEST

echo ""
echo "=================================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration:"
echo "   nano .env"
echo ""
echo "2. Start SAAS:"
echo "   python run.py"
echo ""
echo "3. Access dashboard:"
echo "   http://localhost:5000"
echo ""
echo "For more information, see:"
echo "  - QUICK_SETUP_GUIDE.md"
echo "  - CONFIGURATION_REFERENCE.md"
echo "  - SAAS_DEPLOYMENT.md"
echo ""
