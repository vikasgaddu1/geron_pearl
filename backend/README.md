# PEARL Backend

FastAPI backend with async PostgreSQL CRUD operations for studies management.

## Package Management

This project uses **[UV](https://docs.astral.sh/uv/)** as the modern Python package manager for:
- ⚡ **Fast dependency resolution** and installation
- 🔒 **Deterministic builds** with lockfile support
- 🐍 **Python version management**
- 📦 **Unified toolchain** for project management

## Features

- 🚀 **FastAPI 0.111+** with async/await support
- 🐘 **PostgreSQL** with async SQLAlchemy 2.0 ORM
- 📝 **Pydantic 2** for request/response validation
- 🔄 **Alembic** for database migrations
- 🛡️ **Security** ready (OAuth2/JWT placeholders)
- 📚 **Auto-generated API docs** at `/docs` and `/redoc`
- ❤️ **Health checks** with database connectivity testing
- 🌐 **CORS** configured for frontend integration
- ⚡ **UV package management** for modern Python development

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── __init__.py      # API v1 router
│   │   │   └── studies.py       # Studies CRUD endpoints
│   │   └── health.py            # Health check endpoint
│   ├── core/
│   │   ├── config.py           # Application settings
│   │   └── security.py         # Security utilities
│   ├── crud/
│   │   ├── __init__.py
│   │   └── study.py            # Study CRUD operations
│   ├── db/
│   │   ├── base.py             # SQLAlchemy base
│   │   ├── init_db.py          # Database initialization
│   │   └── session.py          # Database session
│   ├── models/
│   │   ├── __init__.py
│   │   └── study.py            # Study SQLAlchemy model
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── study.py            # Study Pydantic schemas
│   ├── __init__.py
│   └── main.py                 # FastAPI application
├── migrations/                 # Alembic migrations
├── .env                       # Environment variables
├── alembic.ini               # Alembic configuration
├── pyproject.toml            # Project dependencies
├── requirements.txt          # Pip requirements
└── run.py                    # Development server
```

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- [UV package manager](https://docs.astral.sh/uv/getting-started/installation/)

1. **Install UV** (if not already installed):
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Or via pip
   pip install uv
   ```

2. **Install dependencies**:
   ```bash
   # Using uv (recommended - faster and more reliable)
   uv pip install -r requirements.txt
   
   # Or create virtual environment and install
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

3. **Configure environment**:
   - Copy `.env.example` to `.env` (if exists) or use the existing `.env`
   - Update database connection string if needed

4. **Setup database**:
   ```bash
   # Initialize database (creates database if not exists + tables)
   uv run python -m app.db.init_db
   
   # Or use Alembic for migrations (database must exist first)
   uv run alembic revision --autogenerate -m "Initial migration"
   uv run alembic upgrade head
   ```

   **Note**: The init script will automatically:
   - Create the database if it doesn't exist
   - Create all required tables and indexes
   - Handle connection retries and proper error logging

5. **Run the application**:
   ```bash
   # Development server with auto-reload (using uv)
   uv run python run.py
   
   # Or directly with uvicorn via uv
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Traditional method (if not using uv)
   python run.py
   ```

   **If port 8000 is already in use**, kill the process:
   ```bash
   # Kill process using port 8000 directly
   fuser -k 8000/tcp
   
   # Or kill by process pattern
   pkill -f "port=8000"
   pkill -f "uvicorn.*8000"
   
   # Or find and kill by port
   lsof -ti:8000 | xargs kill -9
   
   # On Windows
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   ```

## API Endpoints

### Health Check
- `GET /health` - Check service and database health

### Studies CRUD
- `POST /api/v1/studies` - Create a new study
- `GET /api/v1/studies` - List all studies (with pagination)
- `GET /api/v1/studies/{study_id}` - Get study by ID
- `PUT /api/v1/studies/{study_id}` - Update study
- `DELETE /api/v1/studies/{study_id}` - Delete study

### Packages CRUD
- `POST /api/v1/packages` - Create a new package
- `GET /api/v1/packages` - List all packages (with pagination)
- `GET /api/v1/packages/{id}` - Get package by ID with items
- `PUT /api/v1/packages/{id}` - Update package
- `DELETE /api/v1/packages/{id}` - Delete package (protected if items exist)

### Package Items CRUD
- `POST /api/v1/packages/{id}/items` - Create package item with details
- `GET /api/v1/packages/{id}/items` - Get all items for a package
- `GET /api/v1/packages/items/{id}` - Get specific package item
- `PUT /api/v1/packages/items/{id}` - Update package item
- `DELETE /api/v1/packages/items/{id}` - Delete package item

### Documentation
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## Example Usage

### Create a Study
```bash
curl -X POST "http://localhost:8000/api/v1/studies" \
     -H "Content-Type: application/json" \
     -d '{"study_label": "My Research Study"}'
```

### Get All Studies
```bash
curl "http://localhost:8000/api/v1/studies"
```

### Get Study by ID
```bash
curl "http://localhost:8000/api/v1/studies/1"
```

### Update Study
```bash
curl -X PUT "http://localhost:8000/api/v1/studies/1" \
     -H "Content-Type: application/json" \
     -d '{"study_label": "Updated Study Name"}'
```

### Delete Study
```bash
curl -X DELETE "http://localhost:8000/api/v1/studies/1"
```

## Database Schema

### Studies Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| study_label | VARCHAR(255) | NOT NULL, INDEXED |

### Packages Tables
- **packages** - Main package table (id, package_name, timestamps)
- **package_items** - Polymorphic items table for TLFs and Datasets
  - Unique constraint: (package_id, item_type, item_subtype, item_code)
- **package_tlf_details** - TLF-specific attributes (title_id, population_flag_id)
- **package_dataset_details** - Dataset-specific attributes (label, sorting_order, acronyms)
- **package_item_footnotes** - Junction table for footnote associations
- **package_item_acronyms** - Junction table for acronym associations

## Development

### Running Tests

The application includes a comprehensive test suite with unit, integration, security, performance, and contract tests.

**See [tests/README.md](tests/README.md) for complete testing instructions, setup, and troubleshooting.**

### Code Formatting
```bash
# Format code with uv
uv run black app/
uv run isort app/

# Type checking
uv run mypy app/

# Lint code
uv run flake8 app/
uv run ruff check app/
```

### Database Migrations
```bash
# Generate migration with uv
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1

# Check migration status
uv run alembic current
uv run alembic history
```

## Critical Development Guidelines

### Schema-Model Alignment

**⚠️ IMPORTANT**: Pydantic schemas MUST exactly match SQLAlchemy model field types to prevent runtime validation errors.

#### Common Issues and Prevention

1. **Field Type Mismatches**
   - **Problem**: SQLAlchemy model has a string field, but Pydantic schema expects integer
   - **Example**: `priority` field defined as `String(50)` in model but `int` in schema
   - **Solution**: Always verify field types match between models and schemas
   ```python
   # Model (app/models/reporting_effort_item_tracker.py)
   priority: Mapped[str] = mapped_column(String(50), default="medium")
   
   # Schema (app/schemas/reporting_effort_item_tracker.py)
   priority: Optional[str] = Field(None, description="Priority level")  # ✅ Matches model
   # priority: Optional[int] = Field(None, ge=1, le=5)  # ❌ Would cause validation error
   ```

2. **Enum Serialization Issues**
   - **Problem**: Nested relationships with enums can fail Pydantic validation
   - **Example**: `ItemType.TLF` enum object vs "TLF" string value
   - **Solution**: Use `use_enum_values=True` in ConfigDict or avoid nested enum fields
   ```python
   model_config = ConfigDict(from_attributes=True, use_enum_values=True)
   ```

3. **Eager Loading Complications**
   - **Problem**: SQLAlchemy eager loading with `selectinload` can cause detached instance errors
   - **Solution**: Only eager load when necessary; remove if causing serialization issues

#### Debugging HTTP 500 Errors

When encountering "Internal Server Error" without visible logs:

1. **Add verbose error logging to endpoints**:
   ```python
   except Exception as e:
       logger.error(f"Error in endpoint: {str(e)}", exc_info=True)
       raise HTTPException(
           status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
           detail=f"Failed: {str(e)}"  # Include error in development
       )
   ```

2. **Test CRUD operations directly**:
   ```python
   # Create test_endpoint.py to isolate issues
   async def test():
       async with AsyncSessionLocal() as db:
           result = await crud_method.get_multi(db)
           # Try Pydantic validation
           Schema.model_validate(result[0])
   ```

3. **Run model validator after changes**:
   ```bash
   uv run python tests/validator/run_model_validation.py
   ```

4. **Common error patterns**:
   - `ResponseValidationError` → Schema doesn't match returned data
   - `DetachedInstanceError` → Lazy loading after session closed
   - `ValidationError` with enum → Enum value vs object mismatch
   - `int_parsing` error → String field expected as integer

#### Best Practices

1. **Always run model validator** after modifying models or schemas
2. **Test endpoints with curl** before frontend integration
3. **Use consistent field types** across the stack (DB → Model → Schema → API)
4. **Document field constraints** in both models and schemas
5. **Avoid complex nested relationships** in response schemas when possible

## Production Deployment

### Posit Connect Deployment

This application is designed for deployment on **Posit Connect** servers:

1. **Environment Configuration**:
   ```bash
   # Set production environment
   ENV=production
   DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
   JWT_SECRET=your-strong-secret-key-here
   ALLOWED_ORIGINS=["https://your-shiny-app.posit.co"]
   ```

2. **Deployment Steps**:
   - Set `ENV=production` in `.env` file
   - Update `DATABASE_URL` with production PostgreSQL credentials
   - Generate strong `JWT_SECRET` for security
   - Configure `ALLOWED_ORIGINS` for R Shiny frontend integration
   - Use `app.main:app` as the application entry point
   - Include `requirements.txt` for dependency management
   - Optionally include `uv.lock` for reproducible builds

3. **Database Setup on Posit Connect**:
   ```bash
   # Initialize production database
   uv run python -m app.db.init_db
   
   # Or use Alembic migrations
   uv run alembic upgrade head
   ```

4. **R Shiny Integration**:
   - FastAPI will serve as the backend API
   - R Shiny apps can connect via HTTP requests to `/api/v1/studies` endpoints
   - CORS is pre-configured for cross-origin requests

## Security Notes

- JWT authentication is prepared but not implemented
- API key authentication placeholder exists
- CORS is configured for development origins
- Update secrets for production use
- SQL injection prevention via bound parameters
- Comprehensive error handling with logging