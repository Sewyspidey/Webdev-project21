# ⚠️ IMPORTANT - QUEST VIDEO FIX

## The quest video is NOT showing because you need to RESET THE DATABASE

The video URL has been updated in app.py, but your existing database still has the old URL.

## How to Fix (Choose ONE method):

### Method 1: Delete Database (EASIEST)
```bash
cd bridgehive_final
rm bridgehive.db
# OR if you use enterprise version:
rm bridgehive_enterprise.db

# Then run the app - it will recreate the database with the new video:
python app.py
```

### Method 2: Update Database Directly (Advanced)
```bash
cd bridgehive_final
python3 << 'EOF'
from app import app, db, Quest
with app.app_context():
    quest = Quest.query.filter_by(title="Introduction to Scams").first()
    if quest:
        quest.video_url = "https://www.youtube.com/embed/cRUpM9MS3-k"
        db.session.commit()
        print("✅ Quest video updated!")
    else:
        print("❌ Quest not found")
EOF
```

### Method 3: Manually Check Database
```bash
sqlite3 bridgehive.db
SELECT title, video_url FROM quest WHERE title LIKE '%Introduction%';
-- You should see the OLD URL (dQw4w9WgXcQ)
-- After deleting and recreating, you'll see the NEW URL (cRUpM9MS3-k)
```

## After Reset:

1. The "Introduction to Scams" quest will have the correct video
2. Video will play automatically in the modal
3. 30-second timer will start
4. After 30 seconds, "Claim Points" button activates
5. Clicking it triggers confetti animation! 🎊

## What the Video URL Looks Like Now:

```python
# In app.py line 3452:
"https://www.youtube.com/embed/cRUpM9MS3-k"
```

This is the correct EMBED format for YouTube videos in iframes.

## ⚠️ Why You Must Reset Database

When you first ran `python app.py`, Flask created the database with the SEED DATA at that time.

The seed data had the placeholder video URL:
- Old: `https://www.youtube.com/embed/dQw4w9WgXcQ` (Rick Roll)
- New: `https://www.youtube.com/embed/cRUpM9MS3-k` (Your real video)

Changing app.py does NOT automatically update existing database records.

You must either:
1. Delete the database file (it will recreate with new data), OR
2. Manually update the database record

**I recommend Method 1 (delete and recreate) - it's the simplest!**

## Your Sample Data Will Be Lost

When you delete the database:
- ❌ All test user accounts will be deleted
- ❌ All sample course enrollments will be deleted
- ❌ All test points/rewards will be deleted
- ✅ You'll get fresh sample data with the correct video

This is fine for development! Just recreate your test account.

## Quick Commands:

```bash
# Stop Flask if running (Ctrl+C)

# Delete database
rm bridgehive.db

# Restart Flask
python app.py

# That's it! Database recreated with correct video URL
```

## Verify It Worked:

1. Go to Rewards > Quests tab
2. Click "Introduction to Scams"
3. Modal opens with video player
4. Video should start playing automatically
5. See 30-second countdown timer
6. After 30s, click "Claim Points"
7. See confetti! 🎊

---

**Bottom line: DELETE THE DATABASE FILE, then restart Flask. That's it!**
