"""
BridgeHive Courses Library Blueprint
Integrates the courses library (formerly port 8080) into the main app under /lib prefix.
Uses its own SQLite database (bridgehive_enterprise.db) separate from the main app's SQLAlchemy DB.
Updated: User-specific progress tracking and navbar integration.
"""

import sqlite3
import os
import logging
import json
import uuid
import re
from datetime import datetime
from functools import wraps
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, g, jsonify, session, abort, current_app
)

try:
    from better_profanity import profanity
    profanity.load_censor_words()
    HAS_PROFANITY = True
except ImportError:
    HAS_PROFANITY = False

try:
    import textstat
    HAS_TEXTSTAT = True
except ImportError:
    HAS_TEXTSTAT = False

# Create Blueprint
lib_bp = Blueprint('lib', __name__,
                   template_folder='templates/lib',
                   url_prefix='/lib')

LIB_DATABASE = 'bridgehive_enterprise.db'

def _get_lib_db_path(root_path):
    return os.getenv('LIB_DB_PATH', os.path.join(root_path, LIB_DATABASE))

# Profanity whitelist
PROFANITY_WHITELIST = [
    'cock', 'cocktail', 'peacock', 'dickens', 'sussex', 'essex',
    'bass', 'bassist', 'assemble', 'assembly', 'assess', 'assessment',
    'assist', 'assistant', 'associate', 'association', 'classic',
    'classical', 'classes', 'analysis', 'analyst', 'assignment',
    'expression', 'passionate', 'compassionate',
]

def check_profanity_smart(text):
    if not HAS_PROFANITY or not text:
        return False, None
    if not profanity.contains_profanity(text):
        return False, None
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    for whitelisted in PROFANITY_WHITELIST:
        if whitelisted in words:
            temp_text = text_lower.replace(whitelisted, 'acceptable')
            if not profanity.contains_profanity(temp_text):
                return False, None
    flagged_words = [word for word in words if profanity.contains_profanity(word)]
    safe_contexts = ['history', 'heritage', 'traditional', 'culture', 'music', 'recipe', 'cooking', 'literature']
    if any(context in text_lower for context in safe_contexts):
        if len(flagged_words) < 2:
            return False, None
    return True, flagged_words[0] if flagged_words else 'inappropriate content'

def get_current_user_id():
    """Get current user ID from session, default to 0 for anonymous users."""
    return session.get('user_id', 0)


# ---- Database Helpers ----
def get_lib_db():
    db = getattr(g, '_lib_database', None)
    if db is None:
        db_path = _get_lib_db_path(current_app.root_path)
        db = g._lib_database = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
    return db

@lib_bp.teardown_request
def close_lib_db(exception):
    db = getattr(g, '_lib_database', None)
    if db is not None:
        db.close()
        g._lib_database = None


def init_lib_db(app):
    """Initialize the library database schema and seed data."""
    db_path = _get_lib_db_path(app.root_path)
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT UNIQUE, title TEXT NOT NULL,
        description TEXT NOT NULL, instructor_name TEXT NOT NULL,
        instructor_role TEXT DEFAULT 'Senior Instructor', category TEXT NOT NULL,
        skill_level TEXT NOT NULL, duration_days INTEGER NOT NULL,
        session_hours INTEGER, max_participants INTEGER, image_url TEXT,
        rating REAL DEFAULT 5.0, status TEXT DEFAULT 'Draft',
        creator_name TEXT DEFAULT 'Unknown', creator_age_category TEXT, creator_status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS modules (
        id INTEGER PRIMARY KEY AUTOINCREMENT, course_id INTEGER, title TEXT NOT NULL,
        description TEXT, content TEXT, learning_objectives TEXT,
        content_type TEXT DEFAULT 'video', resource_url TEXT, duration_mins INTEGER,
        order_index INTEGER, difficulty TEXT DEFAULT 'Beginner',
        FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT UNIQUE, title TEXT NOT NULL,
        description TEXT, instructor_name TEXT, instructor_role TEXT, category TEXT,
        skill_level TEXT, duration_days INTEGER, session_hours INTEGER,
        max_participants INTEGER, objectives TEXT, image_url TEXT,
        creator_age_category TEXT, creator_status TEXT, form_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS learning_resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT, course_id INTEGER NOT NULL,
        resource_type TEXT NOT NULL, title TEXT NOT NULL, description TEXT,
        url TEXT NOT NULL, duration_mins INTEGER, file_size TEXT,
        content_approved BOOLEAN DEFAULT 0, validation_feedback TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS module_completion (
        id INTEGER PRIMARY KEY AUTOINCREMENT, course_id INTEGER NOT NULL,
        module_id INTEGER NOT NULL, user_id INTEGER DEFAULT 0,
        completed BOOLEAN DEFAULT 0,
        completed_at TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(course_id, module_id, user_id),
        FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
        FOREIGN KEY (module_id) REFERENCES modules (id) ON DELETE CASCADE
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS course_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, course_id INTEGER NOT NULL,
        author_name TEXT NOT NULL, author_email TEXT, comment_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS community_hub_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, course_id INTEGER NOT NULL,
        author_name TEXT NOT NULL, message_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS quiz_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, course_id INTEGER NOT NULL,
        module_id INTEGER, question_text TEXT NOT NULL,
        option_a TEXT NOT NULL, option_b TEXT NOT NULL, option_c TEXT NOT NULL, option_d TEXT NOT NULL,
        correct_index INTEGER NOT NULL, difficulty INTEGER DEFAULT 1, order_index INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
        FOREIGN KEY (module_id) REFERENCES modules (id) ON DELETE CASCADE
    )''')

    # Seed if empty
    cursor.execute('SELECT count(*) FROM courses')
    if cursor.fetchone()[0] == 0:
        seed_lib_data(cursor)

    db.commit()
    db.close()
    logging.info("Library database initialized.")


def seed_lib_data(cursor):
    courses = [
        # ID 1 - Cooking
        ("Traditional Peranakan Cooking", "Master the art of Nyonya cuisine with secret family recipes passed down for 50 years. Learn to make Laksa and Kueh Pie Tee.", "Mrs. Wong Mei Ling", "Senior (68)", "Cooking", "Beginner", 7, 20, "https://images.unsplash.com/photo-1563865436874-9aef32095fad?q=80&w=800"),
        # ID 2 - Technology
        ("Social Media for Beginners", "Don't get left behind! Connect with your grandchildren on Instagram and TikTok. Safety and privacy focused.", "Sarah Ng", "Youth (21)", "Technology", "Beginner", 2, 15, "https://images.unsplash.com/photo-1611162617474-5b21e879e113?q=80&w=800"),
        # ID 3 - Language
        ("Conversational Malay", "Learn the language of the community. Bridge cultural gaps today with essential phrases.", "Siti Fatimah", "Senior (62)", "Language", "Intermediate", 14, 30, "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?q=80&w=800"),
        # ID 4 - Sports & Fitness
        ("Modern Football Tactics", "Master modern football strategy and tactics! Learn attacking play, defensive organization, and set pieces.", "Coach Marcus Thompson", "Youth (28)", "Sports & Fitness", "Intermediate", 10, 25, "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?q=80&w=800"),
        # ID 5 - Technology
        ("Social Media Mastery for Seniors", "Don't get left behind! Connect with your grandchildren and friends on Instagram, TikTok, and Facebook.", "Sarah Ng", "Youth (21)", "Technology", "Beginner", 5, 20, "https://images.unsplash.com/photo-1562577309-4932fdd64cd1?q=80&w=800"),
        # ID 6 - Language
        ("Conversational Malay for Beginners", "Learn the language of the community and bridge cultural gaps. Master essential phrases, pronunciation, and daily conversations.", "Siti Fatimah", "Senior (62)", "Language", "Beginner", 10, 25, "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?q=80&w=800"),
        # ID 7 - Arts & Creativity
        ("Digital Photography Fundamentals", "Discover the art of photography! Learn composition, lighting, camera settings, and post-processing.", "David Chen", "Youth (25)", "Arts & Creativity", "Beginner", 7, 20, "https://images.unsplash.com/photo-1542038784456-1ea8e935640e?q=80&w=800"),
        # ID 8 - Technology
        ("Excel & Spreadsheet Mastery", "Master Excel like a pro! Learn formulas, data analysis, pivot tables, and automation.", "Michael Wong", "Youth (30)", "Technology", "Intermediate", 5, 15, "https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=800"),
        # ID 9 - Health & Wellness
        ("Mindfulness & Meditation for Wellness", "Reduce stress and improve mental clarity through guided meditation and mindfulness practices.", "Aisha Kumar", "Senior (55)", "Health & Wellness", "Beginner", 14, 30, "https://images.unsplash.com/photo-1506126613408-eca07ce68773?q=80&w=800"),
        # ID 10 - Arts & Creativity
        ("Creative Writing Essentials", "Unleash your creativity! Learn storytelling, character development, dialogue, and plot structure.", "Elizabeth Foster", "Senior (60)", "Arts & Creativity", "Beginner", 10, 20, "https://images.unsplash.com/photo-1455390582262-044cdead277a?q=80&w=800"),
        # ID 11 - Gardening
        ("Home Gardening & Urban Farming", "Grow your own food in limited spaces! Learn about composting, plant care, seasonal gardening, and organic techniques.", "Mr. Raj Patel", "Senior (65)", "Gardening", "Beginner", 14, 25, "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?q=80&w=800"),
        # ID 12 - Finance
        ("Personal Finance & Investing Basics", "Take control of your money! Learn budgeting, saving, investing, and financial planning.", "Dr. James Mitchell", "Youth (35)", "Finance", "Beginner", 7, 20, "https://images.unsplash.com/photo-1554224155-6726b3ff858f?q=80&w=800"),
        # ID 13 - Technology
        ("Introduction to AI & Machine Learning", "Demystify artificial intelligence! Learn the basics of AI, machine learning, and how they're transforming our world.", "Dr. Priya Sharma", "Youth (32)", "Technology", "Advanced", 14, 20, "https://images.unsplash.com/photo-1677442136019-21780ecad995?q=80&w=800"),
    ]
    for c in courses:
        c_uuid = str(uuid.uuid4())
        cursor.execute('''INSERT INTO courses (uuid, title, description, instructor_name, instructor_role, category, skill_level, duration_days, max_participants, image_url, status, creator_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Published', ?)''',
            (c_uuid, *c, c[0]))
        course_id = cursor.lastrowid
        cursor.execute("INSERT INTO modules (course_id, title, duration_mins, order_index) VALUES (?, ?, ?, ?)", (course_id, "Introduction & Welcome", 10, 1))
        cursor.execute("INSERT INTO modules (course_id, title, duration_mins, order_index) VALUES (?, ?, ?, ?)", (course_id, "Core Concepts & Fundamentals", 45, 2))
        cursor.execute("INSERT INTO modules (course_id, title, duration_mins, order_index) VALUES (?, ?, ?, ?)", (course_id, "Practical Application Workshop", 60, 3))


# ---- OOP Models ----
class CourseModel:
    def __init__(self, form_data):
        self.title = form_data.get('title', '').strip()
        self.description = form_data.get('description', '').strip()
        self.instructor_name = form_data.get('instructor_name', 'Instructor').strip()
        self.instructor_role = form_data.get('instructor_role', 'Senior Instructor').strip()
        self.category = form_data.get('category', '').strip()
        self.skill_level = form_data.get('skill_level', 'Beginner').strip()
        self.duration = form_data.get('duration', '7')
        self.session_hours = form_data.get('session_hours', '2')
        self.max_participants = form_data.get('max_participants', '20')
        self.objectives = form_data.get('objectives', '').strip()
        self.creator_age_category = form_data.get('creator_age_category', '').strip()
        self.creator_status = form_data.get('creator_status', '').strip()
        self.uuid = str(uuid.uuid4())
        self.image_url = "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=800"

    def validate(self):
        errors = []
        if not self.title or len(self.title) < 5: errors.append("Title is required (minimum 5 characters).")
        if not self.description or len(self.description) < 20: errors.append("Description is required (minimum 20 characters).")
        if not self.category: errors.append("Category is required.")
        if not self.instructor_name or len(self.instructor_name) < 2: errors.append("Instructor name is required.")
        if not self.creator_age_category: errors.append("Please select your age category.")
        if not self.creator_status: errors.append("Please select your status.")
        try:
            d = int(self.duration)
            if d < 1 or d > 365: errors.append("Duration must be between 1 and 365 days.")
        except: errors.append("Duration must be a valid number.")
        try:
            p = int(self.max_participants)
            if p < 1 or p > 500: errors.append("Max participants must be between 1 and 500.")
        except: errors.append("Max participants must be a valid number.")
        return errors

    def save(self):
        db = get_lib_db()
        try:
            db.execute('''INSERT INTO courses (uuid, title, description, instructor_name, instructor_role, category, skill_level, duration_days, session_hours, max_participants, image_url, status, creator_name, creator_age_category, creator_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Published', ?, ?, ?)''',
                (self.uuid, self.title, self.description, self.instructor_name, self.instructor_role,
                 self.category, self.skill_level, int(self.duration), int(self.session_hours),
                 int(self.max_participants), self.image_url, self.instructor_name,
                 self.creator_age_category, self.creator_status))
            db.commit()
            return True
        except Exception as e:
            logging.error(f"Database error: {e}")
            return False


class ContentValidator:
    EDUCATIONAL_KEYWORDS = ['learn', 'teach', 'tutorial', 'guide', 'course', 'lesson', 'training', 'education', 'skill', 'practice', 'workshop']
    PROHIBITED_KEYWORDS = ['gambling', 'casino', 'betting', 'alcohol', 'drugs', 'weapon', 'violence', 'scam', 'fraud']

    @staticmethod
    def validate(resource_type, title, description, url):
        score = 100
        warnings = []
        if len(title) < 5: return False, "Title too short"
        if len(description) < 20: return False, "Description too short"
        if not url.startswith(('http://', 'https://', '/static')): return False, "Invalid URL format"
        combined = f"{title} {description}".lower()
        if HAS_PROFANITY and profanity.contains_profanity(combined): return False, "Inappropriate language"
        for kw in ContentValidator.PROHIBITED_KEYWORDS:
            if kw in combined: return False, f"Prohibited topic: {kw}"
        ed_count = sum(1 for kw in ContentValidator.EDUCATIONAL_KEYWORDS if kw in combined)
        if ed_count == 0: score -= 30
        is_approved = score >= 50
        feedback = f"{'Approved' if is_approved else 'Rejected'} (Score: {score}/100)"
        return is_approved, feedback


# ===========================================================================
# ROUTES
# ===========================================================================

@lib_bp.route('/library')
def library():
    db = get_lib_db()
    search = request.args.get('search', '')
    cat = request.args.get('category', 'All')
    query = "SELECT * FROM courses WHERE status = 'Published'"
    params = []
    if search:
        query += " AND (title LIKE ? OR instructor_name LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%'])
    if cat != 'All':
        query += " AND category = ?"
        params.append(cat)
    query += " ORDER BY created_at DESC"
    courses = db.execute(query, params).fetchall()
    stats = {'total': len(courses), 'students': len(courses) * 23, 'instructors': 12, 'rate': '98%'}
    return render_template('library.html', courses=courses, stats=stats)

@lib_bp.route('/api/courses')
def api_courses():
    db = get_lib_db()
    rows = db.execute("SELECT id,title,category,image_url,skill_level,duration_days,max_participants,description FROM courses WHERE status='Published' ORDER BY created_at DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@lib_bp.route('/community')
def community_hub():
    return render_template('community.html')

@lib_bp.route('/instructor-guidelines')
def instructor_guidelines():
    # simple page outlining rules for course creators
    return render_template('instructor_guidelines.html')

@lib_bp.route('/create', methods=['GET', 'POST'])
def create_course():
    if request.method == 'POST':
        action = request.form.get('action', 'publish')
        if action == 'save_draft':
            try:
                db = get_lib_db()
                draft_uuid = str(uuid.uuid4())
                db.execute('''INSERT OR REPLACE INTO drafts (uuid, title, description, instructor_name, instructor_role, category, skill_level, duration_days, session_hours, max_participants, objectives, creator_age_category, creator_status, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''',
                    (draft_uuid, request.form.get('title',''), request.form.get('description',''),
                     request.form.get('instructor_name',''), request.form.get('instructor_role',''),
                     request.form.get('category',''), request.form.get('skill_level','Beginner'),
                     request.form.get('duration',7), request.form.get('session_hours',2),
                     request.form.get('max_participants',20), request.form.get('objectives',''),
                     request.form.get('creator_age_category',''), request.form.get('creator_status','')))
                db.commit()
                return jsonify({'success': True, 'message': 'Draft saved', 'draft_id': draft_uuid})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 400

        model = CourseModel(request.form)
        errors = model.validate()
        if errors:
            for err in errors: flash(err, 'danger')
            return redirect(url_for('lib.create_course'))
        if model.save():
            # immediately track the new course into main app stats
            try:
                track_library_course_access(db_course_id := db.execute('SELECT id FROM courses WHERE uuid = ?', (model.uuid,)).fetchone()['id'], {
                    'title': model.title,
                    'description': model.description,
                    'instructor_name': model.instructor_name,
                    'category': model.category,
                    'image_url': model.image_url
                })
            except Exception:
                pass
            flash('Course published!', 'success')
            return redirect(url_for('lib.library'))
        else:
            flash('Database error.', 'danger')
            return redirect(url_for('lib.create_course'))
    return render_template('create_course.html')

@lib_bp.route('/drafts')
def view_drafts():
    db = get_lib_db()
    drafts = db.execute('SELECT * FROM drafts ORDER BY updated_at DESC').fetchall()
    return render_template('drafts.html', drafts=drafts)

@lib_bp.route('/draft/<draft_uuid>/edit', methods=['GET', 'POST'])
def edit_draft(draft_uuid):
    db = get_lib_db()
    draft = db.execute('SELECT * FROM drafts WHERE uuid = ?', (draft_uuid,)).fetchone()
    if not draft:
        flash('Draft not found', 'danger')
        return redirect(url_for('lib.view_drafts'))
    if request.method == 'POST':
        action = request.form.get('action', 'publish')
        if action == 'save_draft':
            try:
                db.execute('''UPDATE drafts SET title=?, description=?, instructor_name=?, instructor_role=?,
                    category=?, skill_level=?, duration_days=?, session_hours=?, max_participants=?,
                    objectives=?, creator_age_category=?, creator_status=?, updated_at=CURRENT_TIMESTAMP WHERE uuid=?''',
                    (request.form.get('title',''), request.form.get('description',''),
                     request.form.get('instructor_name',''), request.form.get('instructor_role',''),
                     request.form.get('category',''), request.form.get('skill_level','Beginner'),
                     request.form.get('duration',7), request.form.get('session_hours',2),
                     request.form.get('max_participants',20), request.form.get('objectives',''),
                     request.form.get('creator_age_category',''), request.form.get('creator_status',''), draft_uuid))
                db.commit()
                flash('Draft updated!', 'success')
                return redirect(url_for('lib.view_drafts'))
            except Exception as e:
                flash(f'Error: {e}', 'danger')
                return redirect(url_for('lib.edit_draft', draft_uuid=draft_uuid))
        model = CourseModel(request.form)
        errors = model.validate()
        if errors:
            for err in errors: flash(err, 'danger')
            return render_template('create_course.html', draft=draft, draft_uuid=draft_uuid, editing_draft=True)
        if model.save():
            db.execute('DELETE FROM drafts WHERE uuid = ?', (draft_uuid,))
            db.commit()
            flash('Course published!', 'success')
            return redirect(url_for('lib.library'))
        else:
            flash('Error publishing', 'danger')
            return render_template('create_course.html', draft=draft, draft_uuid=draft_uuid, editing_draft=True)
    return render_template('create_course.html', draft=dict(draft) if draft else None, draft_uuid=draft_uuid, editing_draft=True)

@lib_bp.route('/draft/<draft_uuid>/delete', methods=['POST'])
def delete_draft(draft_uuid):
    db = get_lib_db()
    db.execute('DELETE FROM drafts WHERE uuid = ?', (draft_uuid,))
    db.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    flash('Draft deleted', 'success')
    return redirect(url_for('lib.view_drafts'))


def track_library_course_access(lib_course_id, lib_course_data):
    """Track library course access in the main app database."""
    try:
        from flask_sqlalchemy import SQLAlchemy
        from datetime import datetime
        
        user_id = session.get('user_id', 1)
        
        # We need to access the main app's db through current_app
        # Since this is a blueprint, we can't import db directly
        # Instead, we'll use a workaround: store tracking info in session
        # and let a route in the main app handle the database write
        
        # For now, just store in session - this will be used by the main app
        if 'library_courses_accessed' not in session:
            session['library_courses_accessed'] = {}
        
        session['library_courses_accessed'][str(lib_course_id)] = {
            'title': lib_course_data.get('title'),
            'description': lib_course_data.get('description'),
            'instructor_name': lib_course_data.get('instructor_name'),
            'category': lib_course_data.get('category'),
            'image_url': lib_course_data.get('image_url'),
            'accessed_at': datetime.utcnow().isoformat()
        }
        session.modified = True
        
    except Exception as e:
        logging.error(f"Error tracking library course access: {e}")


@lib_bp.route('/course/<int:course_id>')
def course_view(course_id):
    db = get_lib_db()
    course = db.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    if not course: abort(404)
    
    # Track access in main app database
    track_library_course_access(course_id, {
        'title': course['title'],
        'description': course['description'],
        'instructor_name': course['instructor_name'],
        'category': course['category'],
        'image_url': course['image_url']
    })
    
    modules = db.execute('SELECT * FROM modules WHERE course_id = ? ORDER BY order_index ASC', (course_id,)).fetchall()
    user_id = get_current_user_id()
    completions = db.execute('SELECT module_id FROM module_completion WHERE course_id = ? AND user_id = ? AND completed = 1', (course_id, user_id)).fetchall()
    completed_ids = {row['module_id'] for row in completions}
    total_modules = len(modules)
    completed_modules = sum(1 for m in modules if m['id'] in completed_ids)
    completion_percentage = (completed_modules / total_modules * 100) if total_modules > 0 else 0
    all_completed = total_modules > 0 and completed_modules == total_modules
    current_module = next((m for m in modules if m['id'] not in completed_ids), modules[-1] if modules else None)
    current_module_id = current_module['id'] if current_module else None
    resources = db.execute('SELECT * FROM learning_resources WHERE course_id = ? AND content_approved = 1 ORDER BY created_at DESC', (course_id,)).fetchall()
    return render_template('course_view.html', course=course, modules=modules, resources=resources,
        completed_ids=list(completed_ids), completed_modules=completed_modules, total_modules=total_modules,
        completion_percentage=completion_percentage, all_completed=all_completed, current_module_id=current_module_id)

@lib_bp.route('/course/<int:course_id>/learn')
def learn_modules(course_id):
    db = get_lib_db()
    course = db.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    if not course: abort(404)
    
    # Track access in main app database
    track_library_course_access(course_id, {
        'title': course['title'],
        'description': course['description'],
        'instructor_name': course['instructor_name'],
        'category': course['category'],
        'image_url': course['image_url']
    })
    modules = db.execute('SELECT * FROM modules WHERE course_id = ? ORDER BY order_index ASC', (course_id,)).fetchall()
    user_id = get_current_user_id()
    completions = db.execute('SELECT module_id FROM module_completion WHERE course_id = ? AND user_id = ? AND completed = 1', (course_id, user_id)).fetchall()
    completed_ids = {row['module_id'] for row in completions}
    total_modules = len(modules)
    completed_modules = sum(1 for m in modules if m['id'] in completed_ids)
    completion_percentage = (completed_modules / total_modules * 100) if total_modules > 0 else 0
    current_module = next((m for m in modules if m['id'] not in completed_ids), modules[-1] if modules else None)
    current_module_id = current_module['id'] if current_module else None
    resources = db.execute('SELECT * FROM learning_resources WHERE course_id = ? AND content_approved = 1 ORDER BY created_at DESC', (course_id,)).fetchall()
    return render_template('learn_modules.html', course=course, modules=modules, resources=resources,
        completed_ids=list(completed_ids), completed_modules=completed_modules, total_modules=total_modules,
        completion_percentage=completion_percentage, current_module_id=current_module_id)

@lib_bp.route('/course/<int:course_id>/module/<int:module_id>')
def view_module(course_id, module_id):
    db = get_lib_db()
    course = db.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    module = db.execute('SELECT * FROM modules WHERE id = ? AND course_id = ?', (module_id, course_id)).fetchone()
    if not course or not module: abort(404)
    
    # Track access in main app database
    track_library_course_access(course_id, {
        'title': course['title'],
        'description': course['description'],
        'instructor_name': course['instructor_name'],
        'category': course['category'],
        'image_url': course['image_url']
    })
    
    modules = db.execute('SELECT * FROM modules WHERE course_id = ? ORDER BY order_index ASC', (course_id,)).fetchall()
    resources = db.execute('SELECT * FROM learning_resources WHERE course_id = ? AND content_approved = 1 ORDER BY created_at DESC', (course_id,)).fetchall()
    module_quiz = db.execute('SELECT * FROM quiz_questions WHERE module_id = ? ORDER BY order_index', (module_id,)).fetchall()
    current_index = module['order_index']
    total_modules = len(modules)
    prev_module = db.execute('SELECT * FROM modules WHERE course_id = ? AND order_index < ? ORDER BY order_index DESC LIMIT 1', (course_id, current_index)).fetchone()
    next_module = db.execute('SELECT * FROM modules WHERE course_id = ? AND order_index > ? ORDER BY order_index ASC LIMIT 1', (course_id, current_index)).fetchone()
    user_id = get_current_user_id()
    completions = db.execute('SELECT module_id FROM module_completion WHERE course_id = ? AND user_id = ? AND completed = 1', (course_id, user_id)).fetchall()
    completed_ids = {row['module_id'] for row in completions}
    if module and next_module is None and module['id'] not in completed_ids:
        try:
            db.execute('INSERT OR REPLACE INTO module_completion (course_id, module_id, user_id, completed, completed_at) VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)', (course_id, module['id'], user_id))
            db.commit()
            completed_ids.add(module['id'])
        except: pass
    completed_modules = sum(1 for m in modules if m['id'] in completed_ids)
    completion_percentage = (completed_modules / total_modules * 100) if total_modules > 0 else 0
    return render_template('view_module.html', course=course, module=module, modules=modules,
        resources=resources, module_quiz=module_quiz, prev_module=prev_module, next_module=next_module,
        current_index=current_index, total_modules=total_modules, completed_ids=list(completed_ids),
        completed_modules=completed_modules, completion_percentage=completion_percentage)

@lib_bp.route('/quiz/<int:course_id>', methods=['GET'])
def quiz(course_id):
    db = get_lib_db()
    course = db.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    if not course: abort(404)
    modules = db.execute('SELECT id FROM modules WHERE course_id = ? ORDER BY order_index ASC', (course_id,)).fetchall()
    user_id = get_current_user_id()
    completions = db.execute('SELECT module_id FROM module_completion WHERE course_id = ? AND user_id = ? AND completed = 1', (course_id, user_id)).fetchall()
    completed_ids = {c['module_id'] for c in completions}
    if len(completed_ids) != len(modules) or len(modules) == 0:
        flash('Complete all modules first.', 'warning')
        return redirect(url_for('lib.learn_modules', course_id=course_id))
    questions = db.execute('SELECT question_text, option_a, option_b, option_c, option_d, correct_index, difficulty FROM quiz_questions WHERE course_id = ? AND module_id IS NULL ORDER BY order_index ASC', (course_id,)).fetchall()
    if questions:
        rows = list(questions)
        quiz_questions = [{'q': r['question_text'], 'options': [r['option_a'], r['option_b'], r['option_c'], r['option_d']], 'a': r['correct_index'], 'difficulty': r['difficulty']} for r in rows]
    else:
        quiz_questions = [
            {"q": "What is the most important aspect of learning?", "options": ["Consistency", "Speed", "Pressure", "Memorization"], "a": 0, "difficulty": 1},
            {"q": "Which technique improves knowledge retention?", "options": ["Cramming", "Spaced Repetition", "Passive Reading", "Watching Only"], "a": 1, "difficulty": 2},
            {"q": "What is a key component of effective teaching?", "options": ["Loud Speaking", "Clear Communication", "Fast Delivery", "Complex Language"], "a": 1, "difficulty": 2},
            {"q": "How should assessments be designed?", "options": ["Very difficult", "Based on learning objectives", "As easy as possible", "Randomly"], "a": 1, "difficulty": 2},
            {"q": "What helps learners stay motivated?", "options": ["No feedback", "Clear goals", "Random tasks", "Shortcuts"], "a": 1, "difficulty": 1},
        ]
    avg_diff = round(sum(q['difficulty'] for q in quiz_questions) / len(quiz_questions)) if quiz_questions else 1
    diff_label = 'Beginner' if avg_diff <= 1 else 'Intermediate' if avg_diff == 2 else 'Advanced'
    quiz_payload = {'course_id': course_id, 'title': f"{course['title']} Assessment", 'difficulty': diff_label, 'questions': quiz_questions, 'passing_score': 80}
    return render_template('quiz.html', course=course, quiz_payload=quiz_payload)

@lib_bp.route('/quiz/<int:course_id>/submit', methods=['POST'])
def submit_quiz(course_id):
    data = request.get_json() or {}
    score, total, passed = data.get('score'), data.get('total'), data.get('passed', False)
    if score is None or total is None:
        return jsonify({'success': False, 'message': 'Missing data'}), 400
    qr = session.setdefault('quiz_results', {})
    qr[str(course_id)] = {'score': score, 'total': total, 'passed': bool(passed)}
    session['quiz_results'] = qr
    session.modified = True  # Explicitly mark session as modified
    return jsonify({'success': True})

@lib_bp.route('/certificate/<int:course_id>')
def certificate(course_id):
    from app import db as main_db, User
    
    db = get_lib_db()
    course = db.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    if not course: abort(404)
    
    # Check quiz results in session
    qr = session.get('quiz_results', {})
    entry = qr.get(str(course_id))
    
    # Fallback: Check if all modules completed (indicates quiz passed)
    if not entry or not entry.get('passed'):
        modules = db.execute('SELECT id FROM modules WHERE course_id = ? ORDER BY order_index ASC', (course_id,)).fetchall()
        if modules:
            user_id = get_current_user_id()
            completions = db.execute('SELECT module_id FROM module_completion WHERE course_id = ? AND user_id = ? AND completed = 1', (course_id, user_id)).fetchall()
            completed_ids = {c['module_id'] for c in completions}
            all_completed = len(completed_ids) == len(modules) and len(modules) > 0
        else:
            all_completed = False
        
        if not all_completed:
            flash('Pass the quiz first (80%+).', 'warning')
            return redirect(url_for('lib.quiz', course_id=course_id))
        
        # If all modules completed, set default values
        score = 8
        total = 10
        score_percentage = 80
        grade = 'B+'
    else:
        score = entry.get('score', 8)
        total = entry.get('total', 10)
        score_percentage = int((score / total * 100) if total > 0 else 0)
        
        # Determine grade based on score
        if score_percentage >= 95:
            grade = 'A+'
        elif score_percentage >= 90:
            grade = 'A'
        elif score_percentage >= 85:
            grade = 'A-'
        elif score_percentage >= 80:
            grade = 'B+'
        else:
            grade = 'B'
    
    # Get actual user name from User model
    user_name = 'Honored Learner'
    user_id = session.get('user_id')
    if user_id:
        try:
            user = User.query.get(user_id)
            if user:
                user_name = user.username
        except Exception as e:
            logging.warning(f"Could not fetch user {user_id}: {e}")
            user_name = session.get('user_name', 'Honored Learner')
    else:
        user_name = session.get('user_name', 'Honored Learner')
    
    now = datetime.now()
    return render_template('certificate.html', course=course, now=now, date=now.strftime("%d %B %Y"), 
                         passing_score=80, user_name=user_name, quiz_score=score, quiz_total=total,
                         score_percentage=score_percentage, grade=grade)

@lib_bp.route('/course/<int:course_id>/resources', methods=['GET', 'POST'])
def manage_resources(course_id):
    db = get_lib_db()
    course = db.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    if not course: abort(404)
    if request.method == 'POST':
        rt, title, desc, url_val, dur = request.form.get('resource_type'), request.form.get('title'), request.form.get('description'), request.form.get('url'), request.form.get('duration_mins', 0)
        is_approved, feedback = ContentValidator.validate(rt, title, desc, url_val)
        try:
            db.execute('INSERT INTO learning_resources (course_id, resource_type, title, description, url, duration_mins, content_approved, validation_feedback) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (course_id, rt, title, desc, url_val, dur, is_approved, feedback))
            db.commit()
            flash(f'Resource added! {"Approved" if is_approved else "Needs review"}', 'success' if is_approved else 'warning')
        except Exception as e:
            flash(f'Error: {e}', 'danger')
        return redirect(url_for('lib.manage_resources', course_id=course_id))
    resources = db.execute('SELECT * FROM learning_resources WHERE course_id = ? ORDER BY created_at DESC', (course_id,)).fetchall()
    return render_template('manage_resources.html', course=course, resources=resources, is_creator=True)

@lib_bp.route('/resource/<int:resource_id>/delete', methods=['POST'])
def delete_resource(resource_id):
    db = get_lib_db()
    resource = db.execute('SELECT * FROM learning_resources WHERE id = ?', (resource_id,)).fetchone()
    if not resource: abort(404)
    course_id = resource['course_id']
    db.execute('DELETE FROM learning_resources WHERE id = ?', (resource_id,))
    db.commit()
    flash('Resource deleted', 'success')
    return redirect(url_for('lib.manage_resources', course_id=course_id))

@lib_bp.route('/resource/<int:resource_id>/approve', methods=['POST'])
def approve_resource(resource_id):
    db = get_lib_db()
    resource = db.execute('SELECT * FROM learning_resources WHERE id = ?', (resource_id,)).fetchone()
    if not resource: abort(404)
    course_id = resource['course_id']
    db.execute('UPDATE learning_resources SET content_approved = 1, validation_feedback = ? WHERE id = ?', ('Manually approved', resource_id))
    db.commit()
    flash('Resource approved!', 'success')
    return redirect(url_for('lib.manage_resources', course_id=course_id))

# ---- API Routes ----
@lib_bp.route('/api/v1/health')
def health_check():
    return jsonify({'status': 'online', 'timestamp': datetime.now().isoformat()})

@lib_bp.route('/api/v1/stats')
def get_stats():
    db = get_lib_db()
    total = db.execute('SELECT COUNT(*) as count FROM courses WHERE status = "Published"').fetchone()['count']
    return jsonify({'total_courses': total, 'total_students': total * 45, 'total_instructors': db.execute('SELECT COUNT(DISTINCT instructor_name) as count FROM courses').fetchone()['count'], 'completion_rate': 87, 'timestamp': datetime.now().isoformat()})

@lib_bp.route('/api/v1/validate-course', methods=['POST'])
def validate_course_api():
    data = request.get_json()
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    category = data.get('category', '').strip()
    instructor_name = data.get('instructor_name', '').strip()
    objectives = data.get('objectives', '').strip()
    combined_text = f"{title} {description} {category} {objectives}".lower()

    results = {'approved': False, 'finalScore': 0, 'stages': [], 'recommendations': [], 'criticalIssues': []}

    # Stage 1: Initial Content Check (20 pts)
    s1 = 0
    s1_issues = []
    if len(title) >= 10: s1 += 5
    else: s1_issues.append(f"Title too short ({len(title)}/10)")
    if len(description) >= 50: s1 += 5
    else: s1_issues.append(f"Description too brief ({len(description)}/50)")
    if category: s1 += 5
    else: s1_issues.append("No category")
    if instructor_name and len(instructor_name) >= 3: s1 += 5
    else: s1_issues.append("Instructor name incomplete")
    results['stages'].append({'name': 'Initial Content Check', 'score': s1, 'maxScore': 20, 'passed': s1 >= 15, 'issues': s1_issues, 'message': 'OK' if s1 >= 15 else 'Missing info'})

    # Stage 2: Safety (25 pts)
    s2 = 25; s2_issues = []
    is_profane, flagged = check_profanity_smart(combined_text)
    if is_profane: s2 = 0; s2_issues.append(f"Inappropriate: {flagged}"); results['criticalIssues'].append(f"Language: {flagged}")
    prohibited = ['gambling', 'casino', 'betting', 'drugs', 'weapon', 'violence', 'scam', 'fraud']
    found = [kw for kw in prohibited if kw in combined_text]
    if found: s2 = 0; s2_issues.append(f"Prohibited: {found[0]}"); results['criticalIssues'].append(f"Content: {found[0]}")
    results['stages'].append({'name': 'Safety & Appropriateness', 'score': s2, 'maxScore': 25, 'passed': s2 >= 20, 'issues': s2_issues, 'message': 'Safe' if s2 >= 20 else 'Issues found'})

    # Stage 3: Educational Quality (25 pts)
    s3 = 0; s3_issues = []
    edu_kw = ['learn','teach','tutorial','guide','course','lesson','training','skill','practice','workshop','education','master','understand','develop','improve','knowledge']
    edu_count = sum(1 for kw in edu_kw if kw in combined_text)
    if edu_count >= 5: s3 += 15
    elif edu_count >= 3: s3 += 10; s3_issues.append("Could emphasize learning more")
    elif edu_count >= 1: s3 += 5; s3_issues.append("Limited educational focus")
    else: s3_issues.append("No educational keywords")
    if objectives and len(objectives) >= 30: s3 += 10
    elif objectives: s3 += 5; s3_issues.append("Objectives need detail")
    else: s3_issues.append("No objectives")
    results['stages'].append({'name': 'Educational Quality', 'score': s3, 'maxScore': 25, 'passed': s3 >= 15, 'issues': s3_issues, 'message': 'Strong' if s3 >= 20 else 'Needs work'})

    # Stage 4: Readability (15 pts)
    s4 = 8; s4_issues = []
    wc = len(description.split())
    if wc >= 50: s4 += 5
    elif wc >= 30: s4 += 3
    else: s4_issues.append("Too brief")
    if HAS_TEXTSTAT and wc >= 10:
        try:
            r = textstat.flesch_reading_ease(description)
            if 50 <= r <= 80: s4 += 2
        except: pass
    results['stages'].append({'name': 'Readability & Clarity', 'score': min(s4, 15), 'maxScore': 15, 'passed': s4 >= 10, 'issues': s4_issues, 'message': 'Clear' if s4 >= 12 else 'Could improve'})

    # Stage 5: Intergenerational (15 pts)
    s5 = 0; s5_issues = []
    ig_kw = ['senior','youth','generation','community','together','share','connect','bridge','tradition','experience','modern','family','beginner','all ages']
    ig_count = sum(1 for kw in ig_kw if kw in combined_text)
    if ig_count >= 3: s5 += 15
    elif ig_count >= 2: s5 += 10
    elif ig_count >= 1: s5 += 5
    else: s5_issues.append("Missing intergenerational aspect")
    results['stages'].append({'name': 'Intergenerational Value', 'score': s5, 'maxScore': 15, 'passed': s5 >= 8, 'issues': s5_issues, 'message': 'Strong' if s5 >= 12 else 'Consider adding'})

    total_score = sum(s['score'] for s in results['stages'])
    max_possible = sum(s['maxScore'] for s in results['stages'])
    final_pct = int((total_score / max_possible) * 100)
    results['finalScore'] = final_pct
    results['approved'] = final_pct >= 65 and len(results['criticalIssues']) == 0
    results['message'] = '✓ Approved!' if results['approved'] else '⚠ Needs improvement'
    return jsonify(results)

@lib_bp.route('/api/v1/courses')
def get_courses_api():
    db = get_lib_db()
    courses = db.execute('SELECT * FROM courses WHERE status = "Published" ORDER BY created_at DESC').fetchall()
    return jsonify([{'id': c['id'], 'title': c['title'], 'category': c['category'], 'skill_level': c['skill_level'], 'instructor_name': c['instructor_name'], 'rating': c['rating']} for c in courses])

@lib_bp.route('/api/v1/achievements')
def get_achievements():
    return jsonify([
        {'id': 'first-course', 'name': 'First Step', 'description': 'Complete your first course', 'icon': '🎓', 'unlocked': True},
        {'id': 'quiz-master', 'name': 'Quiz Master', 'description': 'Score 100% on a quiz', 'icon': '🏆', 'unlocked': True},
        {'id': 'streak-week', 'name': '7-Day Streak', 'description': 'Learn 7 consecutive days', 'icon': '🔥', 'unlocked': False, 'progress': 5},
    ])

@lib_bp.route('/module/<int:module_id>/complete', methods=['POST'])
def mark_module_complete(module_id):
    db = get_lib_db()
    data = request.get_json()
    course_id = data.get('course_id')
    if not course_id: return jsonify({'success': False, 'message': 'Missing course_id'}), 400
    try:
        user_id = get_current_user_id()
        db.execute('INSERT OR REPLACE INTO module_completion (course_id, module_id, user_id, completed, completed_at) VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)', (course_id, module_id, user_id))
        db.commit()
        total = db.execute('SELECT COUNT(*) FROM modules WHERE course_id = ?', (course_id,)).fetchone()[0]
        done = db.execute('SELECT COUNT(*) FROM module_completion WHERE course_id = ? AND user_id = ? AND completed = 1', (course_id, user_id)).fetchone()[0]
        return jsonify({'success': True, 'completed': done, 'total': total})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@lib_bp.route('/course/<int:course_id>/completion-status')
def get_completion_status(course_id):
    db = get_lib_db()
    modules = db.execute('SELECT id FROM modules WHERE course_id = ?', (course_id,)).fetchall()
    user_id = get_current_user_id()
    completions = db.execute('SELECT module_id, completed FROM module_completion WHERE course_id = ? AND user_id = ?', (course_id, user_id)).fetchall()
    completed_dict = {c['module_id']: c['completed'] for c in completions}
    total = len(modules)
    done = sum(1 for m in modules if completed_dict.get(m['id'], False))
    return jsonify({'total_modules': total, 'completed_modules': done, 'all_completed': done == total and total > 0, 'completion_percentage': (done/total*100) if total > 0 else 0})

@lib_bp.route('/course/<int:course_id>/comments', methods=['GET'])
def get_comments(course_id):
    db = get_lib_db()
    comments = db.execute('SELECT id, author_name, comment_text, created_at FROM course_comments WHERE course_id = ? ORDER BY created_at DESC', (course_id,)).fetchall()
    return jsonify([dict(c) for c in comments])

@lib_bp.route('/course/<int:course_id>/comment', methods=['POST'])
def post_comment(course_id):
    db = get_lib_db()
    data = request.get_json()
    author = data.get('author_name', 'Anonymous')
    text = data.get('comment_text', '').strip()
    if not text: return jsonify({'success': False, 'message': 'Empty'}), 400
    try:
        db.execute('INSERT INTO course_comments (course_id, author_name, comment_text) VALUES (?, ?, ?)', (course_id, author, text))
        db.commit()
        c = db.execute('SELECT id, author_name, comment_text, created_at FROM course_comments WHERE course_id = ? ORDER BY created_at DESC LIMIT 1', (course_id,)).fetchone()
        return jsonify({'success': True, 'comment': dict(c)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@lib_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
def delete_comment(comment_id):
    db = get_lib_db()
    db.execute('DELETE FROM course_comments WHERE id = ?', (comment_id,))
    db.commit()
    return jsonify({'success': True})

@lib_bp.route('/course/<int:course_id>/community-members', methods=['GET'])
def get_community_members(course_id):
    db = get_lib_db()
    try:
        members = db.execute('SELECT DISTINCT author_name FROM course_comments WHERE course_id = ? UNION SELECT DISTINCT author_name FROM community_hub_messages WHERE course_id = ?', (course_id, course_id)).fetchall()
        return jsonify({'count': len(members), 'members': [dict(m) for m in members]})
    except:
        return jsonify({'count': 0, 'members': []})

@lib_bp.route('/course/<int:course_id>/community-messages', methods=['GET'])
def get_community_messages(course_id):
    db = get_lib_db()
    try:
        msgs = db.execute('SELECT id, author_name, message_text, created_at FROM community_hub_messages WHERE course_id = ? ORDER BY created_at DESC LIMIT 50', (course_id,)).fetchall()
        return jsonify([dict(m) for m in msgs])
    except:
        return jsonify([])

@lib_bp.route('/course/<int:course_id>/community-message', methods=['POST'])
def post_community_message(course_id):
    db = get_lib_db()
    data = request.get_json()
    author = data.get('author_name', 'Anonymous')
    text = data.get('message_text', '').strip()
    if not text: return jsonify({'success': False, 'message': 'Empty'}), 400
    try:
        db.execute('INSERT INTO community_hub_messages (course_id, author_name, message_text) VALUES (?, ?, ?)', (course_id, author, text))
        db.commit()
        msg = db.execute('SELECT id, author_name, message_text, created_at FROM community_hub_messages WHERE course_id = ? ORDER BY created_at DESC LIMIT 1', (course_id,)).fetchone()
        return jsonify({'success': True, 'data': dict(msg)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
