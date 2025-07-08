#!/bin/bash
# Test script for Vercel deployment readiness

echo "🧪 Testing Vercel Deployment Readiness..."
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if any tests fail
FAILED=0

# Test 1: Check Python imports
echo -e "\n${YELLOW}1. Testing Python imports...${NC}"
cd api
python3 -c "import index; print('✅ API imports work')" 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Python import failed!${NC}"
    echo "   Fix: Install dependencies with: pip3 install -r api/requirements.txt"
    FAILED=1
else
    echo -e "${GREEN}✅ Python imports successful${NC}"
fi
cd ..

# Test 2: Check if all Python dependencies exist
echo -e "\n${YELLOW}2. Checking Python dependencies...${NC}"
cd api
pip3 install -r requirements.txt --dry-run > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Some Python packages may not be available on PyPI${NC}"
    FAILED=1
else
    echo -e "${GREEN}✅ All Python dependencies are valid${NC}"
fi
cd ..

# Test 3: Check Node.js dependencies
echo -e "\n${YELLOW}3. Testing Node.js build...${NC}"
cd frontend
npm install --dry-run > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Node dependency issues found${NC}"
    FAILED=1
else
    echo -e "${GREEN}✅ Node dependencies look good${NC}"
fi

# Test 4: Try building the frontend
echo -e "\n${YELLOW}4. Testing frontend build...${NC}"
npm run build > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Frontend build failed${NC}"
    echo "   Run 'npm run build' in frontend/ to see errors"
    FAILED=1
else
    echo -e "${GREEN}✅ Frontend builds successfully${NC}"
fi
cd ..

# Test 5: Check for common Vercel issues
echo -e "\n${YELLOW}5. Checking for common Vercel issues...${NC}"

# Check if index.py exists (required for Vercel Python)
if [ ! -f "api/index.py" ]; then
    echo -e "${RED}❌ api/index.py not found (required for Vercel)${NC}"
    FAILED=1
else
    echo -e "${GREEN}✅ api/index.py exists${NC}"
fi

# Check for vercel.json
if [ ! -f "vercel.json" ]; then
    echo -e "${YELLOW}⚠️  No vercel.json found (optional but recommended)${NC}"
else
    echo -e "${GREEN}✅ vercel.json exists${NC}"
fi

# Summary
echo -e "\n======================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed! Ready for deployment.${NC}"
    echo -e "\nNext steps:"
    echo "1. Commit your changes: git add . && git commit -m 'Your message'"
    echo "2. Push to your branch: git push origin your-branch"
    echo "3. Check the preview URL in your PR comments"
else
    echo -e "${RED}❌ Some tests failed. Fix the issues above before deploying.${NC}"
    exit 1
fi 