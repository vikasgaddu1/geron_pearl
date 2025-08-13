#!/usr/bin/env python3
"""Debug script to inspect the actual schema fields."""

from app.schemas.reporting_effort_item import ReportingEffortItemCreate
import json

# Inspect the actual schema
schema = ReportingEffortItemCreate.model_json_schema()
print("Schema fields:")
for field_name, field_info in schema.get('properties', {}).items():
    print(f"  {field_name}: {field_info.get('type', 'unknown')} - {field_info.get('description', 'no description')}")

print(f"\nRequired fields: {schema.get('required', [])}")

# Try to create an instance
try:
    test_item = ReportingEffortItemCreate(
        reporting_effort_id=2,
        item_type="TLF",
        item_subtype="Table",
        item_code="TEST_CODE"
    )
    print(f"\nSuccessfully created: {test_item}")
    print(f"Model dump: {test_item.model_dump()}")
except Exception as e:
    print(f"\nError creating instance: {e}")