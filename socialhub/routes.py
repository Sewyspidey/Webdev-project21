import os
from flask import render_template, request, jsonify, current_app, redirect, url_for, session
from werkzeug.utils import secure_filename
from . import socialhub_bp, socketio
from flask_socketio import emit
from sqlalchemy import or_

# These will be set by init_socialhub_routes()
SHUser = None
SHPost = None
SHComment = None
SHLike = None
SHPrivateMessage = None
db = None
MainUser = None  # Main app User model for navbar

def init_socialhub_routes(database, models, main_user_model=None):
    """Initialize route references to models and db"""
    global SHUser, SHPost, SHComment, SHLike, SHPrivateMessage, db, MainUser
    db = database
    SHUser, SHPost, SHComment, SHLike, SHPrivateMessage = models
    MainUser = main_user_model

def get_main_user():
    """Get main app User from session for navbar display"""
    if MainUser:
        user_id = session.get('user_id', 1)
        u = MainUser.query.get(user_id)
        if u:
            return u
        return MainUser.query.first()
    return None

# --- 1. NAVIGATION ---

@socialhub_bp.route('/', methods=['GET'])
def feed():
    username_param = request.args.get('user')
    
    # Try to find specific user or first user
    if username_param:
        currentUser = SHUser.query.filter_by(username=username_param).first()
    else:
        # Try to get the currently logged in user from session first
        main_user = get_main_user()
        if main_user:
            currentUser = SHUser.query.filter_by(username=main_user.username).first()
        
        # Fallback if no logged in user matches
        if not currentUser:
            currentUser = SHUser.query.first()

    # SAFETY CHECK: If database is empty or user not found, render a "setup" or empty state
    if not currentUser:
        # Returns an empty feed instead of crashing with 500 error
        return render_template('socialhub/feed.html', posts=[], user=None, community_users=[], user_likes=[], main_user=get_main_user())
    
    posts = SHPost.query.order_by(SHPost.timestamp.desc()).limit(20).all()
    # Ensure currentUser is valid before filtering
    all_users = SHUser.query.filter(SHUser.username != currentUser.username).all()
    user_likes = [like.post_id for like in SHLike.query.filter_by(user_id=currentUser.id).all()]
    
    return render_template('socialhub/feed.html', posts=posts, user=currentUser, community_users=all_users, user_likes=user_likes, main_user=get_main_user())

@socialhub_bp.route('/explore')
def explore():
    username_param = request.args.get('user')
    currentUser = SHUser.query.filter_by(username=username_param).first() if username_param else SHUser.query.first()
    community_users = SHUser.query.filter(SHUser.username != currentUser.username).all()
    trending_posts = SHPost.query.limit(2).all()
    return render_template('socialhub/explore.html', user=currentUser, community_users=community_users, posts=trending_posts, main_user=get_main_user())

@socialhub_bp.route('/saved')
def saved():
    username_param = request.args.get('user')
    currentUser = SHUser.query.filter_by(username=username_param).first() if username_param else SHUser.query.first()
    community_users = SHUser.query.filter(SHUser.username != currentUser.username).all()
    return render_template('socialhub/saved.html', user=currentUser, community_users=community_users, main_user=get_main_user())

@socialhub_bp.route('/saved/posts')
def saved_posts():
    username_param = request.args.get('user')
    currentUser = SHUser.query.filter_by(username=username_param).first() if username_param else SHUser.query.first()
    community_users = SHUser.query.filter(SHUser.username != currentUser.username).all()
    return render_template('socialhub/saved_posts.html', user=currentUser, community_users=community_users, main_user=get_main_user())

@socialhub_bp.route('/saved/resources')
def saved_resources():
    username_param = request.args.get('user')
    currentUser = SHUser.query.filter_by(username=username_param).first() if username_param else SHUser.query.first()
    community_users = SHUser.query.filter(SHUser.username != currentUser.username).all()
    return render_template('socialhub/saved_resources.html', user=currentUser, community_users=community_users, main_user=get_main_user())

@socialhub_bp.route('/collections/new')
def create_collection():
    username_param = request.args.get('user')
    currentUser = SHUser.query.filter_by(username=username_param).first() if username_param else SHUser.query.first()
    return render_template('socialhub/create_collection.html', user=currentUser, main_user=get_main_user())

# --- 2. FILE UPLOAD API ---
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@socialhub_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        import time
        filename = f"{int(time.time())}_{filename}"
        upload_path = current_app.config.get('SOCIALHUB_UPLOAD_FOLDER', 
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads'))
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        file.save(os.path.join(upload_path, filename))
        ext = filename.rsplit('.', 1)[1].lower()
        media_type = 'video' if ext in ['mp4', 'mov'] else 'image'
        return jsonify({'filename': filename, 'type': media_type})
    return jsonify({'error': 'File type not allowed'}), 400

# --- 3. POST ACTIONS ---

@socialhub_bp.route('/api/like_post', methods=['POST'])
def like_post():
    data = request.json
    post_id = data.get('post_id')
    username = data.get('username')
    user = SHUser.query.filter_by(username=username).first()
    post = SHPost.query.get(post_id)
    if user and post:
        existing_like = SHLike.query.filter_by(user_id=user.id, post_id=post.id).first()
        if existing_like:
            db.session.delete(existing_like)
            action = 'unliked'
        else:
            new_like = SHLike(user_id=user.id, post_id=post.id)
            db.session.add(new_like)
            action = 'liked'
        db.session.commit()
        return jsonify({'status': 'success', 'action': action, 'count': len(post.likes)})
    return jsonify({'status': 'error'}), 400

@socialhub_bp.route('/api/edit_post', methods=['POST'])
def edit_post():
    data = request.json
    post = SHPost.query.get(data['post_id'])
    if post:
        post.body = data['new_body']
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 404

@socialhub_bp.route('/api/report_post', methods=['POST'])
def report_post():
    print(f"REPORT: Post {request.json['post_id']} reported by {request.json['username']}")
    return jsonify({'status': 'success', 'message': 'Post has been flagged for review.'})

@socialhub_bp.route('/api/chat_history')
def get_chat_history():
    user1 = request.args.get('user1')
    user2 = request.args.get('user2')
    messages = SHPrivateMessage.query.filter(
        or_((SHPrivateMessage.sender == user1) & (SHPrivateMessage.recipient == user2),
            (SHPrivateMessage.sender == user2) & (SHPrivateMessage.recipient == user1))
    ).order_by(SHPrivateMessage.timestamp.asc()).limit(50).all()
    return jsonify([{'sender': msg.sender, 'body': msg.body} for msg in messages])

# --- 4. SOCKET EVENTS ---

@socketio.on('send_message')
def handle_feed_post(data):
    author = SHUser.query.filter_by(username=data['username']).first()
    if author:
        new_post = SHPost(
            body=data['body'], author=author,
            post_type=data.get('post_type', 'general'),
            related_course=data.get('course_name', ''),
            media_type=data.get('media_type'),
            media_filename=data.get('media_filename')
        )
        db.session.add(new_post)
        db.session.commit()
        emit('receive_message', {
            'id': new_post.id,
            'username': author.username,
            'avatar_letter': author.username[0].upper(),
            'body': new_post.body,
            'timestamp': new_post.timestamp.strftime('%I:%M %p'),
            'post_type': new_post.post_type,
            'related_course': new_post.related_course,
            'media_type': new_post.media_type,
            'media_filename': new_post.media_filename
        }, broadcast=True)

@socketio.on('send_comment')
def handle_comment(data):
    user = SHUser.query.filter_by(username=data['username']).first()
    if user:
        new_comment = SHComment(
            body=data['body'],
            user_id=user.id,
            post_id=data['post_id'],
            username=user.username
        )
        db.session.add(new_comment)
        db.session.commit()
        emit('receive_comment', {'post_id': data['post_id'], 'comment_id': new_comment.id, 'username': user.username, 'body': data['body']}, broadcast=True)

@socketio.on('private_chat_event')
def handle_private_chat(data):
    new_msg = SHPrivateMessage(sender=data['username'], recipient=data['recipient'], body=data['message'])
    db.session.add(new_msg)
    db.session.commit()
    emit('receive_private_message', {'username': data['username'], 'recipient': data['recipient'], 'message': data['message'], 'avatar': data['username'][0].upper()}, broadcast=True)

# --- 5. DELETE COMMENT API ---

@socialhub_bp.route('/api/delete_comment', methods=['POST'])
def delete_comment():
    data = request.json
    comment_id = data.get('comment_id')
    username = data.get('username')
    comment = SHComment.query.get(comment_id)
    if comment and comment.username == username:
        post_id = comment.post_id
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'status': 'success', 'post_id': post_id})
    return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

# --- 6. COMMUNITY PAGE ---

@socialhub_bp.route('/community/<name>')
def community(name):
    username_param = request.args.get('user')
    currentUser = SHUser.query.filter_by(username=username_param).first() if username_param else SHUser.query.first()
    community_users = SHUser.query.filter(SHUser.username != currentUser.username).all()
    
    # MOCK Community Data
    community_data = {}
    if name == 'Dialect Exchange':
        community_data = {
            'name': 'Dialect Exchange',
            'initials': 'DE',
            'bg_color': '#D4A373',
            'description': 'Bridging generations through language. Share Hokkien, Teochew, Cantonese phrases and stories!',
            'members_count': 128,
            'is_joined': True
        }
    elif name == 'Gardening Pros':
         community_data = {
            'name': 'Gardening Pros',
            'initials': 'GP',
            'bg_color': '#CCD5AE',
            'description': 'Tips for HDB corridor gardening, community plots, and urban farming.',
            'members_count': 85,
            'is_joined': True
        }
    else:
         community_data = {
            'name': name,
            'initials': name[0:2].upper(),
            'bg_color': '#718096',
            'description': 'Welcome to this community hive.',
            'members_count': 0,
            'is_joined': False
        }

    posts = SHPost.query.order_by(SHPost.timestamp.desc()).limit(10).all()
    user_likes = [like.post_id for like in SHLike.query.filter_by(user_id=currentUser.id).all()]

    return render_template('socialhub/community.html', user=currentUser, community_users=community_users, community=community_data, posts=posts, user_likes=user_likes, main_user=get_main_user())
