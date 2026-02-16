"""
Migration script to add user_id to module_completion table.
Run this ONCE to update the database schema for user-specific progress tracking.
"""

import sqlite3
import os

def migrate_module_completion():
    """Add user_id column to module_completion table and update UNIQUE constraint."""
    db_path = os.path.join(os.path.dirname(__file__), 'bridgehive_enterprise.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("The database will be created with the new schema when the app runs.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if user_id column already exists
        cursor.execute("PRAGMA table_info(module_completion)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'user_id' in columns:
            print("✅ Migration already applied - user_id column exists.")
            conn.close()
            return
        
        print("🔄 Starting migration...")
        
        # Step 1: Create new table with user_id
        cursor.execute('''
            CREATE TABLE module_completion_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                module_id INTEGER NOT NULL,
                user_id INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(course_id, module_id, user_id),
                FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
                FOREIGN KEY (module_id) REFERENCES modules (id) ON DELETE CASCADE
            )
        ''')
        print("✓ Created new table structure")
        
        # Step 2: Copy data from old table (assign user_id = 0 for existing records)
        cursor.execute('''
            INSERT INTO module_completion_new 
                (id, course_id, module_id, user_id, completed, completed_at, created_at)
            SELECT 
                id, course_id, module_id, 0, completed, completed_at, created_at
            FROM module_completion
        ''')
        print("✓ Copied existing data")
        
        # Step 3: Drop old table
        cursor.execute('DROP TABLE module_completion')
        print("✓ Removed old table")
        
        # Step 4: Rename new table
        cursor.execute('ALTER TABLE module_completion_new RENAME TO module_completion')
        print("✓ Renamed table")
        
        # Commit changes
        conn.commit()
        print("✅ Migration completed successfully!")
        print("\n⚠️  Note: All existing progress has been assigned to user_id = 0 (anonymous).")
        print("   Users will need to complete modules again to track their individual progress.")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        print("Please check the error and try again.")
    
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Module Completion Migration Script")
    print("=" * 60)
    print("\nThis script will add user_id to the module_completion table.")
    print("This enables user-specific progress tracking for courses.\n")
    
    response = input("Continue with migration? (yes/no): ").strip().lower()
    if response in ['yes', 'y']:
        migrate_module_completion()
    else:
        print("Migration cancelled.")
