import psycopg2

conn = psycopg2.connect('dbname=fusionlab user=postgres password=hello123')
cur = conn.cursor()

# Fix the database column - add default value and allow NULL
print("Fixing database column constraint...")
cur.execute("ALTER TABLE globals_moduleaccess ALTER COLUMN database DROP NOT NULL")
cur.execute("ALTER TABLE globals_moduleaccess ALTER COLUMN database SET DEFAULT FALSE")
conn.commit()

# Update existing NULL values
cur.execute("UPDATE globals_moduleaccess SET database = FALSE WHERE database IS NULL")
conn.commit()

print("Updated", cur.rowcount, "rows")

# Verify
cur.execute("""
    SELECT column_name, is_nullable, column_default 
    FROM information_schema.columns 
    WHERE table_name = 'globals_moduleaccess' 
    AND column_name = 'database'
""")
result = cur.fetchone()
print(f"\nColumn info: name={result[0]}, nullable={result[1]}, default={result[2]}")

cur.close()
conn.close()
print("\n✅ Fixed! database column now allows NULL and has default FALSE")
