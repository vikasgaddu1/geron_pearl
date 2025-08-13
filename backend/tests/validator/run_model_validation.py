#!/usr/bin/env python3
"""
FastAPI Model Validator Runner

Simple script to run model validation on the current project.
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi_model_validator import FastAPIModelValidator
from model_validator_config import DEFAULT_CONFIG


def main():
    """Run model validation on the current project."""
    print("[SEARCH] FastAPI Model Validator Agent")
    print("=" * 40)
    print()
    
    # Get project root (go up from tests/validator to backend)
    project_root = Path(__file__).parent.parent.parent
    
    print(f"[DIR] Scanning project: {project_root}")
    print(f"[MODELS] Models path: {project_root / DEFAULT_CONFIG.models_path}")
    print(f"[SCHEMAS] Schemas path: {project_root / DEFAULT_CONFIG.schemas_path}")
    print()
    
    # Initialize and run validator
    validator = FastAPIModelValidator(project_root)
    
    print("[LOADING] Discovering models...")
    issues = validator.validate_project()
    
    print(f"[COMPLETE] Validation complete! Found {len(issues)} issues.")
    print()
    
    # Show discovered models summary
    print("[SUMMARY] Model Discovery Summary:")
    print(f"   SQLAlchemy models: {len(validator.sqlalchemy_models)} found")
    for name in sorted(validator.sqlalchemy_models.keys()):
        model = validator.sqlalchemy_models[name]
        field_count = len(model.fields)
        print(f"     - {name} ({field_count} fields)")
    
    print(f"   Pydantic models: {len(validator.pydantic_models)} found")
    for name in sorted(validator.pydantic_models.keys()):
        model = validator.pydantic_models[name]
        field_count = len(model.fields)
        print(f"     - {name} ({field_count} fields)")
    print()
    
    # Generate and display report
    report = validator.generate_report("text")
    print(report)
    
    # Exit with appropriate code
    critical_issues = [i for i in issues if i.severity.value in ["CRITICAL", "HIGH"]]
    if critical_issues:
        print(f"\n[WARNING] Found {len(critical_issues)} critical/high severity issues!")
        print("Please address these issues before deployment.")
        return 1
    else:
        print("\n[SUCCESS] No critical issues found. Models appear to be properly aligned!")
        return 0


if __name__ == "__main__":
    sys.exit(main())