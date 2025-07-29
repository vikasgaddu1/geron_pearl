#!/usr/bin/env python3
"""
FastAPI Model Validator Agent

A specialized agent for validating that Pydantic and SQLAlchemy models are properly aligned.
Detects schema mismatches, type conflicts, and missing fields before they cause integration issues.

Author: Claude Code Agent
Version: 1.0.0
"""

import ast
import inspect
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union, get_origin, get_args

try:
    import sqlalchemy
    from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text
    from sqlalchemy.orm import Mapped
    from sqlalchemy.sql.schema import MetaData
    from sqlalchemy.ext.declarative import DeclarativeMeta
except ImportError:
    print("SQLAlchemy not found. Please install: pip install sqlalchemy")
    sys.exit(1)

try:
    import pydantic
    from pydantic import BaseModel, Field
    from pydantic.fields import FieldInfo
except ImportError:
    print("Pydantic not found. Please install: pip install pydantic")
    sys.exit(1)


class Severity(Enum):
    """Issue severity levels."""
    CRITICAL = "CRITICAL"  # Will cause runtime errors
    HIGH = "HIGH"        # Likely to cause issues
    MEDIUM = "MEDIUM"    # May cause inconsistencies
    LOW = "LOW"          # Style/best practice issues
    INFO = "INFO"        # Informational notices


@dataclass
class FieldInfo:
    """Information about a model field."""
    name: str
    type_: str
    python_type: Optional[type] = None
    nullable: bool = False
    optional: bool = False
    default: Any = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None


@dataclass
class ModelInfo:
    """Information about a model (SQLAlchemy or Pydantic)."""
    name: str
    module: str
    file_path: str
    fields: Dict[str, FieldInfo] = field(default_factory=dict)
    base_classes: List[str] = field(default_factory=list)
    table_name: Optional[str] = None


@dataclass
class ValidationIssue:
    """A validation issue found during model comparison."""
    severity: Severity
    category: str
    message: str
    field_name: Optional[str] = None
    sqlalchemy_model: Optional[str] = None
    pydantic_model: Optional[str] = None
    suggestion: Optional[str] = None
    line_number: Optional[int] = None


class TypeMapper:
    """Maps between SQLAlchemy and Pydantic types."""
    
    # SQLAlchemy to Python type mapping
    SQLALCHEMY_TO_PYTHON = {
        'Integer': int,
        'String': str,
        'Text': str,
        'Boolean': bool,
        'Float': float,
        'DateTime': 'datetime',
        'Date': 'date',
        'Time': 'time',
        'Numeric': float,
        'BigInteger': int,
        'SmallInteger': int,
        'CHAR': str,
        'VARCHAR': str,
        'TEXT': str,
        'BOOLEAN': bool,
        'REAL': float,
        'DOUBLE_PRECISION': float,
        'TIMESTAMP': 'datetime',
        'UUID': str,
        'JSON': dict,
        'JSONB': dict,
    }
    
    # Common type equivalencies
    TYPE_EQUIVALENCIES = {
        ('str', 'string'): True,
        ('int', 'integer'): True,
        ('float', 'number'): True,
        ('bool', 'boolean'): True,
        ('datetime', 'timestamp'): True,
        ('dict', 'object'): True,
        ('list', 'array'): True,
    }
    
    @classmethod
    def normalize_type(cls, type_str: str) -> str:
        """Normalize type string for comparison."""
        if not type_str:
            return 'unknown'
        
        # Remove module prefixes
        type_str = type_str.split('.')[-1]
        
        # Handle SQLAlchemy Mapped[T] types - extract the inner type
        if type_str.startswith('Mapped[') and type_str.endswith(']'):
            inner_type = type_str[7:-1]  # Remove 'Mapped[' and ']'
            return cls.normalize_type(inner_type)
        
        # Handle Optional[T] types
        if type_str.startswith('Optional[') and type_str.endswith(']'):
            inner_type = type_str[9:-1]  # Remove 'Optional[' and ']'
            return cls.normalize_type(inner_type)
        
        # Handle Union types (like Union[str, None])
        if type_str.startswith('Union['):
            # For Union types, take the first non-None type
            inner = type_str[6:-1]  # Remove 'Union[' and ']'
            types = [t.strip() for t in inner.split(',')]
            for t in types:
                if t.lower() != 'none' and 'nonetype' not in t.lower():
                    return cls.normalize_type(t)
        
        # Handle generic types
        if '[' in type_str:
            base_type = type_str.split('[')[0]
            return base_type.lower()
        
        return type_str.lower()
    
    @classmethod
    def types_compatible(cls, type1: str, type2: str) -> bool:
        """Check if two types are compatible."""
        norm1 = cls.normalize_type(type1)
        norm2 = cls.normalize_type(type2)
        
        if norm1 == norm2:
            return True
        
        # Check equivalencies
        for (t1, t2), compatible in cls.TYPE_EQUIVALENCIES.items():
            if (norm1 == t1 and norm2 == t2) or (norm1 == t2 and norm2 == t1):
                return compatible
        
        return False


class FastAPIModelValidator:
    """Main validator class for analyzing model alignment."""
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.sqlalchemy_models: Dict[str, ModelInfo] = {}
        self.pydantic_models: Dict[str, ModelInfo] = {}
        self.issues: List[ValidationIssue] = []
        self.type_mapper = TypeMapper()
    
    def validate_project(self) -> List[ValidationIssue]:
        """Validate all models in the project."""
        self.issues.clear()
        
        # Discover models
        self._discover_sqlalchemy_models()
        self._discover_pydantic_models()
        
        # Resolve inheritance for Pydantic models
        self._resolve_pydantic_inheritance()
        
        # Validate alignment
        self._validate_model_alignment()
        
        # Additional validations
        self._validate_naming_conventions()
        self._validate_relationship_consistency()
        
        return self.issues
    
    def _discover_sqlalchemy_models(self):
        """Discover SQLAlchemy models in the project."""
        models_dir = self.project_root / "app" / "models"
        if not models_dir.exists():
            return
        
        for py_file in models_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            try:
                self._parse_sqlalchemy_file(py_file)
            except Exception as e:
                self.issues.append(ValidationIssue(
                    severity=Severity.HIGH,
                    category="parsing_error",
                    message=f"Failed to parse SQLAlchemy model file {py_file}: {e}",
                    suggestion="Check file syntax and imports"
                ))
    
    def _discover_pydantic_models(self):
        """Discover Pydantic schemas in the project."""
        schemas_dir = self.project_root / "app" / "schemas"
        if not schemas_dir.exists():
            return
        
        for py_file in schemas_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            try:
                self._parse_pydantic_file(py_file)
            except Exception as e:
                self.issues.append(ValidationIssue(
                    severity=Severity.HIGH,
                    category="parsing_error",
                    message=f"Failed to parse Pydantic schema file {py_file}: {e}",
                    suggestion="Check file syntax and imports"
                ))
    
    def _parse_sqlalchemy_file(self, file_path: Path):
        """Parse a SQLAlchemy model file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                model_info = self._extract_sqlalchemy_model_info(node, file_path, content)
                if model_info:
                    self.sqlalchemy_models[model_info.name] = model_info
    
    def _parse_pydantic_file(self, file_path: Path):
        """Parse a Pydantic schema file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                model_info = self._extract_pydantic_model_info(node, file_path, content)
                if model_info:
                    self.pydantic_models[model_info.name] = model_info
    
    def _extract_sqlalchemy_model_info(self, node: ast.ClassDef, file_path: Path, content: str) -> Optional[ModelInfo]:
        """Extract information from SQLAlchemy model class."""
        # Check if it's a SQLAlchemy model
        base_names = [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]
        if 'Base' not in base_names:
            return None
        
        model_info = ModelInfo(
            name=node.name,
            module=file_path.stem,
            file_path=str(file_path),
            base_classes=base_names
        )
        
        # Extract table name
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == '__tablename__':
                        if isinstance(stmt.value, ast.Constant):
                            model_info.table_name = stmt.value.value
        
        # Extract fields
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                field_info = self._extract_sqlalchemy_field_info(stmt, content)
                if field_info:
                    model_info.fields[field_info.name] = field_info
        
        return model_info
    
    def _extract_pydantic_model_info(self, node: ast.ClassDef, file_path: Path, content: str) -> Optional[ModelInfo]:
        """Extract information from Pydantic model class."""
        # Check if it's a Pydantic model
        base_names = [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]
        if not any('BaseModel' in base or 'Base' in base for base in base_names):
            return None
        
        model_info = ModelInfo(
            name=node.name,
            module=file_path.stem,
            file_path=str(file_path),
            base_classes=base_names
        )
        
        # Extract fields from this class
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                field_info = self._extract_pydantic_field_info(stmt, content)
                if field_info:
                    model_info.fields[field_info.name] = field_info
        
        return model_info
    
    def _extract_sqlalchemy_field_info(self, stmt: ast.AnnAssign, content: str) -> Optional[FieldInfo]:
        """Extract field information from SQLAlchemy model."""
        field_name = stmt.target.id
        
        # Get type annotation
        type_str = self._ast_to_string(stmt.annotation)
        
        field_info = FieldInfo(
            name=field_name,
            type_=type_str
        )
        
        # Parse mapped_column or Column definition
        if stmt.value:
            if isinstance(stmt.value, ast.Call):
                if hasattr(stmt.value, 'func'):
                    func_name = self._ast_to_string(stmt.value.func)
                    if 'mapped_column' in func_name or 'Column' in func_name:
                        # Extract column properties
                        for arg in stmt.value.args:
                            if isinstance(arg, ast.Name):
                                # Column type
                                arg_name = arg.id
                                if arg_name in self.type_mapper.SQLALCHEMY_TO_PYTHON:
                                    field_info.python_type = self.type_mapper.SQLALCHEMY_TO_PYTHON[arg_name]
                        
                        # Extract keyword arguments
                        for keyword in stmt.value.keywords:
                            if keyword.arg == 'nullable':
                                field_info.nullable = self._evaluate_boolean(keyword.value)
                            elif keyword.arg == 'default':
                                field_info.default = self._ast_to_string(keyword.value)
                            elif keyword.arg == 'index':
                                field_info.constraints['index'] = self._evaluate_boolean(keyword.value)
                            elif keyword.arg == 'primary_key':
                                field_info.constraints['primary_key'] = self._evaluate_boolean(keyword.value)
                            elif keyword.arg == 'autoincrement':
                                field_info.constraints['autoincrement'] = self._evaluate_boolean(keyword.value)
        
        return field_info
    
    def _extract_pydantic_field_info(self, stmt: ast.AnnAssign, content: str) -> Optional[FieldInfo]:
        """Extract field information from Pydantic model."""
        field_name = stmt.target.id
        
        # Get type annotation
        type_str = self._ast_to_string(stmt.annotation)
        
        field_info = FieldInfo(
            name=field_name,
            type_=type_str
        )
        
        # Check if it's Optional
        if 'Optional' in type_str or 'Union' in type_str:
            field_info.optional = True
        
        # Parse Field definition
        if stmt.value:
            if isinstance(stmt.value, ast.Call):
                func_name = self._ast_to_string(stmt.value.func)
                if 'Field' in func_name:
                    # Extract Field arguments
                    if stmt.value.args:
                        # First positional argument is default
                        default_arg = stmt.value.args[0]
                        if isinstance(default_arg, ast.Constant):
                            field_info.default = default_arg.value
                        elif isinstance(default_arg, ast.Attribute) and default_arg.attr == 'Ellipsis':
                            field_info.default = ...  # Required field
                    
                    # Extract keyword arguments
                    for keyword in stmt.value.keywords:
                        if keyword.arg == 'description':
                            if isinstance(keyword.value, ast.Constant):
                                field_info.description = keyword.value.value
                        elif keyword.arg == 'min_length':
                            field_info.constraints['min_length'] = self._evaluate_constant(keyword.value)
                        elif keyword.arg == 'max_length':
                            field_info.constraints['max_length'] = self._evaluate_constant(keyword.value)
                        elif keyword.arg == 'gt':
                            field_info.constraints['gt'] = self._evaluate_constant(keyword.value)
                        elif keyword.arg == 'ge':
                            field_info.constraints['ge'] = self._evaluate_constant(keyword.value)
                        elif keyword.arg == 'lt':
                            field_info.constraints['lt'] = self._evaluate_constant(keyword.value)
                        elif keyword.arg == 'le':
                            field_info.constraints['le'] = self._evaluate_constant(keyword.value)
            elif isinstance(stmt.value, ast.Constant):
                field_info.default = stmt.value.value
        
        return field_info
    
    def _validate_model_alignment(self):
        """Validate alignment between SQLAlchemy and Pydantic models."""
        # Find potential model pairs
        model_pairs = self._find_model_pairs()
        
        for sqlalchemy_name, pydantic_names in model_pairs.items():
            sqlalchemy_model = self.sqlalchemy_models[sqlalchemy_name]
            
            for pydantic_name in pydantic_names:
                pydantic_model = self.pydantic_models[pydantic_name]
                self._validate_model_pair(sqlalchemy_model, pydantic_model)
    
    def _find_model_pairs(self) -> Dict[str, List[str]]:
        """Find likely pairs between SQLAlchemy and Pydantic models."""
        pairs = {}
        
        for sqlalchemy_name in self.sqlalchemy_models:
            matching_pydantic = []
            
            # Direct name match
            if sqlalchemy_name in self.pydantic_models:
                matching_pydantic.append(sqlalchemy_name)
            
            # Look for variations (StudyBase, StudyCreate, StudyInDB, etc.)
            for pydantic_name in self.pydantic_models:
                if (pydantic_name.startswith(sqlalchemy_name) or 
                    pydantic_name.endswith(sqlalchemy_name) or
                    sqlalchemy_name in pydantic_name):
                    if pydantic_name not in matching_pydantic:
                        matching_pydantic.append(pydantic_name)
            
            if matching_pydantic:
                pairs[sqlalchemy_name] = matching_pydantic
        
        return pairs
    
    def _validate_model_pair(self, sqlalchemy_model: ModelInfo, pydantic_model: ModelInfo):
        """Validate a specific SQLAlchemy/Pydantic model pair."""
        # Check for missing fields
        self._check_missing_fields(sqlalchemy_model, pydantic_model)
        
        # Check for type mismatches
        self._check_type_mismatches(sqlalchemy_model, pydantic_model)
        
        # Check nullable/optional consistency
        self._check_nullable_consistency(sqlalchemy_model, pydantic_model)
        
        # Check constraint consistency
        self._check_constraint_consistency(sqlalchemy_model, pydantic_model)
    
    def _check_missing_fields(self, sqlalchemy_model: ModelInfo, pydantic_model: ModelInfo):
        """Check for missing fields between models."""
        sqlalchemy_fields = set(sqlalchemy_model.fields.keys())
        pydantic_fields = set(pydantic_model.fields.keys())
        
        # Fields in SQLAlchemy but not in Pydantic
        missing_in_pydantic = sqlalchemy_fields - pydantic_fields
        for field_name in missing_in_pydantic:
            # Skip fields that are commonly excluded from certain Pydantic models
            should_skip = False
            
            # Skip 'id' field in Base, Create, and Update schemas (but not InDB)
            if field_name == 'id' and any(suffix in pydantic_model.name for suffix in ['Base', 'Create', 'Update']):
                should_skip = True
            
            # Skip timestamp fields in Create schemas
            if field_name in ['created_at', 'updated_at', 'deleted_at'] and 'Create' in pydantic_model.name:
                should_skip = True
            
            if should_skip:
                continue
            
            # Determine severity based on field importance
            severity = Severity.MEDIUM
            if field_name == 'id' and 'InDB' in pydantic_model.name:
                severity = Severity.HIGH  # ID is critical for InDB schemas
            
            self.issues.append(ValidationIssue(
                severity=severity,
                category="missing_field",
                message=f"Field '{field_name}' exists in SQLAlchemy model '{sqlalchemy_model.name}' but not in Pydantic model '{pydantic_model.name}'",
                field_name=field_name,
                sqlalchemy_model=sqlalchemy_model.name,
                pydantic_model=pydantic_model.name,
                suggestion=f"Add field '{field_name}' to Pydantic model or verify if it should be excluded"
            ))
        
        # Fields in Pydantic but not in SQLAlchemy
        missing_in_sqlalchemy = pydantic_fields - sqlalchemy_fields
        for field_name in missing_in_sqlalchemy:
            self.issues.append(ValidationIssue(
                severity=Severity.HIGH,
                category="missing_field",
                message=f"Field '{field_name}' exists in Pydantic model '{pydantic_model.name}' but not in SQLAlchemy model '{sqlalchemy_model.name}'",
                field_name=field_name,
                sqlalchemy_model=sqlalchemy_model.name,
                pydantic_model=pydantic_model.name,
                suggestion=f"Add field '{field_name}' to SQLAlchemy model or remove from Pydantic model"
            ))
    
    def _check_type_mismatches(self, sqlalchemy_model: ModelInfo, pydantic_model: ModelInfo):
        """Check for type mismatches between models."""
        common_fields = set(sqlalchemy_model.fields.keys()) & set(pydantic_model.fields.keys())
        
        for field_name in common_fields:
            sqlalchemy_field = sqlalchemy_model.fields[field_name]
            pydantic_field = pydantic_model.fields[field_name]
            
            if not self.type_mapper.types_compatible(sqlalchemy_field.type_, pydantic_field.type_):
                self.issues.append(ValidationIssue(
                    severity=Severity.CRITICAL,
                    category="type_mismatch",
                    message=f"Type mismatch for field '{field_name}': SQLAlchemy uses '{sqlalchemy_field.type_}', Pydantic uses '{pydantic_field.type_}'",
                    field_name=field_name,
                    sqlalchemy_model=sqlalchemy_model.name,
                    pydantic_model=pydantic_model.name,
                    suggestion=f"Ensure both models use compatible types for field '{field_name}'"
                ))
    
    def _check_nullable_consistency(self, sqlalchemy_model: ModelInfo, pydantic_model: ModelInfo):
        """Check for nullable/optional consistency."""
        common_fields = set(sqlalchemy_model.fields.keys()) & set(pydantic_model.fields.keys())
        
        for field_name in common_fields:
            sqlalchemy_field = sqlalchemy_model.fields[field_name]
            pydantic_field = pydantic_model.fields[field_name]
            
            # SQLAlchemy nullable should match Pydantic optional
            if sqlalchemy_field.nullable and not pydantic_field.optional:
                self.issues.append(ValidationIssue(
                    severity=Severity.HIGH,
                    category="nullable_mismatch",
                    message=f"Field '{field_name}' is nullable in SQLAlchemy but not optional in Pydantic",
                    field_name=field_name,
                    sqlalchemy_model=sqlalchemy_model.name,
                    pydantic_model=pydantic_model.name,
                    suggestion=f"Make field '{field_name}' optional in Pydantic model: Optional[{pydantic_field.type_}]"
                ))
            elif not sqlalchemy_field.nullable and pydantic_field.optional:
                self.issues.append(ValidationIssue(
                    severity=Severity.HIGH,
                    category="nullable_mismatch",
                    message=f"Field '{field_name}' is not nullable in SQLAlchemy but optional in Pydantic",
                    field_name=field_name,
                    sqlalchemy_model=sqlalchemy_model.name,
                    pydantic_model=pydantic_model.name,
                    suggestion=f"Make field '{field_name}' nullable in SQLAlchemy or required in Pydantic"
                ))
    
    def _check_constraint_consistency(self, sqlalchemy_model: ModelInfo, pydantic_model: ModelInfo):
        """Check for constraint consistency between models."""
        common_fields = set(sqlalchemy_model.fields.keys()) & set(pydantic_model.fields.keys())
        
        for field_name in common_fields:
            sqlalchemy_field = sqlalchemy_model.fields[field_name]
            pydantic_field = pydantic_model.fields[field_name]
            
            # Check string length constraints
            if 'String' in sqlalchemy_field.type_:
                # Extract length from String(255)
                length_match = re.search(r'String\((\d+)\)', sqlalchemy_field.type_)
                if length_match:
                    sqlalchemy_max_length = int(length_match.group(1))
                    pydantic_max_length = pydantic_field.constraints.get('max_length')
                    
                    if pydantic_max_length and pydantic_max_length != sqlalchemy_max_length:
                        self.issues.append(ValidationIssue(
                            severity=Severity.MEDIUM,
                            category="constraint_mismatch",
                            message=f"String length constraint mismatch for field '{field_name}': SQLAlchemy allows {sqlalchemy_max_length}, Pydantic allows {pydantic_max_length}",
                            field_name=field_name,
                            sqlalchemy_model=sqlalchemy_model.name,
                            pydantic_model=pydantic_model.name,
                            suggestion=f"Ensure both models use the same max_length constraint for field '{field_name}'"
                        ))
    
    def _validate_naming_conventions(self):
        """Validate naming conventions."""
        # Check for consistent model naming
        for sqlalchemy_name in self.sqlalchemy_models:
            # Look for corresponding Pydantic models
            expected_pydantic_names = [
                sqlalchemy_name,
                f"{sqlalchemy_name}Base",
                f"{sqlalchemy_name}Create",
                f"{sqlalchemy_name}Update",
                f"{sqlalchemy_name}InDB"
            ]
            
            found_any = any(name in self.pydantic_models for name in expected_pydantic_names)
            if not found_any:
                self.issues.append(ValidationIssue(
                    severity=Severity.INFO,
                    category="naming_convention",
                    message=f"No corresponding Pydantic schemas found for SQLAlchemy model '{sqlalchemy_name}'",
                    sqlalchemy_model=sqlalchemy_name,
                    suggestion=f"Consider creating Pydantic schemas: {', '.join(expected_pydantic_names)}"
                ))
    
    def _resolve_pydantic_inheritance(self):
        """Resolve inheritance for Pydantic models to get complete field lists."""
        # Build dependency graph
        resolved = set()
        
        def resolve_model(model_name: str, model_info: ModelInfo):
            if model_name in resolved:
                return
            
            # Resolve parent classes first
            for base_class in model_info.base_classes:
                if base_class in self.pydantic_models and base_class not in resolved:
                    resolve_model(base_class, self.pydantic_models[base_class])
            
            # Inherit fields from parent classes
            for base_class in model_info.base_classes:
                if base_class in self.pydantic_models:
                    parent_model = self.pydantic_models[base_class]
                    # Add parent fields that aren't overridden
                    for field_name, field_info in parent_model.fields.items():
                        if field_name not in model_info.fields:
                            model_info.fields[field_name] = field_info
            
            resolved.add(model_name)
        
        # Resolve all models
        for model_name, model_info in self.pydantic_models.items():
            resolve_model(model_name, model_info)
    
    def _validate_relationship_consistency(self):
        """Validate relationship mappings between models."""
        # This is a placeholder for relationship validation
        # In a full implementation, this would check foreign keys, relationships, etc.
        pass
    
    def _ast_to_string(self, node: ast.AST) -> str:
        """Convert AST node to string representation."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._ast_to_string(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._ast_to_string(node.value)}[{self._ast_to_string(node.slice)}]"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Tuple):
            elements = [self._ast_to_string(elt) for elt in node.elts]
            return f"({', '.join(elements)})"
        else:
            return str(node)
    
    def _evaluate_boolean(self, node: ast.AST) -> bool:
        """Evaluate boolean value from AST node."""
        if isinstance(node, ast.Constant):
            return bool(node.value)
        elif isinstance(node, ast.NameConstant):
            return bool(node.value)
        return False
    
    def _evaluate_constant(self, node: ast.AST) -> Any:
        """Evaluate constant value from AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.NameConstant):
            return node.value
        return None
    
    def generate_report(self, output_format: str = "text") -> str:
        """Generate validation report."""
        if output_format == "json":
            return self._generate_json_report()
        else:
            return self._generate_text_report()
    
    def _generate_text_report(self) -> str:
        """Generate text format report."""
        if not self.issues:
            return "✅ No validation issues found! Models are properly aligned."
        
        report = []
        report.append("FastAPI Model Validation Report")
        report.append("=" * 40)
        report.append("")
        
        # Summary
        severity_counts = {}
        for issue in self.issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        report.append("Summary:")
        for severity in Severity:
            count = severity_counts.get(severity, 0)
            if count > 0:
                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "INFO": "ℹ️"}[severity.value]
                report.append(f"  {icon} {severity.value}: {count}")
        report.append("")
        
        # Group issues by category
        categories = {}
        for issue in self.issues:
            if issue.category not in categories:
                categories[issue.category] = []
            categories[issue.category].append(issue)
        
        for category, issues in categories.items():
            report.append(f"{category.replace('_', ' ').title()}:")
            report.append("-" * (len(category) + 1))
            
            for issue in issues:
                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "INFO": "ℹ️"}[issue.severity.value]
                report.append(f"{icon} {issue.message}")
                
                if issue.suggestion:
                    report.append(f"   💡 Suggestion: {issue.suggestion}")
                
                if issue.field_name:
                    report.append(f"   🏷️  Field: {issue.field_name}")
                
                if issue.sqlalchemy_model and issue.pydantic_model:
                    report.append(f"   📋 Models: {issue.sqlalchemy_model} ↔ {issue.pydantic_model}")
                
                report.append("")
        
        return "\n".join(report)
    
    def _generate_json_report(self) -> str:
        """Generate JSON format report."""
        import json
        
        report_data = {
            "summary": {
                "total_issues": len(self.issues),
                "severity_counts": {},
                "sqlalchemy_models": len(self.sqlalchemy_models),
                "pydantic_models": len(self.pydantic_models)
            },
            "issues": []
        }
        
        # Count severities
        for issue in self.issues:
            severity = issue.severity.value
            report_data["summary"]["severity_counts"][severity] = \
                report_data["summary"]["severity_counts"].get(severity, 0) + 1
        
        # Add issues
        for issue in self.issues:
            issue_data = {
                "severity": issue.severity.value,
                "category": issue.category,
                "message": issue.message,
                "field_name": issue.field_name,
                "sqlalchemy_model": issue.sqlalchemy_model,
                "pydantic_model": issue.pydantic_model,
                "suggestion": issue.suggestion,
                "line_number": issue.line_number
            }
            report_data["issues"].append(issue_data)
        
        return json.dumps(report_data, indent=2)


def main():
    """Main entry point for the validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="FastAPI Model Validator Agent")
    parser.add_argument("project_path", help="Path to the FastAPI project root")
    parser.add_argument("--format", choices=["text", "json"], default="text", 
                       help="Output format (default: text)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    
    args = parser.parse_args()
    
    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Error: Project path '{project_path}' does not exist")
        sys.exit(1)
    
    validator = FastAPIModelValidator(project_path)
    issues = validator.validate_project()
    
    report = validator.generate_report(args.format)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)
    
    # Exit with error code if critical or high severity issues found
    has_critical_issues = any(issue.severity in [Severity.CRITICAL, Severity.HIGH] for issue in issues)
    sys.exit(1 if has_critical_issues else 0)


if __name__ == "__main__":
    main()