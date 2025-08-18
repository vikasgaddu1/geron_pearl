#!/usr/bin/env python
"""Create test tracker data for debugging the reporting effort tracker UI."""

import asyncio
import sys
from datetime import datetime, timedelta
import random

sys.path.append('.')

from app.db.session import AsyncSessionLocal
from app.crud.study import study
from app.crud.database_release import database_release
from app.crud.reporting_effort import reporting_effort
from app.crud.reporting_effort_item import reporting_effort_item
from app.crud.reporting_effort_item_tracker import reporting_effort_item_tracker
from app.crud.crud_user import user
from app.crud.tracker_comment import tracker_comment

from app.schemas.study import StudyCreate
from app.schemas.database_release import DatabaseReleaseCreate
from app.schemas.reporting_effort import ReportingEffortCreate
from app.schemas.reporting_effort_item import ReportingEffortItemCreate
from app.schemas.reporting_effort_item_tracker import ReportingEffortItemTrackerUpdate
from app.schemas.user import UserCreate
from app.schemas.tracker_comment import TrackerCommentCreate

async def create_test_data():
    """Create comprehensive test data for tracker testing."""
    
    async with AsyncSessionLocal() as db:
        print("Creating test data for tracker management...")
        
        # Create a test study
        study_data = StudyCreate(
            study_label="PEARL-2025-001",
            study_name="Phase III Clinical Trial - Tracker Testing"
        )
        created_study = await study.create(db, obj_in=study_data)
        print(f"Created study: {created_study.study_label}")
        
        # Create a database release
        db_release_data = DatabaseReleaseCreate(
            study_id=created_study.id,
            database_release_label="January 2025 Primary Analysis",
            database_release_date=datetime(2025, 1, 15)
        )
        created_db_release = await database_release.create(db, obj_in=db_release_data)
        print(f"Created database release: {created_db_release.database_release_label}")
        
        # Create a reporting effort
        effort_data = ReportingEffortCreate(
            database_release_id=created_db_release.id,
            study_id=created_study.id,
            database_release_label="CSR Primary Analysis - January 2025"
        )
        created_effort = await reporting_effort.create(db, obj_in=effort_data)
        print(f"Created reporting effort: {created_effort.database_release_label}")
        
        # Create test users
        users_data = [
            UserCreate(
                username="john_smith",
                email="john.smith@example.com",
                full_name="John Smith",
                role="EDITOR",
                department="Programming"
            ),
            UserCreate(
                username="jane_doe",
                email="jane.doe@example.com",
                full_name="Jane Doe",
                role="EDITOR",
                department="Programming"
            ),
            UserCreate(
                username="bob_wilson",
                email="bob.wilson@example.com",
                full_name="Bob Wilson",
                role="VIEWER",
                department="Biostatistics"
            ),
            UserCreate(
                username="alice_johnson",
                email="alice.johnson@example.com",
                full_name="Alice Johnson",
                role="EDITOR",
                department="Programming"
            )
        ]
        
        created_users = []
        for user_data in users_data:
            try:
                created_user = await user.create(db, obj_in=user_data)
                created_users.append(created_user)
                print(f"Created user: {created_user.username}")
            except Exception as e:
                print(f"User {user_data.username} might already exist: {e}")
                # Try to get existing user
                existing = await user.get_by_username(db, username=user_data.username)
                if existing:
                    created_users.append(existing)
        
        # Create multiple reporting effort items (TLFs and Datasets)
        items_data = [
            # TLF items
            ReportingEffortItemCreate(
                reporting_effort_id=created_effort.id,
                item_type="TLF",
                item_subtype="Table",
                item_code="14.1.1"
            ),
            ReportingEffortItemCreate(
                reporting_effort_id=created_effort.id,
                item_type="TLF",
                item_subtype="Table",
                item_code="14.2.1"
            ),
            ReportingEffortItemCreate(
                reporting_effort_id=created_effort.id,
                item_type="TLF",
                item_subtype="Figure",
                item_code="14.3.1"
            ),
            ReportingEffortItemCreate(
                reporting_effort_id=created_effort.id,
                item_type="TLF",
                item_subtype="Listing",
                item_code="16.2.1"
            ),
            # Dataset items
            ReportingEffortItemCreate(
                reporting_effort_id=created_effort.id,
                item_type="Dataset",
                item_subtype="SDTM",
                item_code="DM"
            ),
            ReportingEffortItemCreate(
                reporting_effort_id=created_effort.id,
                item_type="Dataset",
                item_subtype="SDTM",
                item_code="AE"
            ),
            ReportingEffortItemCreate(
                reporting_effort_id=created_effort.id,
                item_type="Dataset",
                item_subtype="ADaM",
                item_code="ADSL"
            ),
            ReportingEffortItemCreate(
                reporting_effort_id=created_effort.id,
                item_type="Dataset",
                item_subtype="ADaM",
                item_code="ADEFF"
            )
        ]
        
        created_items = []
        for item_data in items_data:
            created_item = await reporting_effort_item.create(db, obj_in=item_data)
            created_items.append(created_item)
            print(f"Created item: {item_data.item_type} - {item_data.item_code}")
            
            # Get the auto-created tracker
            tracker = await reporting_effort_item_tracker.get_by_item(db, reporting_effort_item_id=created_item.id)
            if tracker and len(created_users) >= 2:
                # Assign programmers randomly
                prod_user = random.choice(created_users[:2])
                qc_user = random.choice([u for u in created_users[:2] if u.id != prod_user.id])
                
                # Update tracker with assignments and random status
                statuses = ["not_started", "in_progress", "completed", "in_progress"]
                tracker_update = ReportingEffortItemTrackerUpdate(
                    production_programmer_id=prod_user.id,
                    qc_programmer_id=qc_user.id if random.random() > 0.3 else None,
                    production_status=random.choice(statuses),
                    qc_status=random.choice(["not_started", "in_progress"]) if random.random() > 0.5 else "not_started",
                    notes=f"Working on {item_data.item_code} implementation" if random.random() > 0.5 else None
                )
                
                updated_tracker = await reporting_effort_item_tracker.update(
                    db, db_obj=tracker, obj_in=tracker_update
                )
                print(f"  Updated tracker: Prod={prod_user.username}, Status={updated_tracker.production_status}")
                
                # Add some comments
                if random.random() > 0.5:
                    comment_data = TrackerCommentCreate(
                        tracker_id=tracker.id,
                        user_id=random.choice(created_users).id,
                        comment_text=f"Initial review of {item_data.item_code} completed. Looks good so far.",
                        is_resolved=random.choice([True, False])
                    )
                    created_comment = await tracker_comment.create(db, obj_in=comment_data)
                    print(f"  Added comment from user {created_comment.user_id}")
        
        await db.commit()
        print("\nTest data created successfully!")
        print(f"Study ID: {created_study.id}")
        print(f"Database Release ID: {created_db_release.id}")
        print(f"Reporting Effort ID: {created_effort.id}")
        print(f"Created {len(created_items)} tracker items")
        print(f"Created {len(created_users)} users")
        
        return created_effort.id

if __name__ == "__main__":
    effort_id = asyncio.run(create_test_data())
    print(f"\nUse Reporting Effort ID {effort_id} in the UI for testing")