# Validation Agent

A specialized agent for running FastAPI model validation checks and providing detailed feedback on Pydantic/SQLAlchemy model alignment issues.

## Purpose

This agent validates that Pydantic and SQLAlchemy models are properly aligned in the PEARL FastAPI application. It detects schema mismatches, type conflicts, and missing fields before they cause integration problems.

## Usage

To run validation checks, use one of these approaches:

### Option 1: Quick Validation (Recommended)
```bash
# From the backend directory
uv run python tests/validator/run_model_validation.py
```

### Option 2: Detailed Validation with Options
```bash
# Run with specific options
uv run python tests/validator/fastapi_model_validator.py /path/to/project

# Generate JSON report
uv run python tests/validator/fastapi_model_validator.py /path/to/project --format json

# Save report to file
uv run python tests/validator/fastapi_model_validator.py /path/to/project -o validation_report.txt
```

## What It Checks

The validation agent performs the following checks:

### 🔴 Critical Issues
- **Type Mismatches**: SQLAlchemy and Pydantic models with incompatible field types
- **Missing Required Fields**: Required fields missing from corresponding models
- **Nullable/Optional Conflicts**: Misalignment between nullable and optional field definitions

### 🟡 High Priority Issues  
- **Field Name Inconsistencies**: Fields with different names between related models
- **Constraint Mismatches**: Different validation constraints between models
- **Missing Pydantic Models**: SQLAlchemy models without corresponding Pydantic schemas

### 🟢 Medium/Low Priority Issues
- **Naming Convention Violations**: Models not following expected naming patterns
- **Missing Field Descriptions**: Fields without proper documentation
- **Optimization Opportunities**: Suggestions for better model organization

## Output Format

The agent provides:

1. **Discovery Summary**: Shows all found models and their field counts
2. **Issue Report**: Categorized list of problems with severity levels
3. **Suggestions**: Actionable recommendations for fixing issues
4. **Exit Code**: Non-zero if critical/high severity issues found

## Example Output

```
🔍 FastAPI Model Validator Agent
========================================

📂 Scanning project: /mnt/c/python/PEARL/backend
📋 Models path: /mnt/c/python/PEARL/backend/app/models
📄 Schemas path: /mnt/c/python/PEARL/backend/app/schemas

🔄 Discovering models...
✅ Validation complete! Found 0 issues.

📋 Model Discovery Summary:
   SQLAlchemy models: 1 found
     • Study (5 fields)
   Pydantic models: 4 found
     • StudyBase (4 fields)
     • StudyCreate (4 fields)
     • StudyUpdate (4 fields)
     • Study (5 fields)

FastAPI Model Validation Report
========================================

Summary:
  ✅ No issues found!

✅ No critical issues found. Models appear to be properly aligned!
```

## Configuration

The validator uses configuration from `backend/tests/validator/model_validator_config.py`:

- **Model Paths**: `app/models` for SQLAlchemy, `app/schemas` for Pydantic
- **Validation Rules**: Type checking, constraint validation, naming conventions
- **Severity Levels**: Configurable thresholds for different issue types
- **Ignored Fields**: Common fields like timestamps can be excluded

## Integration

This agent can be integrated into:

- **Pre-commit Hooks**: Validate models before committing changes
- **CI/CD Pipeline**: Automated validation in GitHub Actions
- **Development Workflow**: Regular checks during feature development
- **Code Reviews**: Validate model changes during PR reviews

## Files

The validation system consists of:

- `fastapi_model_validator.py` - Main validation engine
- `model_validator_config.py` - Configuration settings
- `run_model_validation.py` - Simple runner script
- `validation_ignore.yaml` - Patterns to ignore during validation
- `MODEL_VALIDATOR_README.md` - Detailed documentation

## Best Practices

1. **Run Before Deployment**: Always validate models before production deployment
2. **Address Critical Issues**: Fix CRITICAL and HIGH severity issues immediately
3. **Regular Validation**: Include in development workflow and CI/CD
4. **Review Suggestions**: Consider MEDIUM/LOW issues for code quality improvements
5. **Update Configuration**: Customize validation rules for project-specific needs