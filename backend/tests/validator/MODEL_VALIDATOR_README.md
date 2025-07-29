# FastAPI Model Validator Agent

A specialized agent for validating that Pydantic and SQLAlchemy models are properly aligned in FastAPI applications. Detects schema mismatches, type conflicts, and missing fields before they cause frontend integration problems.

## 🎯 Purpose

The FastAPI Model Validator Agent helps prevent common issues in FastAPI applications by:

- **Early Detection**: Catches model misalignment issues before they reach production
- **Type Safety**: Ensures SQLAlchemy and Pydantic models use compatible types
- **Consistency Validation**: Verifies nullable/optional field consistency
- **Constraint Checking**: Validates that field constraints match between models
- **Relationship Mapping**: Ensures proper relationship definitions (future feature)

## 🚀 Quick Start

### Basic Usage

```bash
# Run validation on current project (from backend directory)
uv run python tests/validator/run_model_validation.py

# Run with specific project path
uv run python tests/validator/fastapi_model_validator.py /path/to/project

# Generate JSON report
uv run python tests/validator/fastapi_model_validator.py /path/to/project --format json

# Save report to file
uv run python tests/validator/fastapi_model_validator.py /path/to/project -o validation_report.txt
```

### Example Output

```
🔍 FastAPI Model Validator Agent
========================================

📂 Scanning project: /path/to/project
📋 Models path: /path/to/project/app/models
📄 Schemas path: /path/to/project/app/schemas

🔄 Discovering models...
✅ Validation complete! Found 3 issues.

FastAPI Model Validation Report
========================================

Summary:
  🔴 CRITICAL: 1
  🟠 HIGH: 1
  🟡 MEDIUM: 1

Type Mismatch:
--------------
🔴 Type mismatch for field 'age': SQLAlchemy uses 'Integer', Pydantic uses 'str'
   💡 Suggestion: Ensure both models use compatible types for field 'age'
   🏷️  Field: age
   📋 Models: User ↔ UserSchema
```

## 🔍 Issues Detected

### Critical Issues (🔴)

**Type Mismatches**: Incompatible types between SQLAlchemy and Pydantic models
```python
# SQLAlchemy Model
class User(Base):
    age: Mapped[int] = mapped_column(Integer)

# Pydantic Schema  
class UserSchema(BaseModel):
    age: str  # ❌ Should be int
```

### High Severity Issues (🟠)

**Missing Fields**: Fields exist in one model but not the other
```python
# SQLAlchemy Model
class User(Base):
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))

# Pydantic Schema
class UserSchema(BaseModel):
    name: str
    # ❌ Missing email field
```

**Nullable Mismatches**: SQLAlchemy nullable doesn't match Pydantic optional
```python
# SQLAlchemy Model
class User(Base):
    bio: Mapped[str] = mapped_column(String(500), nullable=True)

# Pydantic Schema
class UserSchema(BaseModel):
    bio: str  # ❌ Should be Optional[str]
```

### Medium Severity Issues (🟡)

**Constraint Mismatches**: Different constraints between models
```python
# SQLAlchemy Model
class User(Base):
    name: Mapped[str] = mapped_column(String(100))

# Pydantic Schema
class UserSchema(BaseModel):
    name: str = Field(max_length=255)  # ❌ Different max length
```

### Info Issues (ℹ️)

**Naming Convention**: Missing expected Pydantic schemas for SQLAlchemy models

## 📁 Project Structure

The validator expects the following FastAPI project structure:

```
project/
├── app/
│   ├── models/          # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── study.py
│   └── schemas/         # Pydantic schemas
│       ├── __init__.py
│       ├── user.py
│       └── study.py
└── fastapi_model_validator.py
```

## ⚙️ Configuration

### Custom Configuration

Create a `model_validator_config.py` file to customize validation behavior:

```python
from model_validator_config import ValidatorConfig

config = ValidatorConfig(
    models_path="app/models",
    schemas_path="app/schemas",
    enforce_naming_conventions=True,
    require_field_descriptions=True,
    type_mismatch_severity="CRITICAL"
)
```

### Ignore Rules

Create a `validation_ignore.yaml` file to ignore specific issues:

```yaml
ignore_rules:
  - category: "nullable_mismatch"
    sqlalchemy_model: "Study"
    pydantic_model: "StudyUpdate"
    field_name: "study_label"
    reason: "Update schemas should allow optional fields"
```

## 🔧 Integration

### VS Code Task

Add to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Validate Models",
      "type": "shell",
      "command": "uv",
      "args": ["run", "python", "tests/validator/run_model_validation.py"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    }
  ]
}
```

## 📊 Report Formats

### Text Report (Default)

Human-readable format with color-coded severity levels and actionable suggestions.

### JSON Report

Machine-readable format for integration with other tools:

```json
{
  "summary": {
    "total_issues": 3,
    "severity_counts": {
      "CRITICAL": 1,
      "HIGH": 1,
      "MEDIUM": 1
    },
    "sqlalchemy_models": 2,
    "pydantic_models": 8
  },
  "issues": [
    {
      "severity": "CRITICAL",
      "category": "type_mismatch",
      "message": "Type mismatch for field 'age'...",
      "field_name": "age",
      "sqlalchemy_model": "User",
      "pydantic_model": "UserSchema",
      "suggestion": "Ensure both models use compatible types..."
    }
  ]
}
```

## 🏗️ Architecture

### Core Components

1. **Model Discovery**: Scans project files to find SQLAlchemy and Pydantic models
2. **AST Parsing**: Uses Python AST to extract field information from model classes
3. **Type Mapping**: Intelligent type comparison between SQLAlchemy and Pydantic types
4. **Inheritance Resolution**: Resolves Pydantic model inheritance to get complete field lists
5. **Validation Engine**: Runs various validation checks and generates issues
6. **Report Generation**: Formats results in text or JSON format

### Key Classes

- `FastAPIModelValidator`: Main validation orchestrator
- `ModelInfo`: Represents discovered model information
- `FieldInfo`: Detailed field information
- `ValidationIssue`: Represents a validation issue
- `TypeMapper`: Handles type compatibility checking

## 🧪 Testing

### Run Example Validation

```bash
# See detailed examples and common issues
uv run python tests/validator/example_validation_usage.py
```

### Manual Testing

Create test models with intentional mismatches:

```python
# app/models/test_model.py
class TestModel(Base):
    __tablename__ = "tests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

# app/schemas/test_model.py  
class TestSchema(BaseModel):
    id: str  # ❌ Type mismatch
    description: str  # ❌ Missing in SQLAlchemy
    # ❌ Missing name field
```

## 🔄 Best Practices

### Model Design

1. **Consistent Naming**: Use the same field names in both models
2. **Type Alignment**: Match SQLAlchemy and Pydantic types
3. **Nullable Consistency**: Make nullable SQLAlchemy fields Optional in Pydantic
4. **Schema Variants**: Create Base, Create, Update, InDB schemas as needed
5. **Constraint Matching**: Keep string lengths and validation rules consistent

### Validation Workflow

1. **Development**: Run validator after model changes
2. **Pre-commit**: Validate before committing code
3. **CI/CD**: Include in automated testing pipeline
4. **Regular Audits**: Run comprehensive validation periodically

### Error Resolution

1. **Critical Issues**: Fix immediately (type mismatches)
2. **High Issues**: Address before deployment (missing fields, nullable mismatches)
3. **Medium Issues**: Plan for next iteration (constraint differences)
4. **Info Issues**: Consider for code quality improvements

## 🚨 Common Issues & Solutions

### False Positives

If you get false positives:

1. Check if inheritance is working correctly
2. Verify field names match exactly (case-sensitive)
3. Use ignore rules for intentional differences
4. Update type mappings for custom types

### Performance

For large projects:

1. Use targeted validation on specific modules
2. Cache results for repeated runs
3. Run in parallel for multiple modules
4. Consider incremental validation

### Integration Issues

If integration fails:

1. Verify project structure matches expected layout
2. Check Python path and imports
3. Ensure all dependencies are installed
4. Review error logs for specific issues

## 📈 Future Enhancements

- **Relationship Validation**: Validate foreign key relationships
- **Migration Alignment**: Check Alembic migrations against models
- **Performance Metrics**: Track validation performance
- **Custom Validators**: Plugin system for custom validation rules
- **IDE Integration**: VS Code extension for real-time validation
- **Auto-fix Suggestions**: Automatic code generation for fixes

## 🤝 Contributing

To extend the validator:

1. Add new validation methods to `FastAPIModelValidator`
2. Create custom type mappings in `TypeMapper`
3. Extend configuration options in `ValidatorConfig`
4. Add new issue categories and severities
5. Improve AST parsing for complex patterns

## 📝 License

This FastAPI Model Validator Agent is part of the PEARL project and follows the same licensing terms.

---

**Generated by Claude Code Agent** - Early detection saves integration time! 🚀