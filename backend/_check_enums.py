#!/usr/bin/env python3
from sqlalchemy import create_engine, text
from app.core.config import settings

def main():
	url = settings.database_url
	url_sync = url.replace('+asyncpg', '')
	engine = create_engine(url_sync)
	with engine.connect() as conn:
		rows = conn.execute(text("SELECT enumlabel FROM pg_enum WHERE enumtypid=(SELECT oid FROM pg_type WHERE typname='sourcetype') ORDER BY enumsortorder")).fetchall()
		print('sourcetype:', [r[0] for r in rows])
		rows2 = conn.execute(text("SELECT enumlabel FROM pg_enum WHERE enumtypid=(SELECT oid FROM pg_type WHERE typname='itemtype') ORDER BY enumsortorder")).fetchall()
		print('itemtype:', [r[0] for r in rows2])

if __name__ == '__main__':
	main()

