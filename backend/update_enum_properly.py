#!/usr/bin/env python3
"""Update the sourcetype enum to use lowercase values."""

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def update_enum():
    engine = create_async_engine(settings.database_url)
    
    async with engine.begin() as conn:
        try:
            print("Checking current enum values...")
            
            # Check current enum values
            result = await conn.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'sourcetype')
                ORDER BY enumsortorder
            """))
            current_values = [row[0] for row in result]
            print(f"Current values: {current_values}")
            
            if current_values == ['package', 'reporting_effort', 'custom', 'bulk_upload']:
                print("✅ Enum values are already lowercase!")
                return
            
            # Check if any tables use this enum
            result = await conn.execute(text("""
                SELECT DISTINCT table_name, column_name
                FROM information_schema.columns
                WHERE udt_name = 'sourcetype'
            """))
            columns = result.fetchall()
            
            if columns:
                print(f"Tables using sourcetype enum: {columns}")
                
                # Temporarily alter columns to text
                for table_name, column_name in columns:
                    print(f"Converting {table_name}.{column_name} to TEXT...")
                    
                    # First check if there's any data
                    result = await conn.execute(text(f"""
                        SELECT COUNT(*) FROM {table_name} WHERE {column_name} IS NOT NULL
                    """))
                    count = result.scalar()
                    print(f"  {count} rows with data")
                    
                    # Convert to text
                    await conn.execute(text(f"""
                        ALTER TABLE {table_name}
                        ALTER COLUMN {column_name} TYPE TEXT
                        USING {column_name}::TEXT
                    """))
                    
                    # Update values to lowercase
                    if count > 0:
                        print(f"  Updating values to lowercase...")
                        await conn.execute(text(f"""
                            UPDATE {table_name}
                            SET {column_name} = LOWER({column_name})
                            WHERE {column_name} IS NOT NULL
                        """))
            
            # Drop the old enum
            print("Dropping old enum...")
            await conn.execute(text("DROP TYPE sourcetype"))
            
            # Create new enum with lowercase values
            print("Creating new enum with lowercase values...")
            await conn.execute(text("""
                CREATE TYPE sourcetype AS ENUM ('package', 'reporting_effort', 'custom', 'bulk_upload')
            """))
            
            # Convert columns back to enum
            if columns:
                for table_name, column_name in columns:
                    print(f"Converting {table_name}.{column_name} back to sourcetype enum...")
                    await conn.execute(text(f"""
                        ALTER TABLE {table_name}
                        ALTER COLUMN {column_name} TYPE sourcetype
                        USING {column_name}::sourcetype
                    """))
            
            # Verify the change
            result = await conn.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'sourcetype')
                ORDER BY enumsortorder
            """))
            new_values = [row[0] for row in result]
            print(f"✅ New enum values: {new_values}")
            
            print("\n✅ Database enum updated successfully!")
            print("⚠️  IMPORTANT: Restart the backend server to pick up the changes!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            raise
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(update_enum())
