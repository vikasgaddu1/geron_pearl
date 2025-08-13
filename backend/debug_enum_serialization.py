#!/usr/bin/env python3
"""Debug script to test enum serialization in Pydantic models."""

from app.schemas.reporting_effort_item import ReportingEffortItemCreate
from app.models.reporting_effort_item import ItemType, SourceType
import json

# Test enum serialization
test_item = ReportingEffortItemCreate(
    reporting_effort_id=2,
    item_type="TLF",
    item_subtype="Table",
    item_code="TEST_CODE",
    source_type="custom"
)

print("Standard model_dump():")
standard_dump = test_item.model_dump()
print(f"  {standard_dump}")
print(f"  item_type type: {type(standard_dump['item_type'])}")
print(f"  source_type type: {type(standard_dump['source_type'])}")

print("\nWith mode='json':")
json_dump = test_item.model_dump(mode='json')
print(f"  {json_dump}")
print(f"  item_type type: {type(json_dump['item_type'])}")
print(f"  source_type type: {type(json_dump['source_type'])}")

print("\nJSON serializable?")
try:
    json_str = json.dumps(json_dump)
    print(f"  SUCCESS: {json_str}")
except Exception as e:
    print(f"  ERROR: {e}")