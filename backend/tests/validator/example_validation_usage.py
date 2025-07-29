#!/usr/bin/env python3
"""
Example usage of the FastAPI Model Validator

This script demonstrates how to use the validator and shows examples of
common issues it can detect.
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi_model_validator import FastAPIModelValidator, Severity


def demonstrate_validator():
    """Demonstrate the validator capabilities."""
    
    print("🧪 FastAPI Model Validator - Example Usage")
    print("=" * 50)
    print()
    
    # Initialize validator - go up from tests/validator to backend
    project_root = Path(__file__).parent.parent.parent
    validator = FastAPIModelValidator(project_root)
    
    # Run validation
    print("🔍 Running validation...")
    issues = validator.validate_project()
    
    print(f"📊 Found {len(issues)} total issues")
    print()
    
    # Show discovered models
    print("📋 Discovered Models:")
    print("-" * 20)
    print(f"SQLAlchemy models: {list(validator.sqlalchemy_models.keys())}")
    print(f"Pydantic models: {list(validator.pydantic_models.keys())}")
    print()
    
    # Generate detailed report
    text_report = validator.generate_report("text")
    json_report = validator.generate_report("json")
    
    print("📄 Text Report:")
    print("-" * 15)
    print(text_report)
    print()
    
    # Save JSON report
    json_file = Path("validation_report.json")
    with open(json_file, 'w') as f:
        f.write(json_report)
    print(f"💾 JSON report saved to: {json_file}")
    
    # Show issue breakdown
    if issues:
        print("\n🔍 Issue Analysis:")
        print("-" * 17)
        
        severity_groups = {}
        category_groups = {}
        
        for issue in issues:
            # Group by severity
            if issue.severity not in severity_groups:
                severity_groups[issue.severity] = []
            severity_groups[issue.severity].append(issue)
            
            # Group by category
            if issue.category not in category_groups:
                category_groups[issue.category] = []
            category_groups[issue.category].append(issue)
        
        print("By Severity:")
        for severity in Severity:
            count = len(severity_groups.get(severity, []))
            if count > 0:
                print(f"  {severity.value}: {count}")
        
        print("\nBy Category:")
        for category, issues_list in category_groups.items():
            print(f"  {category.replace('_', ' ').title()}: {len(issues_list)}")
    
    return len([i for i in issues if i.severity.value in ["CRITICAL", "HIGH"]])


def show_common_issues():
    """Show examples of common issues the validator can detect."""
    
    print("\n🚨 Common Issues the Validator Detects:")
    print("=" * 45)
    
    examples = [
        {
            "title": "Type Mismatch",
            "description": "SQLAlchemy uses Integer, Pydantic uses str",
            "severity": "CRITICAL",
            "example": """
            # SQLAlchemy Model
            class User(Base):
                age: Mapped[int] = mapped_column(Integer)
            
            # Pydantic Schema  
            class UserSchema(BaseModel):
                age: str  # ❌ Should be int
            """
        },
        {
            "title": "Missing Field",
            "description": "Field exists in one model but not the other",
            "severity": "HIGH",
            "example": """
            # SQLAlchemy Model
            class User(Base):
                name: Mapped[str] = mapped_column(String(255))
                email: Mapped[str] = mapped_column(String(255))
            
            # Pydantic Schema
            class UserSchema(BaseModel):
                name: str
                # ❌ Missing email field
            """
        },
        {
            "title": "Nullable Mismatch",
            "description": "SQLAlchemy nullable doesn't match Pydantic optional",
            "severity": "HIGH", 
            "example": """
            # SQLAlchemy Model
            class User(Base):
                bio: Mapped[str] = mapped_column(String(500), nullable=True)
            
            # Pydantic Schema
            class UserSchema(BaseModel):
                bio: str  # ❌ Should be Optional[str]
            """
        },
        {
            "title": "Constraint Mismatch",
            "description": "String length or other constraints don't match",
            "severity": "MEDIUM",
            "example": """
            # SQLAlchemy Model
            class User(Base):
                name: Mapped[str] = mapped_column(String(100))
            
            # Pydantic Schema
            class UserSchema(BaseModel):
                name: str = Field(max_length=255)  # ❌ Different max length
            """
        },
        {
            "title": "Missing Pydantic Schemas",
            "description": "SQLAlchemy model without corresponding Pydantic schemas", 
            "severity": "INFO",
            "example": """
            # SQLAlchemy Model exists
            class Product(Base):
                name: Mapped[str] = mapped_column(String(255))
            
            # ❌ No ProductBase, ProductCreate, ProductUpdate schemas found
            """
        }
    ]
    
    for i, example in enumerate(examples, 1):
        severity_icon = {
            "CRITICAL": "🔴",
            "HIGH": "🟠", 
            "MEDIUM": "🟡",
            "LOW": "🔵",
            "INFO": "ℹ️"
        }[example["severity"]]
        
        print(f"{i}. {severity_icon} {example['title']} ({example['severity']})")
        print(f"   {example['description']}")
        print(f"   Example:{example['example']}")
        print()


def show_best_practices():
    """Show best practices for model alignment."""
    
    print("✅ Best Practices for Model Alignment:")
    print("=" * 40)
    
    practices = [
        "Use consistent field names between SQLAlchemy and Pydantic models",
        "Ensure nullable SQLAlchemy fields are Optional in Pydantic",
        "Match string length constraints between models",
        "Create multiple Pydantic schemas: Base, Create, Update, InDB",
        "Use Field() with descriptions in Pydantic models",
        "Keep constraint validation consistent (min/max values, patterns)",
        "Document any intentional differences between models",
        "Run validation regularly in CI/CD pipeline",
        "Use type hints consistently throughout",
        "Consider using Pydantic's from_attributes=True for ORM compatibility"
    ]
    
    for i, practice in enumerate(practices, 1):
        print(f"{i:2d}. {practice}")
    
    print()


def main():
    """Main demonstration function."""
    
    # Run the actual validator
    critical_count = demonstrate_validator()
    
    # Show educational content
    show_common_issues()
    show_best_practices()
    
    print("🎯 Integration Tips:")
    print("=" * 18)
    print("• Run manually: uv run python tests/validator/run_model_validation.py")
    print("• Run after model changes to catch issues early")
    print("• Use JSON output for integration with other tools")
    print("• Set up as VS Code task for easy access")
    
    return critical_count


if __name__ == "__main__":
    critical_issues = main()
    if critical_issues > 0:
        print(f"\n⚠️  Exiting with error code due to {critical_issues} critical issues")
        sys.exit(1)
    else:
        print("\n✅ No critical issues found!")
        sys.exit(0)