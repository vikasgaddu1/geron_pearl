# PEARL Backend Simple CRUD Tests

Simple and reliable testing approach for the PEARL FastAPI Studies CRUD application using curl commands.

## 🎯 Simple Testing Philosophy

**Core Principle**: Test what matters - functional endpoint behavior with real HTTP requests.

This simplified testing approach replaces the previous comprehensive but problematic testing framework with:
- ✅ **Direct endpoint testing** using curl commands
- ✅ **No SQLAlchemy session conflicts** - tests make HTTP requests like real clients
- ✅ **Predictable and reliable** - no async session management issues
- ✅ **Easy to understand and maintain** - simple bash script
- ✅ **Production-like testing** - tests actual HTTP endpoints
- ✅ **Automatic cleanup** - removes test data after execution

## 📁 Directory Structure

```
PEARL/
└── backend/              ← Run test script from here
    ├── app/             ← Application source code  
    ├── tests/           ← Simplified test directory
    │   ├── README.md    ← This file
    │   └── __init__.py  ← Python package marker
    ├── test_crud_simple.sh  ← Main test script
    └── pyproject.toml   ← Package configuration
```

## 🚀 Running Tests

### Prerequisites

```bash
# Ensure PostgreSQL is running
sudo service postgresql start  # On Ubuntu/WSL
# OR
brew services start postgresql  # On macOS

# Navigate to the backend directory
cd /mnt/c/python/PEARL/backend

# Start the FastAPI server
uv run uvicorn app.main:app --reload
```

### Quick Start

```bash
# Ensure you're in the backend directory
cd /mnt/c/python/PEARL/backend

# Run the simple CRUD tests
./test_crud_simple.sh
```

### What the Test Script Does

The script performs the following operations in sequence:

1. **Health Check** - Verifies server is running (`GET /health`)
2. **CREATE** - Creates a new study (`POST /api/v1/studies/`)
3. **READ ALL** - Lists all studies (`GET /api/v1/studies/`)
4. **READ ONE** - Gets the created study by ID (`GET /api/v1/studies/{id}`)
5. **UPDATE** - Updates the study label (`PUT /api/v1/studies/{id}`)
6. **READ UPDATED** - Verifies update persisted (`GET /api/v1/studies/{id}`)
7. **DELETE** - Deletes the study (`DELETE /api/v1/studies/{id}`)
8. **READ DELETED** - Verifies deletion (should return 404)
9. **DUPLICATE TEST** - Tests duplicate label prevention
10. **VALIDATION TEST** - Tests invalid data handling
11. **CLEANUP** - Removes any remaining test data

### Sample Output

```bash
$ ./test_crud_simple.sh

============================================
      PEARL Backend Simple CRUD Tests      
============================================
Base URL: http://localhost:8000
Test Label: test-study-1234567890
Timestamp: 1234567890
============================================

[INFO] Checking if server is running...
[PASS] Server is running
[INFO] Testing health endpoint...
[PASS] Health Check - Status: 200
[INFO] Testing CREATE endpoint...
[PASS] CREATE Study - Status: 201
[INFO] Created study with ID: 123
[INFO] Testing READ ALL endpoint...
[PASS] READ ALL Studies - Status: 200
[PASS] Created study found in studies list
[INFO] Testing READ ONE endpoint...
[PASS] READ ONE Study - Status: 200
[PASS] Study label matches expected value
[INFO] Testing UPDATE endpoint...
[PASS] UPDATE Study - Status: 200
[PASS] Study updated successfully with new label
[INFO] Testing READ after UPDATE...
[PASS] READ Updated Study - Status: 200
[PASS] Updated study label persisted correctly
[INFO] Testing DELETE endpoint...
[PASS] DELETE Study - Status: 200
[INFO] Testing READ deleted study (should return 404)...
[PASS] READ Deleted Study (404 expected) - Status: 404
[INFO] Testing duplicate label prevention...
[PASS] Duplicate Label Prevention - Status: 400
[INFO] Testing invalid data handling...
[PASS] Empty Label Validation - Status: 422
[INFO] Cleaning up test data...

============================================
              Test Results                  
============================================
Total Tests: 12
Passed: 12
Failed: 0

✅ All tests passed!
```

## 🔧 Test Configuration

### Environment Variables

The test script uses these defaults:
- **Base URL**: `http://localhost:8000`
- **Test Label**: `test-study-{timestamp}`
- **Updated Label**: `test-study-updated-{timestamp}`

### Customization

You can customize the test script by modifying these variables at the top:

```bash
BASE_URL="http://localhost:8000"        # Change server URL
API_BASE="${BASE_URL}/api/v1/studies"   # API endpoint base
```

## 📊 Test Coverage

### CRUD Operations Tested

- ✅ **CREATE**: Study creation with validation
- ✅ **READ**: Individual and bulk study retrieval  
- ✅ **UPDATE**: Study modification with validation
- ✅ **DELETE**: Study removal and verification

### API Endpoints Tested

- ✅ `GET /health` - Health check
- ✅ `POST /api/v1/studies/` - Create study
- ✅ `GET /api/v1/studies/` - List studies
- ✅ `GET /api/v1/studies/{id}` - Get study by ID
- ✅ `PUT /api/v1/studies/{id}` - Update study
- ✅ `DELETE /api/v1/studies/{id}` - Delete study

### Validation Testing

- ✅ **HTTP Status Codes**: Correct status for each operation (200, 201, 404, 422, 400)
- ✅ **Response Content**: JSON structure and field validation
- ✅ **Data Persistence**: Verify updates persist across requests
- ✅ **Error Handling**: Proper error responses for invalid data
- ✅ **Business Rules**: Duplicate label prevention
- ✅ **Data Cleanup**: All test data removed after execution

## 🔍 Troubleshooting

### Common Issues

#### Server Not Running
```
[FAIL] Server is not running at http://localhost:8000
```
**Solution**: Start the FastAPI server:
```bash
cd /mnt/c/python/PEARL/backend
uv run uvicorn app.main:app --reload
```

#### Database Connection Issues
```
[FAIL] CREATE Study - Status: 500
```
**Solution**: Ensure PostgreSQL is running and database exists:
```bash
sudo service postgresql start
psql -U postgres -c "SELECT 1;"
```

#### Permission Denied
```
bash: ./test_crud_simple.sh: Permission denied
```
**Solution**: Make script executable:
```bash
chmod +x test_crud_simple.sh
```

### Debug Mode

For detailed debugging, you can modify the script to show response content:
```bash
# Add this line after any curl command to see the response
cat "$response"
```

## 🎉 Benefits of Simple Testing

### Advantages Over Complex Framework

1. **No Session Conflicts**: HTTP requests don't have SQLAlchemy async session issues
2. **Production-Like**: Tests actual HTTP endpoints like real clients
3. **Reliable Execution**: No batch test failures or session management problems
4. **Easy Maintenance**: Single script that's easy to understand and modify
5. **Fast Execution**: Direct curl commands with immediate results
6. **Clear Output**: Color-coded results with pass/fail status
7. **Automatic Cleanup**: Removes test data even if tests fail

### Why This Approach Works

- **Real HTTP Testing**: Tests the actual API endpoints that clients use
- **No Test Dependencies**: No complex fixtures, factories, or database setup
- **Predictable Results**: Same results every time, no flaky tests
- **Easy Debugging**: Clear error messages and response inspection
- **Framework Independent**: Works regardless of test framework complexities

## 🔄 Integration with Development Workflow

### Before Committing Code
```bash
# Start server
uv run uvicorn app.main:app --reload

# In another terminal, run tests
cd /mnt/c/python/PEARL/backend
./test_crud_simple.sh
```

### Continuous Integration
The script returns appropriate exit codes:
- **Exit 0**: All tests passed
- **Exit 1**: Some tests failed

Perfect for CI/CD pipelines:
```yaml
- name: Run CRUD Tests
  run: |
    cd backend
    ./test_crud_simple.sh
```

## 📚 Understanding the Previous Architecture

The previous testing framework was comprehensive but had limitations:
- Complex pytest structure with session management issues
- Required deep understanding of SQLAlchemy async patterns
- Frequent batch test failures due to session conflicts
- High maintenance overhead for test fixtures and factories

This simple approach focuses on **functional validation** rather than **test framework complexity**, providing reliable and maintainable endpoint testing that matches real-world usage patterns.

## 🤝 Contributing

### Adding New Tests

To add new test scenarios to the script:

1. Add new test functions following the existing pattern
2. Use the `test_endpoint` helper function for consistency
3. Include proper cleanup for any created data
4. Update the test count and results summary

### Test Patterns

```bash
# Standard test pattern
response=$(mktemp)
status=$(curl -s -w "%{http_code}" -o "$response" [curl_options])
test_endpoint "Test Name" expected_status "$response" "$status"
rm "$response"
```

### Best Practices

- Use unique identifiers (timestamps) to avoid conflicts
- Always clean up created data
- Test both success and failure scenarios
- Provide clear, descriptive test names
- Include response validation when appropriate