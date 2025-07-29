"""
Configuration file for FastAPI Model Validator

Customizable settings for model validation rules and behavior.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class ValidatorConfig:
    """Configuration settings for the FastAPI Model Validator."""
    
    # File patterns to include/exclude
    include_patterns: List[str] = field(default_factory=lambda: ["*.py"])
    exclude_patterns: List[str] = field(default_factory=lambda: ["__*", "test_*", "*_test.py"])
    
    # Model discovery paths
    models_path: str = "app/models"
    schemas_path: str = "app/schemas"
    
    # Validation rules
    enforce_naming_conventions: bool = True
    require_field_descriptions: bool = True
    check_constraint_consistency: bool = True
    validate_relationships: bool = True
    
    # Severity thresholds
    type_mismatch_severity: str = "CRITICAL"
    missing_field_severity: str = "HIGH"
    nullable_mismatch_severity: str = "HIGH"
    constraint_mismatch_severity: str = "MEDIUM"
    naming_convention_severity: str = "INFO"
    
    # Model pairing rules
    expected_pydantic_suffixes: List[str] = field(default_factory=lambda: [
        "", "Base", "Create", "Update", "InDB", "Response", "Schema"
    ])
    
    # Fields to ignore in validation
    ignored_fields: Set[str] = field(default_factory=lambda: {
        "created_at", "updated_at", "deleted_at"  # Common timestamp fields
    })
    
    # SQLAlchemy model detection
    sqlalchemy_base_classes: Set[str] = field(default_factory=lambda: {
        "Base", "DeclarativeBase", "AbstractConcreteBase"
    })
    
    # Pydantic model detection  
    pydantic_base_classes: Set[str] = field(default_factory=lambda: {
        "BaseModel", "BaseSchema", "Schema"
    })
    
    # Type mapping overrides
    custom_type_mappings: Dict[str, str] = field(default_factory=dict)
    
    # Constraint validation rules
    validate_string_lengths: bool = True
    validate_numeric_ranges: bool = True
    validate_pattern_constraints: bool = True
    
    # Report settings
    include_suggestions: bool = True
    group_by_severity: bool = True
    show_model_summary: bool = True
    
    @classmethod
    def for_project(cls, project_type: str = "fastapi") -> "ValidatorConfig":
        """Create configuration optimized for specific project types."""
        
        if project_type == "fastapi":
            return cls(
                models_path="app/models",
                schemas_path="app/schemas",
                require_field_descriptions=True,
                validate_relationships=True
            )
        elif project_type == "django":
            return cls(
                models_path="*/models",
                schemas_path="*/serializers", 
                sqlalchemy_base_classes={"models.Model"},
                pydantic_base_classes={"serializers.ModelSerializer"}
            )
        else:
            return cls()


# Default configuration instance
DEFAULT_CONFIG = ValidatorConfig.for_project("fastapi")