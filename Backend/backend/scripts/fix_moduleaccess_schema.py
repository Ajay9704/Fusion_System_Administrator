import psycopg2

conn = psycopg2.connect('dbname=fusionlab user=postgres password=hello123')
cur = conn.cursor()

# Check existing columns
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'globals_moduleaccess' 
    AND column_name IN ('inventory_management', 'database')
    ORDER BY column_name
""")
cols = [row[0] for row in cur.fetchall()]
print('Existing columns:', cols)

# Add missing columns
if 'inventory_management' not in cols:
    print('Adding inventory_management...')
    cur.execute('ALTER TABLE globals_moduleaccess ADD COLUMN inventory_management BOOLEAN DEFAULT FALSE')
    conn.commit()
    print('✅ inventory_management added')

if 'database' not in cols:
    print('Adding database...')
    cur.execute('ALTER TABLE globals_moduleaccess ADD COLUMN database BOOLEAN DEFAULT FALSE')
    conn.commit()
    print('✅ database added')

# Verify
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'globals_moduleaccess' 
    AND column_name IN ('inventory_management', 'database')
    ORDER BY column_name
""")
cols = [row[0] for row in cur.fetchall()]
print('\nFinal columns:', cols)

cur.close()
conn.close()
print('\n✅ Database schema updated successfully!')
