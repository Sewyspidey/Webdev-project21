"""
SocialHub Models - Separate from main BridgeHive models
Uses 'sh_' prefix on table names to avoid conflicts
"""
from datetime import datetime

# db will be imported from the main app - set in init
db = None

def init_sh_models(database):
    """Initialize with the app's db instance"""
    global db
    db = database
    return get_models()

def get_models():
    """Return model classes after db is initialized"""
    
    class SHUser(db.Model):
        __tablename__ = 'sh_users'
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), nullable=False, unique=True)
        posts = db.relationship('SHPost', backref='author', lazy=True)

    class SHPost(db.Model):
        __tablename__ = 'sh_posts'
        id = db.Column(db.Integer, primary_key=True)
        body = db.Column(db.Text, nullable=False)
        timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
        user_id = db.Column(db.Integer, db.ForeignKey('sh_users.id'), nullable=False)
        post_type = db.Column(db.String(50), default='general')
        related_course = db.Column(db.String(100), nullable=True)
        media_type = db.Column(db.String(20))
        media_filename = db.Column(db.String(200))
        comments = db.relationship('SHComment', backref='post', lazy=True, cascade="all, delete-orphan")
        likes = db.relationship('SHLike', backref='post', lazy=True, cascade="all, delete-orphan")

    class SHComment(db.Model):
        __tablename__ = 'sh_comments'
        id = db.Column(db.Integer, primary_key=True)
        body = db.Column(db.String(500), nullable=False)
        timestamp = db.Column(db.DateTime, default=datetime.utcnow)
        user_id = db.Column(db.Integer, db.ForeignKey('sh_users.id'), nullable=False)
        post_id = db.Column(db.Integer, db.ForeignKey('sh_posts.id'), nullable=False)
        username = db.Column(db.String(80))

    class SHLike(db.Model):
        __tablename__ = 'sh_likes'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('sh_users.id'), nullable=False)
        post_id = db.Column(db.Integer, db.ForeignKey('sh_posts.id'), nullable=False)

    class SHPrivateMessage(db.Model):
        __tablename__ = 'sh_private_messages'
        id = db.Column(db.Integer, primary_key=True)
        sender = db.Column(db.String(80), nullable=False)
        recipient = db.Column(db.String(80), nullable=False)
        body = db.Column(db.Text, nullable=False)
        timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    return SHUser, SHPost, SHComment, SHLike, SHPrivateMessage
