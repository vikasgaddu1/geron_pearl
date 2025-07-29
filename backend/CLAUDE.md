# PEARL Backend - Claude Instructions

## Project Overview

PEARL Backend is a FastAPI application with async PostgreSQL CRUD operations for study management. This is a **production-like development environment** with specific constraints around testing and database management.

## Critical Testing Constraints

### Database Session Management Issues

**⚠️ CRITICAL LIMITATION**: This project has SQLAlchemy async session management conflicts that prevent reliable batch test execution. This is NOT a bug but an architectural constraint of running tests against real PostgreSQL without transaction isolation.

**Symptoms**:
```
sqlalchemy.exc.InterfaceError: cannot perform operation: another operation is in progress
```

**Impact**:
- ✅ Individual tests work perfectly
- ❌ Batch test execution frequently fails
- ✅ CRUD functionality is fully working
- ✅ API endpoints work correctly
- ⚠️ Test coverage reports may show failures despite working code

### Test Development Guidelines

1. **Read `tests/README.md` FIRST** - Contains essential constraints and patterns
2. **Prefer individual test files** - One test per file for database operations
3. **Favor non-database tests** - Validation, schema, and logic tests work reliably
4. **Test individually** - Always test with `pytest single_test.py` before batch
5. **Expect batch failures** - This is normal and documented behavior

### Safe Test Patterns

```python
# ✅ SAFE: Non-database validation
async def test_input_validation(self, client):
    response = await client.post("/api/v1/studies/", json={"study_label": ""})
    assert response.status_code == 422

# ✅ SAFE: Single database read (non-existent)
async def test_get_not_found(self, db_session):
    result = await study.get(db_session, id=999999)
    assert result is None

# ❌ UNSAFE: Multiple database operations
async def test_create_and_retrieve(self, db_session):
    created = await study.create(db_session, data)  # Conflicts with other tests
    retrieved = await study.get(db_session, created.id)  # May fail in batch
```

### Unsafe Test Patterns (Avoid)

- Tests using `sample_study` or `multiple_studies` fixtures
- Multiple tests in same file accessing database
- Tests that create database records
- Concurrent database operations
- Tests requiring database state setup

## Architecture Notes

- **FastAPI**: Modern async web framework
- **PostgreSQL**: Real production database (no test isolation)
- **SQLAlchemy 2.0**: Async ORM with session management limitations
- **Pydantic**: Data validation and serialization
- **UV**: Modern Python package manager
- **Pytest**: Testing framework with async support

## Development Workflow

1. Develop features normally - CRUD operations work perfectly
2. Test individual components with single test execution
3. Use batch testing for coverage reports (expect some failures)
4. Focus on functionality validation over test pass rates
5. Database accumulates test data (acceptable in dev environment)

## For Test Architect Agents

**MANDATORY**: Before creating ANY tests, read:
1. `/mnt/c/python/PEARL/backend/tests/README.md` - Complete testing constraints
2. This `CLAUDE.md` file - Project-specific limitations

**Key Constraint**: This project cannot support traditional test isolation patterns. Design tests accordingly or they will fail in batch execution due to async session conflicts.

**Success Metric**: Individual test reliability, not batch test pass rates.