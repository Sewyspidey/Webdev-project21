# ============================================================================
# BridgeHive - Intergenerational Learning Platform
# IT1825 Web Development Project
# ============================================================================
# This is my main Flask application file that handles all the backend logic.
# It connects to SQLite database and uses Jinja2 templates for rendering pages.
# ============================================================================

# --- IMPORTS ---
# Flask stuff for web app, routing, sessions, and JSON responses
from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify
# SQLAlchemy for database ORM (lets me use Python classes instead of raw SQL)
from flask_sqlalchemy import SQLAlchemy
# Security functions for hashing passwords (admin login)
from werkzeug.security import generate_password_hash, check_password_hash
# For timestamps on database records
from datetime import datetime, timedelta
# For FAQ search matching - compares how similar two strings are
from difflib import SequenceMatcher
# Google Gemini AI for chatbot functionality (new package)
from google import genai
import os

# --- FLASK APP SETUP ---
app = Flask(__name__)

# Register the courses library blueprint (serves /lib/* routes)
from library_routes import lib_bp, init_lib_db
app.register_blueprint(lib_bp)
app.config['SECRET_KEY'] = 'bridgehive-secret-key'  # Needed for session/flash messages
DB_PATH = os.getenv('DB_PATH', os.path.join(os.path.dirname(__file__), 'bridgehive.db'))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'  # Database file location
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disables warning messages

db = SQLAlchemy(app)  # Initialize database connection

# Register the SocialHub blueprint (serves /socialhub/* routes)
import os as _os
from socialhub import socialhub_bp, socketio as sh_socketio
from socialhub.models import init_sh_models
from socialhub.routes import init_socialhub_routes
app.register_blueprint(socialhub_bp, url_prefix='/socialhub')
sh_socketio.init_app(app)
app.config['SOCIALHUB_UPLOAD_FOLDER'] = _os.path.join(
    _os.path.dirname(_os.path.abspath(__file__)), 'socialhub', 'static', 'uploads')
_os.makedirs(app.config['SOCIALHUB_UPLOAD_FOLDER'], exist_ok=True)


# ============================================================================
# GEMINI AI CHATBOT CONFIGURATION
# This sets up the AI with restrictions so it only answers BridgeHive questions
# ============================================================================

# ============================================================================
# TRANSLATIONS - All UI elements in 4 languages
# ============================================================================
TRANSLATIONS = {
    "en": {
        # Navigation
        "nav.dashboard": "Dashboard", "nav.rewards": "Rewards", "nav.profile": "Profile",
        "nav.settings": "Settings", "nav.support": "Support", "nav.logout": "Log Out",
        "nav.learn": "Learn", "nav.create": "Create", "nav.chat": "Chat",
        "nav.view_progress": "View progress", "nav.browse_courses": "Browse courses",
        "nav.view_templates": "View Templates", "nav.create_course": "Create new course",
        "nav.create_folder": "Create folder", "nav.admin_login": "Admin Login",
        "nav.notifications": "Notifications",
        
        # Homepage
        "home.jump_back": "Jump back in", "home.pick_up": "Pick up where you last left off...",
        "home.learn_courses": "Learn courses:", "home.your_creations": "Your creations:",
        "home.no_courses": "No courses started yet. Browse courses to begin!",
        "home.no_templates": "No templates started yet. Browse templates to begin creating!",
        "home.think_like": "We think you may like these", "home.based_interests": "Based on your interests",
        "home.latest": "Latest from us", "home.explore_new": "Explore new courses and templates",
        "home.see_others": "See what others are creating", "home.based_topics": "Based on the topics you're working with",
        "home.view_all": "View all", "home.courses": "Courses:", "home.templates": "Templates:",
        "home.my_collections": "My collections", "home.organize": "Organize your courses and templates",
        "home.liked_courses": "Liked Courses", "home.watch_later": "Watch Later",
        "home.liked_templates": "Liked Templates", "home.use_later": "Use Later",
        "home.new_folder": "New Folder", "home.welcome": "Welcome",
        "home.start_journey": "Start your learning and creating journey today",
        "home.no_items_folder": "courses · 0 templates",
        
        # Notifications
        "notif.title": "Notifications", "notif.subtitle": "Your latest updates and reminders.",
        "notif.no_notifications": "You have no notifications.",
        "notif.send_all": "Send notification to all accounts", "notif.notif_title": "Notification title",
        "notif.write_msg": "Write your message for all users", "notif.send_btn": "Send to all users",
        
        # Common
        "common.points": "Hive Points", "common.search": "Search", "common.save": "Save",
        "common.cancel": "Cancel", "common.confirm": "Confirm", "common.submit": "Submit",
        "common.purchase": "Purchase", "common.owned": "Owned", "common.close": "Close",
        
        # Settings
        "settings.title": "Settings", "settings.subtitle": "Manage your preferences and security",
        "settings.success": "Settings saved",
        "settings.language": "Language", "settings.display_lang": "Display Language",
        "settings.lang_desc": "Select your preferred language for the interface.",
        "settings.privacy": "Privacy", "settings.profile_vis": "Profile Visibility",
        "settings.public": "Public", "settings.friends": "Friends Only", "settings.private": "Private",
        "settings.activity": "Activity Status", "settings.activity_desc": "Show when you are active.",
        "settings.security": "Account Security", "settings.change_pw": "Change Password",
        "settings.curr_pw": "Current Password", "settings.new_pw": "New Password",
        "settings.conf_pw": "Confirm Password", "settings.update_pw": "Update Password",
        "settings.2fa": "Two-Factor Authentication", "settings.2fa_desc": "Secure your account with SingPass.",
        "settings.enable_singpass": "Enable with SingPass", "settings.singpass_connected": "SingPass Connected",
        "settings.disconnect": "Disconnect",
        "settings.audio": "Audio Features", "settings.sfx": "Sound Effects",
        "settings.sfx_desc": "Play sounds for notifications and actions.",
        "settings.tts": "Text-to-Speech", "settings.tts_desc": "Read page content aloud.",
        "settings.visual": "Visual & Display", "settings.dark_mode": "Dark Mode",
        "settings.dark_desc": "Reduces eye strain in low light environments.",
        "settings.high_contrast": "High Contrast", "settings.high_desc": "Increases contrast for better visibility.",
        "settings.font_size": "Font Size", "settings.fs_std": "Standard", "settings.fs_lg": "Large",
        "settings.fs_xl": "Extra Large",
        "settings.system": "System Actions", "settings.reset": "Reset All Settings",
        "settings.reset_desc": "Restore default configuration.", "settings.reset_btn": "Reset",
        
        # Rewards
        "rewards.title": "Rewards Shop", "rewards.subtitle": "Exchange your points for items.",
        "rewards.balance": "Your Balance", "rewards.shop": "Shop", "rewards.quests": "Quests",
        
        # Support
        "support.title": "Support Center", "support.subtitle": "Get help, browse FAQs, or submit a ticket",
        "support.faq": "FAQs", "support.submit": "Submit Ticket", "support.history": "My Tickets",
        "support.search_faq": "Search FAQs...", "support.contact": "Contact",
        "support.help_center": "Help Center", "support.feedback": "Feedback",
        
        # Profile
        "profile.title": "Profile", "profile.edit": "Edit", "profile.settings": "Settings",
        "profile.points": "Points", "profile.streak": "Streak", "profile.active": "Active Now",
        "profile.inventory": "My Inventory", "profile.title_items": "Title", 
        "profile.decorations": "Avatar Decoration", "profile.effects": "Profile Effects",
        "profile.equip": "Equip", "profile.equipped": "Equipped", "profile.no_items": "You have no",
        "profile.browse_shop": "Browse Shop",
        
        # Rewards - Extended
        "rewards.title": "Rewards Shop", "rewards.subtitle": "Exchange your points for items.",
        "rewards.balance": "Your Balance", "rewards.shop": "Shop", "rewards.quests": "Quests",
        "rewards.all_items": "All Items", "rewards.decorations": "Decorations",
        "rewards.profile_effects": "Profile Effects", "rewards.chat_effects": "Chat Effects",
        "rewards.nameplates": "Nameplates", "rewards.bundles": "Bundles",
        "rewards.purchase": "Purchase", "rewards.owned": "Owned",
        "rewards.legendary": "LEGENDARY", "rewards.epic": "EPIC", "rewards.rare": "RARE",
        "rewards.common": "COMMON", "rewards.exclusive": "Exclusive",
        "rewards.quest_watch": "Watch to Earn Points", "rewards.quest_claim": "Claim",
        "rewards.quest_watch_msg": "Watch the video to unlock your reward",
        "rewards.quest_timer": "remaining to unlock reward", "rewards.quest_complete": "Video complete! Claim your reward below.",
        "rewards.quest_claimed": "Claimed!", "rewards.quest_claiming": "Claiming...",
        
        # Social Hub
        "social.feed": "Feed", "social.explore": "Explore", "social.saved": "Saved",
        "social.communities": "My Communities", "social.join": "Join New Hive",
        "social.whats_happening": "What's happening?", "social.post": "Post",
        "social.media": "Media", "social.achievement": "Achievement",
        "social.likes": "Likes", "social.comments": "Comments",
        "social.members_online": "Members Online", "social.member": "Member",
        "social.completed_course": "COMPLETED COURSE", "social.chat": "Chat",
        
        # Courses
        "courses.all": "All Courses", "courses.in_progress": "In Progress",
        "courses.history": "History", "courses.recommended": "Recommended",
        "courses.browse": "Browse Courses", "courses.search": "Search courses...",
        "courses.start": "Start Course", "courses.continue": "Continue",
        "courses.completed": "Completed",
        
        # Footer - Extended
        "footer.tagline": "Bridging generations through shared knowledge",
        "footer.platform": "Platform", "footer.resources": "Resources", "footer.legal": "Legal",
        "footer.about": "About Us", "footer.dashboard": "Dashboard",
        "footer.safety": "Safety Tips", "footer.community": "Community Guidelines",
        "footer.accessibility": "Accessibility", "footer.help_center": "Help Center",
        "footer.contact": "Contact", "footer.feedback": "Feedback",
        "footer.privacy": "Privacy Policy", "footer.terms": "Terms of Service",
        "footer.copyright": "© 2025 BridgeHive. Made in Singapore.",

        # Homepage
        "home.welcome": "Welcome", "home.welcome_back": "Welcome back",
        "home.start_journey": "Start your learning and creating journey today",
        "home.jump_back": "Jump back in", "home.pick_up": "Pick up where you last left off...",
        "home.learn_courses": "Learn courses:", "home.your_creations": "Your creations:",
        "home.no_courses": "No courses started yet. Browse courses to begin!",
        "home.no_templates": "No templates started yet. Browse templates to begin creating!",
        "home.may_like": "We think you may like these", "home.courses": "Courses:",
        "home.templates": "Templates:", "home.latest": "Latest from us",
        "home.explore_new": "Explore new courses and templates",
        "home.others_creating": "See what others are creating",
        "home.based_on": "Based on the topics you're working with",
        "home.collections": "My collections", "home.organize": "Organize your courses and templates",
        "home.view_all": "View all", "home.new_folder": "New Folder",
        "home.liked_courses": "Liked Courses", "home.watch_later": "Watch Later",
        "home.liked_templates": "Liked Templates", "home.use_later": "Use Later",
        "home.based_interests": "Based on your interests",

        # Navbar dropdown items
        "nav.view_progress": "View progress", "nav.browse_courses": "Browse courses",
        "nav.view_templates": "View Templates", "nav.create_course": "Create new course",
        "nav.create_folder": "Create folder", "nav.notifications": "Notifications",
        "nav.admin_login": "Admin Login",

        # Notifications page
        "notif.title": "Notifications", "notif.subtitle": "Your latest updates and reminders.",
        "notif.none": "You have no notifications.", "notif.send_all": "Send notification to all accounts",
        "notif.send_btn": "Send to all users", "notif.notif_title": "Notification title",
        "notif.write_msg": "Write your message for all users",

        # Support page extra
        "support.no_tickets": "No tickets yet",
        "support.ticket_desc": "You haven't submitted any support tickets",
        "support.first_ticket": "Submit Your First Ticket",
        "support.category": "Category", "support.select_cat": "Select a category",
        "support.subject": "Subject", "support.brief_desc": "Brief description",
        "support.message": "Message", "support.detail_desc": "Describe your issue in detail...",
        "support.submit_ticket": "Submit Ticket", "support.submit_title": "Submit a Ticket",
        "support.submit_sub": "We'll get back to you as soon as possible.",
    },
    
    "zh": {  # Chinese (Simplified)
        "nav.dashboard": "仪表板", "nav.rewards": "奖励", "nav.profile": "个人资料",
        "nav.settings": "设置", "nav.support": "支持", "nav.logout": "退出登录",
        "nav.learn": "学习", "nav.create": "创建", "nav.chat": "聊天",
        "nav.view_progress": "查看进度", "nav.browse_courses": "浏览课程",
        "nav.view_templates": "查看模板", "nav.create_course": "创建新课程",
        "nav.create_folder": "创建文件夹", "nav.admin_login": "管理员登录",
        "nav.notifications": "通知",
        "home.jump_back": "继续学习", "home.pick_up": "继续您上次的学习...",
        "home.learn_courses": "学习课程：", "home.your_creations": "您的创作：",
        "home.no_courses": "还没有开始的课程。浏览课程开始学习！",
        "home.no_templates": "还没有开始的模板。浏览模板开始创作！",
        "home.think_like": "您可能喜欢这些", "home.based_interests": "根据您的兴趣",
        "home.latest": "最新内容", "home.explore_new": "探索新课程和模板",
        "home.see_others": "看看别人在创作什么", "home.based_topics": "基于您正在学习的主题",
        "home.view_all": "查看全部", "home.courses": "课程：", "home.templates": "模板：",
        "home.my_collections": "我的收藏", "home.organize": "整理您的课程和模板",
        "home.liked_courses": "喜欢的课程", "home.watch_later": "稍后观看",
        "home.liked_templates": "喜欢的模板", "home.use_later": "稍后使用",
        "home.new_folder": "新建文件夹", "home.welcome": "欢迎",
        "home.start_journey": "今天开始您的学习和创作之旅",
        "notif.title": "通知", "notif.subtitle": "您的最新更新和提醒。",
        "notif.no_notifications": "您没有通知。",
        "notif.send_all": "向所有账户发送通知", "notif.notif_title": "通知标题",
        "notif.write_msg": "为所有用户撰写消息", "notif.send_btn": "发送给所有用户",
        "common.points": "蜂巢积分", "common.search": "搜索", "common.save": "保存",
        "common.cancel": "取消", "common.confirm": "确认", "common.submit": "提交",
        "common.purchase": "购买", "common.owned": "已拥有", "common.close": "关闭",
        "settings.title": "设置", "settings.subtitle": "管理您的偏好和安全设置",
        "settings.success": "设置已保存",
        "settings.language": "语言", "settings.display_lang": "显示语言",
        "settings.lang_desc": "选择您的界面首选语言。",
        "settings.privacy": "隐私", "settings.profile_vis": "个人资料可见性",
        "settings.public": "公开", "settings.friends": "仅好友", "settings.private": "私密",
        "settings.activity": "活动状态", "settings.activity_desc": "显示您的在线状态。",
        "settings.security": "账户安全", "settings.change_pw": "修改密码",
        "settings.curr_pw": "当前密码", "settings.new_pw": "新密码",
        "settings.conf_pw": "确认密码", "settings.update_pw": "更新密码",
        "settings.2fa": "双重验证", "settings.2fa_desc": "使用 SingPass 保护账户。",
        "settings.enable_singpass": "通过 SingPass 启用", "settings.singpass_connected": "SingPass 已连接",
        "settings.disconnect": "断开连接",
        "settings.audio": "音频功能", "settings.sfx": "音效",
        "settings.sfx_desc": "为通知和操作播放声音。",
        "settings.tts": "文字转语音", "settings.tts_desc": "高亮文字即可朗读内容。",
        "settings.visual": "视觉与显示", "settings.dark_mode": "暗黑模式",
        "settings.dark_desc": "在低光环境下减少眼睛疲劳。",
        "settings.high_contrast": "高对比度", "settings.high_desc": "提高对比度以改善可见性。",
        "settings.font_size": "字体大小", "settings.fs_std": "标准", "settings.fs_lg": "大",
        "settings.fs_xl": "特大",
        "settings.system": "系统操作", "settings.reset": "重置所有设置",
        "settings.reset_desc": "恢复默认配置。", "settings.reset_btn": "重置",
        "rewards.title": "奖励商店", "rewards.subtitle": "用积分兑换物品。",
        "rewards.balance": "您的余额", "rewards.shop": "商店", "rewards.quests": "任务",
        "support.title": "支持中心", "support.subtitle": "获取帮助、浏览常见问题或提交工单",
        "support.faq": "常见问题", "support.submit": "提交工单", "support.history": "我的工单",
        "support.search_faq": "搜索常见问题...", "support.contact": "联系",
        "support.help_center": "帮助中心", "support.feedback": "反馈",
        
        "profile.title": "个人资料", "profile.edit": "编辑", "profile.settings": "设置",
        "profile.points": "积分", "profile.streak": "连续", "profile.active": "在线中",
        "profile.inventory": "我的物品", "profile.title_items": "称号",
        "profile.decorations": "头像装饰", "profile.effects": "个人资料效果",
        "profile.equip": "装备", "profile.equipped": "已装备", "profile.no_items": "您没有",
        "profile.browse_shop": "浏览商店",
        
        "rewards.title": "奖励商店", "rewards.subtitle": "用积分兑换物品。",
        "rewards.balance": "您的余额", "rewards.shop": "商店", "rewards.quests": "任务",
        "rewards.all_items": "所有物品", "rewards.decorations": "装饰",
        "rewards.profile_effects": "个人资料效果", "rewards.chat_effects": "聊天效果",
        "rewards.nameplates": "名牌", "rewards.bundles": "捆绑包",
        "rewards.purchase": "购买", "rewards.owned": "已拥有",
        "rewards.legendary": "传奇", "rewards.epic": "史诗", "rewards.rare": "稀有",
        "rewards.common": "普通", "rewards.exclusive": "独家",
        "rewards.quest_watch": "观看以赚取积分", "rewards.quest_claim": "领取",
        "rewards.quest_watch_msg": "观看视频以解锁奖励",
        "rewards.quest_timer": "剩余时间解锁奖励", "rewards.quest_complete": "视频完成！领取您的奖励。",
        "rewards.quest_claimed": "已领取！", "rewards.quest_claiming": "领取中...",
        
        "social.feed": "动态", "social.explore": "探索", "social.saved": "已保存",
        "social.communities": "我的社区", "social.join": "加入新蜂巢",
        "social.whats_happening": "发生了什么？", "social.post": "发布",
        "social.media": "媒体", "social.achievement": "成就",
        "social.likes": "赞", "social.comments": "评论",
        "social.members_online": "在线成员", "social.member": "成员",
        "social.completed_course": "完成课程", "social.chat": "聊天",
        
        "courses.all": "所有课程", "courses.in_progress": "进行中",
        "courses.history": "历史", "courses.recommended": "推荐",
        "courses.browse": "浏览课程", "courses.search": "搜索课程...",
        "courses.start": "开始课程", "courses.continue": "继续",
        "courses.completed": "已完成",
        
        "footer.tagline": "通过共享知识连接世代",
        "footer.platform": "平台", "footer.resources": "资源", "footer.legal": "法律",
        "footer.about": "关于我们", "footer.dashboard": "仪表板",
        "footer.safety": "安全提示", "footer.community": "社区准则",
        "footer.accessibility": "无障碍", "footer.help_center": "帮助中心",
        "footer.contact": "联系", "footer.feedback": "反馈",
        "footer.privacy": "隐私政策", "footer.terms": "服务条款",
        "footer.copyright": "© 2025 BridgeHive。新加坡制造。",

        # Homepage
        "home.welcome": "欢迎", "home.welcome_back": "欢迎回来",
        "home.start_journey": "今天开始您的学习和创作之旅",
        "home.jump_back": "继续学习", "home.pick_up": "从上次停止的地方继续...",
        "home.learn_courses": "学习课程：", "home.your_creations": "我的创作：",
        "home.no_courses": "尚未开始任何课程。浏览课程开始学习！",
        "home.no_templates": "尚未开始任何模板。浏览模板开始创作！",
        "home.may_like": "您可能喜欢这些", "home.courses": "课程：",
        "home.templates": "模板：", "home.latest": "最新内容",
        "home.explore_new": "探索新课程和模板",
        "home.others_creating": "看看其他人在创作什么",
        "home.based_on": "基于您正在学习的主题",
        "home.collections": "我的收藏", "home.organize": "整理您的课程和模板",
        "home.view_all": "查看全部", "home.new_folder": "新建文件夹",
        "home.liked_courses": "喜欢的课程", "home.watch_later": "稍后观看",
        "home.liked_templates": "喜欢的模板", "home.use_later": "稍后使用",
        "home.based_interests": "基于您的兴趣",
        "nav.view_progress": "查看进度", "nav.browse_courses": "浏览课程",
        "nav.view_templates": "查看模板", "nav.create_course": "创建新课程",
        "nav.create_folder": "创建文件夹", "nav.notifications": "通知",
        "nav.admin_login": "管理员登录",
        "notif.title": "通知", "notif.subtitle": "您的最新更新和提醒。",
        "notif.none": "您没有通知。", "notif.send_all": "向所有账户发送通知",
        "notif.send_btn": "发送给所有用户", "notif.notif_title": "通知标题",
        "notif.write_msg": "为所有用户写下您的消息",
        "support.no_tickets": "暂无工单",
        "support.ticket_desc": "您还没有提交任何支持工单",
        "support.first_ticket": "提交您的第一个工单",
        "support.category": "类别", "support.select_cat": "选择类别",
        "support.subject": "主题", "support.brief_desc": "简短描述",
        "support.message": "消息", "support.detail_desc": "详细描述您的问题...",
        "support.submit_ticket": "提交工单", "support.submit_title": "提交工单",
        "support.submit_sub": "我们会尽快回复您。",
    },
    
    "ms": {  # Bahasa Melayu
        "nav.dashboard": "Papan Pemuka", "nav.rewards": "Ganjaran", "nav.profile": "Profil",
        "nav.settings": "Tetapan", "nav.support": "Sokongan", "nav.logout": "Log Keluar",
        "nav.learn": "Belajar", "nav.create": "Cipta", "nav.chat": "Sembang",
        "nav.view_progress": "Lihat kemajuan", "nav.browse_courses": "Semak kursus",
        "nav.view_templates": "Lihat Templat", "nav.create_course": "Buat kursus baru",
        "nav.create_folder": "Buat folder", "nav.admin_login": "Log Masuk Admin",
        "nav.notifications": "Pemberitahuan",
        "home.jump_back": "Teruskan", "home.pick_up": "Sambung dari tempat anda berhenti...",
        "home.learn_courses": "Kursus pembelajaran:", "home.your_creations": "Ciptaan anda:",
        "home.no_courses": "Belum ada kursus dimulakan. Semak kursus untuk mula!",
        "home.no_templates": "Belum ada templat dimulakan. Semak templat untuk mula mencipta!",
        "home.think_like": "Kami fikir anda mungkin suka ini", "home.based_interests": "Berdasarkan minat anda",
        "home.latest": "Terbaru daripada kami", "home.explore_new": "Terokai kursus dan templat baru",
        "home.see_others": "Lihat apa yang orang lain cipta", "home.based_topics": "Berdasarkan topik yang anda kerjakan",
        "home.view_all": "Lihat semua", "home.courses": "Kursus:", "home.templates": "Templat:",
        "home.my_collections": "Koleksi saya", "home.organize": "Susun kursus dan templat anda",
        "home.liked_courses": "Kursus Disukai", "home.watch_later": "Tonton Kemudian",
        "home.liked_templates": "Templat Disukai", "home.use_later": "Guna Kemudian",
        "home.new_folder": "Folder Baru", "home.welcome": "Selamat datang",
        "home.start_journey": "Mulakan perjalanan pembelajaran dan penciptaan anda hari ini",
        "notif.title": "Pemberitahuan", "notif.subtitle": "Kemas kini dan peringatan terkini anda.",
        "notif.no_notifications": "Anda tidak mempunyai pemberitahuan.",
        "notif.send_all": "Hantar pemberitahuan kepada semua akaun", "notif.notif_title": "Tajuk pemberitahuan",
        "notif.write_msg": "Tulis mesej untuk semua pengguna", "notif.send_btn": "Hantar kepada semua pengguna",
        "common.points": "Mata Sarang", "common.search": "Cari", "common.save": "Simpan",
        "common.cancel": "Batal", "common.confirm": "Sahkan", "common.submit": "Hantar",
        "common.purchase": "Beli", "common.owned": "Dimiliki", "common.close": "Tutup",
        "settings.title": "Tetapan", "settings.subtitle": "Urus keutamaan dan keselamatan anda",
        "settings.success": "Tetapan disimpan",
        "settings.language": "Bahasa", "settings.display_lang": "Bahasa Paparan",
        "settings.lang_desc": "Pilih bahasa pilihan anda untuk antara muka.",
        "settings.privacy": "Privasi", "settings.profile_vis": "Keterlihatan Profil",
        "settings.public": "Awam", "settings.friends": "Rakan Sahaja", "settings.private": "Peribadi",
        "settings.activity": "Status Aktiviti", "settings.activity_desc": "Tunjukkan bila anda aktif.",
        "settings.security": "Keselamatan Akaun", "settings.change_pw": "Tukar Kata Laluan",
        "settings.curr_pw": "Kata Laluan Semasa", "settings.new_pw": "Kata Laluan Baru",
        "settings.conf_pw": "Sahkan Kata Laluan", "settings.update_pw": "Kemaskini Kata Laluan",
        "settings.2fa": "Pengesahan Dua Faktor", "settings.2fa_desc": "Lindungi akaun anda dengan SingPass.",
        "settings.enable_singpass": "Aktifkan dengan SingPass", "settings.singpass_connected": "SingPass Disambungkan",
        "settings.disconnect": "Putuskan Sambungan",
        "settings.audio": "Ciri Audio", "settings.sfx": "Kesan Bunyi",
        "settings.sfx_desc": "Mainkan bunyi untuk pemberitahuan dan tindakan.",
        "settings.tts": "Teks kepada Ucapan", "settings.tts_desc": "Serlahkan teks untuk mendengarnya dibaca.",
        "settings.visual": "Visual & Paparan", "settings.dark_mode": "Mod Gelap",
        "settings.dark_desc": "Mengurangkan ketegangan mata dalam persekitaran cahaya rendah.",
        "settings.high_contrast": "Kontras Tinggi", "settings.high_desc": "Meningkatkan kontras untuk keterlihatan yang lebih baik.",
        "settings.font_size": "Saiz Fon", "settings.fs_std": "Standard", "settings.fs_lg": "Besar",
        "settings.fs_xl": "Sangat Besar",
        "settings.system": "Tindakan Sistem", "settings.reset": "Tetapkan Semula Semua Tetapan",
        "settings.reset_desc": "Pulihkan konfigurasi lalai.", "settings.reset_btn": "Tetapkan Semula",
        "rewards.title": "Kedai Ganjaran", "rewards.subtitle": "Tukar mata anda untuk item.",
        "rewards.balance": "Baki Anda", "rewards.shop": "Kedai", "rewards.quests": "Misi",
        "support.title": "Pusat Sokongan", "support.subtitle": "Dapatkan bantuan, semak Soalan Lazim atau hantar tiket",
        "support.faq": "Soalan Lazim", "support.submit": "Hantar Tiket", "support.history": "Tiket Saya",
        "support.search_faq": "Cari Soalan Lazim...", "support.contact": "Hubungi",
        "support.help_center": "Pusat Bantuan", "support.feedback": "Maklum Balas",
        
        "profile.title": "Profil", "profile.edit": "Edit", "profile.settings": "Tetapan",
        "profile.points": "Mata", "profile.streak": "Rentetan", "profile.active": "Aktif Sekarang",
        "profile.inventory": "Inventori Saya", "profile.title_items": "Gelaran",
        "profile.decorations": "Hiasan Avatar", "profile.effects": "Kesan Profil",
        "profile.equip": "Pakai", "profile.equipped": "Dipakai", "profile.no_items": "Anda tidak mempunyai",
        "profile.browse_shop": "Layari Kedai",
        
        "rewards.title": "Kedai Ganjaran", "rewards.subtitle": "Tukar mata anda untuk item.",
        "rewards.balance": "Baki Anda", "rewards.shop": "Kedai", "rewards.quests": "Misi",
        "rewards.all_items": "Semua Item", "rewards.decorations": "Hiasan",
        "rewards.profile_effects": "Kesan Profil", "rewards.chat_effects": "Kesan Sembang",
        "rewards.nameplates": "Papan Nama", "rewards.bundles": "Berkas",
        "rewards.purchase": "Beli", "rewards.owned": "Dimiliki",
        "rewards.legendary": "LEGENDA", "rewards.epic": "EPIK", "rewards.rare": "JARANG",
        "rewards.common": "BIASA", "rewards.exclusive": "Eksklusif",
        "rewards.quest_watch": "Tonton untuk Dapatkan Mata", "rewards.quest_claim": "Tuntut",
        "rewards.quest_watch_msg": "Tonton video untuk buka ganjaran",
        "rewards.quest_timer": "baki untuk buka ganjaran", "rewards.quest_complete": "Video selesai! Tuntut ganjaran anda.",
        "rewards.quest_claimed": "Dituntut!", "rewards.quest_claiming": "Menuntut...",
        
        "social.feed": "Suapan", "social.explore": "Terokai", "social.saved": "Disimpan",
        "social.communities": "Komuniti Saya", "social.join": "Sertai Sarang Baru",
        "social.whats_happening": "Apa yang berlaku?", "social.post": "Pos",
        "social.media": "Media", "social.achievement": "Pencapaian",
        "social.likes": "Suka", "social.comments": "Komen",
        "social.members_online": "Ahli Dalam Talian", "social.member": "Ahli",
        "social.completed_course": "KURSUS SELESAI", "social.chat": "Sembang",
        
        "courses.all": "Semua Kursus", "courses.in_progress": "Dalam Kemajuan",
        "courses.history": "Sejarah", "courses.recommended": "Disyorkan",
        "courses.browse": "Layari Kursus", "courses.search": "Cari kursus...",
        "courses.start": "Mula Kursus", "courses.continue": "Teruskan",
        "courses.completed": "Selesai",
        
        "footer.tagline": "Menghubungkan generasi melalui ilmu bersama",
        "footer.platform": "Platform", "footer.resources": "Sumber", "footer.legal": "Undang-undang",
        "footer.about": "Tentang Kami", "footer.dashboard": "Papan Pemuka",
        "footer.safety": "Petua Keselamatan", "footer.community": "Garis Panduan Komuniti",
        "footer.accessibility": "Kebolehcapaian", "footer.help_center": "Pusat Bantuan",
        "footer.contact": "Hubungi", "footer.feedback": "Maklum Balas",
        "footer.privacy": "Dasar Privasi", "footer.terms": "Terma Perkhidmatan",
        "footer.copyright": "© 2025 BridgeHive. Dibuat di Singapura.",

        # Homepage
        "home.welcome": "Selamat datang", "home.welcome_back": "Selamat kembali",
        "home.start_journey": "Mulakan perjalanan pembelajaran dan penciptaan anda hari ini",
        "home.jump_back": "Sambung semula", "home.pick_up": "Sambung dari tempat anda berhenti...",
        "home.learn_courses": "Kursus pembelajaran:", "home.your_creations": "Ciptaan anda:",
        "home.no_courses": "Belum memulakan sebarang kursus. Layari kursus untuk bermula!",
        "home.no_templates": "Belum memulakan sebarang templat. Layari templat untuk mula mencipta!",
        "home.may_like": "Kami rasa anda mungkin menyukai ini", "home.courses": "Kursus:",
        "home.templates": "Templat:", "home.latest": "Terbaru daripada kami",
        "home.explore_new": "Terokai kursus dan templat baharu",
        "home.others_creating": "Lihat apa yang orang lain sedang cipta",
        "home.based_on": "Berdasarkan topik yang anda sedang pelajari",
        "home.collections": "Koleksi saya", "home.organize": "Susun kursus dan templat anda",
        "home.view_all": "Lihat semua", "home.new_folder": "Folder Baharu",
        "home.liked_courses": "Kursus Disukai", "home.watch_later": "Tonton Kemudian",
        "home.liked_templates": "Templat Disukai", "home.use_later": "Guna Kemudian",
        "home.based_interests": "Berdasarkan minat anda",
        "nav.view_progress": "Lihat kemajuan", "nav.browse_courses": "Layari kursus",
        "nav.view_templates": "Lihat Templat", "nav.create_course": "Buat kursus baharu",
        "nav.create_folder": "Buat folder", "nav.notifications": "Pemberitahuan",
        "nav.admin_login": "Log Masuk Admin",
        "notif.title": "Pemberitahuan", "notif.subtitle": "Kemas kini dan peringatan terkini anda.",
        "notif.none": "Anda tiada pemberitahuan.", "notif.send_all": "Hantar pemberitahuan ke semua akaun",
        "notif.send_btn": "Hantar kepada semua pengguna", "notif.notif_title": "Tajuk pemberitahuan",
        "notif.write_msg": "Tulis mesej anda untuk semua pengguna",
        "support.no_tickets": "Tiada tiket lagi",
        "support.ticket_desc": "Anda belum menghantar sebarang tiket sokongan",
        "support.first_ticket": "Hantar Tiket Pertama Anda",
        "support.category": "Kategori", "support.select_cat": "Pilih kategori",
        "support.subject": "Subjek", "support.brief_desc": "Penerangan ringkas",
        "support.message": "Mesej", "support.detail_desc": "Huraikan masalah anda secara terperinci...",
        "support.submit_ticket": "Hantar Tiket", "support.submit_title": "Hantar Tiket",
        "support.submit_sub": "Kami akan membalas anda secepat mungkin.",
    },
    
    "ta": {  # Tamil
        "nav.dashboard": "டாஷ்போர்டு", "nav.rewards": "வெகுமதிகள்", "nav.profile": "சுயவிவரம்",
        "nav.settings": "அமைப்புகள்", "nav.support": "ஆதரவு", "nav.logout": "வெளியேறு",
        "nav.learn": "கற்றல்", "nav.create": "உருவாக்கு", "nav.chat": "அரட்டை",
        "common.points": "ஹைவ் புள்ளிகள்", "common.search": "தேடு", "common.save": "சேமி",
        "common.cancel": "ரத்து செய்", "common.confirm": "உறுதிப்படுத்து", "common.submit": "சமர்ப்பி",
        "common.purchase": "வாங்கு", "common.owned": "சொந்தமானது", "common.close": "மூடு",
        "settings.title": "அமைப்புகள்", "settings.subtitle": "உங்கள் விருப்பங்களையும் பாதுகாப்பையும் நிர்வகிக்கவும்",
        "settings.success": "அமைப்புகள் சேமிக்கப்பட்டன",
        "settings.language": "மொழி", "settings.display_lang": "காட்சி மொழி",
        "settings.lang_desc": "இடைமுகத்திற்கான உங்கள் விருப்பமான மொழியைத் தேர்ந்தெடுக்கவும்.",
        "settings.privacy": "தனியுரிமை", "settings.profile_vis": "சுயவிவர தெரிவு",
        "settings.public": "பொது", "settings.friends": "நண்பர்கள் மட்டும்", "settings.private": "தனிப்பட்ட",
        "settings.activity": "செயல்பாடு நிலை", "settings.activity_desc": "நீங்கள் செயலில் இருக்கும்போது காட்டு.",
        "settings.security": "கணக்கு பாதுகாப்பு", "settings.change_pw": "கடவுச்சொல் மாற்று",
        "settings.curr_pw": "தற்போதைய கடவுச்சொல்", "settings.new_pw": "புதிய கடவுச்சொல்",
        "settings.conf_pw": "கடவுச்சொல் உறுதிப்படுத்து", "settings.update_pw": "கடவுச்சொல் புதுப்பி",
        "settings.2fa": "இரு காரணி அங்கீகாரம்", "settings.2fa_desc": "SingPass மூலம் கணக்கை பாதுகாக்கவும்.",
        "settings.enable_singpass": "SingPass மூலம் இயக்கு", "settings.singpass_connected": "SingPass இணைக்கப்பட்டது",
        "settings.disconnect": "துண்டிக்கவும்",
        "settings.audio": "ஆடியோ அம்சங்கள்", "settings.sfx": "ஒலி விளைவுகள்",
        "settings.sfx_desc": "அறிவிப்புகளுக்கு ஒலி இயக்கவும்.",
        "settings.tts": "உரை-முதல்-பேச்சு", "settings.tts_desc": "உரையை தேர்ந்தெடுத்து சத்தமாக கேளுங்கள்.",
        "settings.visual": "காட்சி & திரை", "settings.dark_mode": "இருண்ட பயன்முறை",
        "settings.dark_desc": "குறைந்த வெளிச்சத்தில் கண் அழுத்தத்தை குறைக்கவும்.",
        "settings.high_contrast": "அதிக மாறுபாடு", "settings.high_desc": "சிறந்த தெரிவுக்கு மாறுபாட்டை அதிகரிக்கவும்.",
        "settings.font_size": "எழுத்துரு அளவு", "settings.fs_std": "நிலையான", "settings.fs_lg": "பெரியது",
        "settings.fs_xl": "மிகவும் பெரியது",
        "settings.system": "கணினி செயல்கள்", "settings.reset": "அனைத்து அமைப்புகளையும் மீட்டமை",
        "settings.reset_desc": "இயல்புநிலை கட்டமைப்பை மீட்டமைக்கவும்.", "settings.reset_btn": "மீட்டமை",
        "rewards.title": "வெகுமதி கடை", "rewards.subtitle": "உங்கள் புள்ளிகளை பொருட்களுக்கு மாற்றவும்.",
        "rewards.balance": "உங்கள் இருப்பு", "rewards.shop": "கடை", "rewards.quests": "பணிகள்",
        "support.title": "ஆதரவு மையம்", "support.subtitle": "உதவி பெறவும், அடிக்கடி கேட்கப்படும் கேள்விகளை பார்க்கவும் அல்லது டிக்கெட் சமர்ப்பிக்கவும்",
        "support.faq": "அடிக்கடி கேட்கப்படும் கேள்விகள்", "support.submit": "டிக்கெட் சமர்ப்பி",
        "support.history": "என் டிக்கெட்டுகள்",
        "support.search_faq": "கேள்விகளைத் தேடு...", "support.contact": "தொடர்பு",
        "support.help_center": "உதவி மையம்", "support.feedback": "கருத்து",
        
        "profile.title": "சுயவிவரம்", "profile.edit": "திருத்து", "profile.settings": "அமைப்புகள்",
        "profile.points": "புள்ளிகள்", "profile.streak": "தொடர்ச்சி", "profile.active": "இப்போது செயலில்",
        "profile.inventory": "என் பொருட்கள்", "profile.title_items": "தலைப்பு",
        "profile.decorations": "அவதார் அலங்காரம்", "profile.effects": "சுயவிவர விளைவுகள்",
        "profile.equip": "அணி", "profile.equipped": "அணிந்துள்ளது", "profile.no_items": "உங்களிடம் இல்லை",
        "profile.browse_shop": "கடையைப் பார்க்க",
        
        "rewards.title": "வெகுமதி கடை", "rewards.subtitle": "உங்கள் புள்ளிகளை பொருட்களுக்கு மாற்றவும்.",
        "rewards.balance": "உங்கள் இருப்பு", "rewards.shop": "கடை", "rewards.quests": "பணிகள்",
        "rewards.all_items": "அனைத்து பொருட்கள்", "rewards.decorations": "அலங்காரங்கள்",
        "rewards.profile_effects": "சுயவிவர விளைவுகள்", "rewards.chat_effects": "அரட்டை விளைவுகள்",
        "rewards.nameplates": "பெயர் பலகைகள்", "rewards.bundles": "தொகுப்புகள்",
        "rewards.purchase": "வாங்கு", "rewards.owned": "சொந்தமானது",
        "rewards.legendary": "புராண", "rewards.epic": "காவியம்", "rewards.rare": "அரிதான",
        "rewards.common": "பொதுவான", "rewards.exclusive": "பிரத்யேகமான",
        "rewards.quest_watch": "புள்ளிகள் பெற பார்க்கவும்", "rewards.quest_claim": "பெறு",
        "rewards.quest_watch_msg": "வெகுமதியைத் திறக்க வீடியோவைப் பார்க்கவும்",
        "rewards.quest_timer": "வெகுமதி திறக்க மீதம்", "rewards.quest_complete": "வீடியோ முடிந்தது! உங்கள் வெகுமதியைப் பெறுங்கள்.",
        "rewards.quest_claimed": "பெறப்பட்டது!", "rewards.quest_claiming": "பெறுகிறது...",
        
        "social.feed": "ஊட்டம்", "social.explore": "ஆராய்", "social.saved": "சேமித்தவை",
        "social.communities": "என் சமூகங்கள்", "social.join": "புதிய தேன்கூடு சேர",
        "social.whats_happening": "என்ன நடக்கிறது?", "social.post": "இடுகை",
        "social.media": "ஊடகம்", "social.achievement": "சாதனை",
        "social.likes": "விருப்பங்கள்", "social.comments": "கருத்துகள்",
        "social.members_online": "ஆன்லைன் உறுப்பினர்கள்", "social.member": "உறுப்பினர்",
        "social.completed_course": "பாடம் முடிந்தது", "social.chat": "அரட்டை",
        
        "courses.all": "அனைத்து பாடங்கள்", "courses.in_progress": "முன்னேற்றத்தில்",
        "courses.history": "வரலாறு", "courses.recommended": "பரிந்துரைக்கப்பட்டது",
        "courses.browse": "பாடங்களைப் பார்க்க", "courses.search": "பாடங்களைத் தேடு...",
        "courses.start": "பாடம் தொடங்கு", "courses.continue": "தொடர்",
        "courses.completed": "முடிந்தது",
        
        "footer.tagline": "பகிர்ந்த அறிவின் மூலம் தலைமுறைகளை இணைக்கிறோம்",
        "footer.platform": "தளம்", "footer.resources": "வளங்கள்", "footer.legal": "சட்டம்",
        "footer.about": "எங்களை பற்றி", "footer.dashboard": "டாஷ்போர்டு",
        "footer.safety": "பாதுகாப்பு உதவிக்குறிப்புகள்", "footer.community": "சமூக வழிகாட்டுதல்கள்",
        "footer.accessibility": "அணுகல்தன்மை", "footer.help_center": "உதவி மையம்",
        "footer.contact": "தொடர்பு", "footer.feedback": "கருத்து",
        "footer.privacy": "தனியுரிமை கொள்கை", "footer.terms": "சேவை விதிமுறைகள்",
        "footer.copyright": "© 2025 BridgeHive. சிங்கப்பூரில் தயாரிக்கப்பட்டது.",

        # Homepage
        "home.welcome": "வணக்கம்", "home.welcome_back": "மீண்டும் வருக",
        "home.start_journey": "இன்று உங்கள் கற்றல் பயணத்தை தொடங்குங்கள்",
        "home.jump_back": "மீண்டும் தொடங்கு", "home.pick_up": "நீங்கள் நிறுத்திய இடத்திலிருந்து தொடரவும்...",
        "home.learn_courses": "பாடநெறிகளை கற்கவும்:", "home.your_creations": "உங்கள் படைப்புகள்:",
        "home.no_courses": "இன்னும் பாடநெறி தொடங்கவில்லை. பாடநெறிகளை தேடுங்கள்!",
        "home.no_templates": "இன்னும் டெம்ப்ளேட் தொடங்கவில்லை. டெம்ப்ளேட்களை தேடுங்கள்!",
        "home.may_like": "நீங்கள் இவற்றை விரும்புவீர்கள்", "home.courses": "பாடநெறிகள்:",
        "home.templates": "டெம்ப்ளேட்கள்:", "home.latest": "எங்களிடமிருந்து புதியவை",
        "home.explore_new": "புதிய பாடநெறிகள் மற்றும் டெம்ப்ளேட்களை கண்டறியுங்கள்",
        "home.others_creating": "மற்றவர்கள் என்ன உருவாக்குகிறார்கள்",
        "home.based_on": "நீங்கள் படிக்கும் தலைப்புகளின் அடிப்படையில்",
        "home.collections": "என் தொகுப்புகள்", "home.organize": "உங்கள் பாடநெறிகள் மற்றும் டெம்ப்ளேட்களை ஒழுங்கமையுங்கள்",
        "home.view_all": "அனைத்தும் காண", "home.new_folder": "புதிய கோப்புறை",
        "home.liked_courses": "விரும்பிய பாடநெறிகள்", "home.watch_later": "பிறகு பார்க்க",
        "home.liked_templates": "விரும்பிய டெம்ப்ளேட்கள்", "home.use_later": "பிறகு பயன்படுத்த",
        "home.based_interests": "உங்கள் ஆர்வங்களின் அடிப்படையில்",
        "home.think_like": "நீங்கள் இவற்றை விரும்புவீர்கள்",
        "home.see_others": "மற்றவர்கள் என்ன உருவாக்குகிறார்கள்",
        "home.my_collections": "என் தொகுப்புகள்",
        "home.based_topics": "நீங்கள் படிக்கும் தலைப்புகளின் அடிப்படையில்",
        "nav.view_progress": "முன்னேற்றம் காண", "nav.browse_courses": "பாடநெறிகள் தேடு",
        "nav.view_templates": "டெம்ப்ளேட்கள் காண", "nav.create_course": "புதிய பாடநெறி",
        "nav.create_folder": "கோப்புறை உருவாக்கு", "nav.notifications": "அறிவிப்புகள்",
        "nav.admin_login": "நிர்வாக உள்நுழைவு",
        "notif.title": "அறிவிப்புகள்", "notif.subtitle": "உங்கள் சமீபத்திய புதுப்பிப்புகள்.",
        "notif.none": "அறிவிப்புகள் இல்லை.", "notif.send_all": "அனைவருக்கும் அறிவிப்பு அனுப்பு",
        "notif.send_btn": "அனைத்து பயனர்களுக்கும் அனுப்பு", "notif.notif_title": "அறிவிப்பு தலைப்பு",
        "notif.write_msg": "அனைத்து பயனர்களுக்கும் செய்தி எழுதுங்கள்",
        "support.no_tickets": "டிக்கெட்கள் இல்லை",
        "support.ticket_desc": "நீங்கள் டிக்கெட் சமர்ப்பிக்கவில்லை",
        "support.first_ticket": "முதல் டிக்கெட் சமர்ப்பிக்கவும்",
        "support.category": "வகை", "support.select_cat": "வகையை தேர்ந்தெடுக்கவும்",
        "support.subject": "பொருள்", "support.brief_desc": "சுருக்கமான விளக்கம்",
        "support.message": "செய்தி", "support.detail_desc": "உங்கள் சிக்கலை விவரிக்கவும்...",
        "support.submit_ticket": "டிக்கெட் சமர்ப்பி", "support.submit_title": "டிக்கெட் சமர்ப்பி",
        "support.submit_sub": "நாங்கள் விரைவில் பதிலளிப்போம்.",
    }
}

def translate(key, locale='en'):
    """Get translation for key in specified locale"""
    return TRANSLATIONS.get(locale, {}).get(key, TRANSLATIONS['en'].get(key, key))

# --- PUT YOUR GEMINI API KEY HERE ---
GEMINI_API_KEY = "AIzaSyCQaFzVGWC8IVav7MCHeRmUxo2qOPP-yW4"  # Replace with your actual API key from https://aistudio.google.com/app/apikey

# System prompt - this tells the AI how to behave and what to answer
# The AI will follow these instructions for every conversation
BRIDGEBOT_SYSTEM_PROMPT = """You are BridgeBot, the friendly AI assistant for BridgeHive - an intergenerational learning platform that connects youth and seniors in Singapore through shared learning experiences.

YOUR PURPOSE:
- Help users discover and choose courses on BridgeHive
- Suggest course ideas based on user interests
- Provide tips on how to learn effectively
- Help with course creation ideas for those who want to teach
- Answer questions about intergenerational learning and connection
- Guide users on how to use the BridgeHive platform

TOPICS YOU CAN HELP WITH:
1. Course recommendations (e.g., "What cooking course should I take?")
2. Learning tips and strategies (e.g., "How can I learn technology faster?")
3. Course creation ideas (e.g., "I want to teach seniors, what should I create?")
4. Intergenerational connection advice (e.g., "How can I connect better with elders?")
5. Platform guidance (e.g., "How do I save a course to my folder?")
6. Skill development suggestions (e.g., "What skills are good for seniors to learn?")

AVAILABLE COURSE CATEGORIES ON BRIDGEHIVE:
- Cooking (Traditional Peranakan cuisine, family recipes)
- Technology (Social media, Excel, AI & Machine Learning)
- Language (Conversational Malay, cultural phrases)
- Sports & Fitness (Football tactics, physical wellness)
- Arts & Creativity (Photography, creative writing)
- Health & Wellness (Mindfulness, meditation, stress reduction)
- Gardening (Home gardening, urban farming, composting)
- Finance (Personal finance, investing, retirement planning)

STRICT RULES - YOU MUST FOLLOW THESE:
1. ONLY answer questions related to learning, courses, teaching, skills, or intergenerational connection
2. If someone asks an unrelated question (like "what's the weather" or "what should I eat"), politely redirect them
3. Keep responses friendly, warm, and encouraging
4. Use simple language that both youth and seniors can understand
5. Keep responses concise (2-4 paragraphs max)
6. When suggesting courses, mention specific categories available on BridgeHive

EXAMPLE OF REDIRECTING OFF-TOPIC QUESTIONS:
User: "What should I eat for dinner?"
You: "I'm here to help you with learning and courses on BridgeHive! 😊 If you're interested in food, why not check out our Cooking course - Traditional Peranakan Cooking by Mrs. Wong Mei Ling? You'll learn to make Laksa and Kueh Pie Tee! Would you like me to suggest some courses based on your interests?"

Always be helpful, positive, and guide users back to learning topics!"""

# ============================================================================
# Each class = one table in the database
# Using SQLAlchemy ORM so I can work with Python objects instead of SQL queries
# ============================================================================

# --- FAQ MODEL ---
# Stores frequently asked questions shown on landing page and search overlay
# Supports CRUD operations through admin panel
class FAQ(db.Model):
    __tablename__ = 'faqs'
    id = db.Column(db.Integer, primary_key=True)  # Auto-incrementing ID
    question = db.Column(db.Text, nullable=False)  # The question text
    answer = db.Column(db.Text, nullable=False)    # The answer text
    category = db.Column(db.String(50), nullable=False)  # e.g., General, Account, Courses
    is_active = db.Column(db.Boolean, default=True)  # Can hide FAQs without deleting
    view_count = db.Column(db.Integer, default=0)    # Track how many times viewed
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# --- USER MODEL ---
# Stores registered users (both youth and seniors)
# Contains onboarding data from the multi-step signup wizard
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)  # Must be unique
    password = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(10), nullable=False)  # 'youth' or 'elder'
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    streak_days = db.Column(db.Integer, default=0)  # For gamification on homepage
    hive_points = db.Column(db.Integer, default=5000)  # Points for navbar display and rewards shop
    is_new_user = db.Column(db.Boolean, default=True)  # Shows different welcome message
    profile_pic = db.Column(db.String(200), default='DefaultPFP.png')  # Profile picture filename
    
    # Onboarding Data - collected during signup wizard
    role = db.Column(db.String(50))        # learner, mentor, or both
    age_group = db.Column(db.String(20))   # Age range selected
    tech_comfort = db.Column(db.String(20))  # How comfortable with tech
    learning_interests = db.Column(db.Text)   # Comma-separated interests
    teaching_interests = db.Column(db.Text)   # What they can teach
    
    # Relationships
    settings = db.relationship('UserSettings', backref='user', uselist=False, cascade='all,delete-orphan')
    inventory = db.relationship('UserItem', backref='user', cascade='all,delete-orphan')


# --- USER SETTINGS MODEL ---
# Stores user preferences for language, visual, audio, and privacy settings
class UserSettings(db.Model):
    __tablename__ = 'user_settings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    language = db.Column(db.String(5), default='en')
    profile_visibility = db.Column(db.String(20), default='public')
    show_activity = db.Column(db.Boolean, default=True)
    singpass_linked = db.Column(db.Boolean, default=False)
    sound_effects = db.Column(db.Boolean, default=False)
    text_to_speech = db.Column(db.Boolean, default=False)
    dark_mode = db.Column(db.Boolean, default=False)
    high_contrast = db.Column(db.Boolean, default=False)
    font_size = db.Column(db.String(20), default='standard')


# --- FOLDER MODEL ---
# User-created collections to organize saved courses
# Like playlists but for courses
class Folder(db.Model):
    __tablename__ = 'folders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Who owns it
    folder_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    folder_type = db.Column(db.String(20), default='custom')  # 'preset' for default folders
    icon = db.Column(db.String(50), default='folder')  # Bootstrap icon name
    color = db.Column(db.String(7), default='#ECD9B9')  # Hex color for card
    is_deletable = db.Column(db.Boolean, default=True)  # Preset folders can't be deleted
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# --- COURSE MODEL ---
# All available courses on the platform
class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    instructor_name = db.Column(db.String(100))
    category = db.Column(db.String(50))  # Used for recommendations matching
    color = db.Column(db.String(7), default='#FEFAF1')  # Card background color
    library_id = db.Column(db.Integer)  # Maps to course ID in courses library (port 8080)
    image_url = db.Column(db.String(500))  # Course image URL from courses library
    date_created = db.Column(db.DateTime, default=datetime.utcnow)


# --- USER PROGRESS MODEL ---
# Tracks which courses each user has started and their progress
# Used for "Jump Back In" section on homepage
class UserProgress(db.Model):
    __tablename__ = 'user_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    progress_percent = db.Column(db.Integer, default=0)  # 0-100
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)


# --- FOLDER-COURSE MODEL ---
# Junction table for many-to-many relationship
# One folder can have many courses, one course can be in many folders
class FolderCourse(db.Model):
    __tablename__ = 'folder_courses'
    id = db.Column(db.Integer, primary_key=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)


# --- TEMPLATE MODEL ---
# Templates for mentors to use when creating courses
# Similar to Course but used in mentor interface
class Template(db.Model):
    __tablename__ = 'templates'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # Same categories as courses
    color = db.Column(db.String(7), default='#FEFAF1')
    usage_count = db.Column(db.Integer, default=0)  # Track popularity
    date_created = db.Column(db.DateTime, default=datetime.utcnow)


# --- TEMPLATE PROGRESS MODEL ---
# Tracks which templates each mentor has started using
# Used for "Jump Back In" section on mentor homepage
class TemplateProgress(db.Model):
    __tablename__ = 'template_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), nullable=False)
    progress_percent = db.Column(db.Integer, default=0)  # 0-100
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)


# --- FOLDER-TEMPLATE MODEL ---
# Junction table for mentors to save templates to folders
class FolderTemplate(db.Model):
    __tablename__ = 'folder_templates'
    id = db.Column(db.Integer, primary_key=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)


# --- ADMIN MODEL ---
# Separate login for admin panel (not regular users)
# Password is hashed for security
class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


# --- CONTACT MESSAGE MODEL ---
# Stores messages submitted through contact form
# Admin can view/delete these in admin panel
class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)  # Track if admin has read it
    date_created = db.Column(db.DateTime, default=datetime.utcnow)


# --- BROADCAST NOTIFICATION MODEL ---
# Stores admin broadcast notifications sent to all users
class BroadcastNotification(db.Model):
    __tablename__ = 'broadcast_notifications'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.String(50), default='admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# --- SUPPORT TICKET MODEL ---
# Stores user support tickets for the support page
class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# --- SHOP ITEM MODEL ---
# Items available for purchase in the rewards shop
class ShopItem(db.Model):
    __tablename__ = 'shop_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    rarity = db.Column(db.String(20), default='common')
    icon = db.Column(db.String(50))
    image = db.Column(db.String(200))
    
    @property
    def icon_class(self):
        """Alias for icon field for template compatibility"""
        return self.icon


# --- USER ITEM MODEL ---
# Items owned by users (purchased from shop)
class UserItem(db.Model):
    __tablename__ = 'user_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('shop_items.id'), nullable=False)
    is_equipped = db.Column(db.Boolean, default=False)
    acquired_at = db.Column(db.DateTime, default=datetime.utcnow)
    item = db.relationship('ShopItem')


# --- USER TITLE MODEL ---
# Titles earned by users based on achievements
class UserTitle(db.Model):
    __tablename__ = 'user_titles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title_name = db.Column(db.String(100), nullable=False)
    title_rarity = db.Column(db.String(20), default='common')
    required_streak = db.Column(db.Integer, default=0)
    is_equipped = db.Column(db.Boolean, default=False)
    acquired_date = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='titles')


# --- QUEST MODEL ---
# Quests users can complete to earn points
class Quest(db.Model):
    __tablename__ = 'quests'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    reward_points = db.Column(db.Integer, default=0)
    banner_image = db.Column(db.String(500))
    video_url = db.Column(db.String(500))
    promoted_by = db.Column(db.String(100))
    ends_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)


# --- QUEST COMPLETION MODEL ---
# Tracks which quests users have completed
class QuestCompletion(db.Model):
    __tablename__ = 'quest_completions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quest_id = db.Column(db.Integer, db.ForeignKey('quests.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    quest = db.relationship('Quest')


# --- VIDEO PROGRESS MODEL ---
# Tracks user progress watching quest videos
class VideoProgress(db.Model):
    __tablename__ = 'video_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quest_id = db.Column(db.Integer, db.ForeignKey('quests.id'), nullable=False)
    watched_duration = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)


# --- CHAT CONVERSATION MODEL ---
# Stores each chatbot conversation session
# Users can have multiple conversations and switch between them
class ChatConversation(db.Model):
    __tablename__ = 'chat_conversations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), default='New Chat')  # Auto-generated from first message
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to get all messages in this conversation
    messages = db.relationship('ChatMessage', backref='conversation', lazy=True, cascade='all, delete-orphan')


# --- CHAT MESSAGE MODEL ---
# Stores individual messages within a conversation
# Each message is either from 'user' or 'bot'
class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversations.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'bot'
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================================
# MAIN PAGE ROUTES
# These handle the main pages users see
# ============================================================================

# Inject current user into all templates (for unified navbar)
@app.context_processor
def inject_navbar_user():
    uid = session.get('user_id')
    current_user = None
    locale = 'en'
    body_classes = []
    tts_enabled = False
    user_settings = None
    
    if uid:
        current_user = User.query.get(uid)
        if current_user:
            # Ensure user has settings
            if not current_user.settings:
                current_user.settings = UserSettings(user_id=current_user.id)
                db.session.add(current_user.settings)
                db.session.commit()
            
            user_settings = current_user.settings
            
            # Get locale from settings
            locale = user_settings.language or 'en'
            
            # Build body classes for visual settings
            if user_settings.dark_mode:
                body_classes.append('dark-mode')
            if user_settings.high_contrast:
                body_classes.append('high-contrast')
            if user_settings.font_size == 'large':
                body_classes.append('font-large')
            elif user_settings.font_size == 'extra-large':
                body_classes.append('font-extra-large')
            
            # TTS state
            tts_enabled = user_settings.text_to_speech
    
    return dict(
        navbar_user=current_user,  # Use navbar_user to not override route's user variable
        t=lambda key: translate(key, locale),
        body_classes=' '.join(body_classes),
        tts_enabled=tts_enabled,
        current_locale=locale,
        user_settings=user_settings
    )


# --- LANDING PAGE ---
# First page visitors see, shows sign up options and FAQ search
@app.route('/')
def landing():
    faqs = FAQ.query.filter_by(is_active=True).all()  # Get all active FAQs for search
    return render_template('landing.html', faqs=faqs)


# --- STUDENT HOMEPAGE ---
# Main dashboard after login for learners, shows personalized content
@app.route('/student/home')
def student_homepage():
    # Get current user from session (defaults to user 1 for demo)
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    if not user:
        user = User.query.first()
    
    # Sync library courses from session to database
    if user and 'library_courses_accessed' in session:
        for lib_course_id_str, course_data in session.get('library_courses_accessed', {}).items():
            lib_course_id = int(lib_course_id_str)
            # Check if Course record already exists for this library course
            course = Course.query.filter_by(library_id=lib_course_id).first()
            if not course:
                course = Course(
                    title=course_data.get('title', 'Course'),
                    description=course_data.get('description'),
                    instructor_name=course_data.get('instructor_name'),
                    category=course_data.get('category'),
                    library_id=lib_course_id,
                    image_url=course_data.get('image_url')
                )
                db.session.add(course)
                db.session.commit()
            
            # Create or update UserProgress
            progress = UserProgress.query.filter_by(user_id=user.id, course_id=course.id).first()
            if not progress:
                progress = UserProgress(user_id=user.id, course_id=course.id, progress_percent=5)
            else:
                progress.progress_percent = max(progress.progress_percent, 5)
            progress.last_accessed = datetime.utcnow()
            db.session.add(progress)
        db.session.commit()
        # Clear the tracking data from session after syncing
        session.pop('library_courses_accessed', None)
    
    # Get user's folders with course counts for the collections section
    folders = Folder.query.filter_by(user_id=user.id if user else 1).all()
    folder_course_counts = {}
    for folder in folders:
        count = FolderCourse.query.filter_by(folder_id=folder.id).count()
        folder_course_counts[folder.id] = count
    
    # Get courses user has started - for "Jump Back In" carousel
    courses_in_progress = []
    in_progress_ids = []  # Keep track to exclude from other sections
    if user:
        progress_records = UserProgress.query.filter_by(user_id=user.id).order_by(UserProgress.last_accessed.desc()).all()
        for p in progress_records:
            course = Course.query.get(p.course_id)
            if course:
                courses_in_progress.append({
                    'course': course,
                    'progress': p.progress_percent
                })
                in_progress_ids.append(course.id)
    
    # Get recommended courses based on user's learning interests
    # Exclude courses already in progress to avoid duplicates
    recommended_courses = []
    if user and user.learning_interests:
        # Split comma-separated interests and find matching courses
        interests = [i.strip() for i in user.learning_interests.split(',')]
        for interest in interests:
            matching = Course.query.filter(Course.category.ilike(f'%{interest}%')).all()
            for course in matching:
                if course.id not in in_progress_ids and course not in recommended_courses:
                    recommended_courses.append(course)
    
    # If no interest-based recommendations, show all available courses
    if not recommended_courses:
        recommended_courses = Course.query.filter(~Course.id.in_(in_progress_ids)).all() if in_progress_ids else Course.query.all()
    
    # Get latest courses for "Explore New" section (also excluding in-progress)
    if in_progress_ids:
        all_courses = Course.query.filter(~Course.id.in_(in_progress_ids)).order_by(Course.date_created.desc()).all()
    else:
        all_courses = Course.query.order_by(Course.date_created.desc()).all()
    
    return render_template('homepage.html', 
                         user=user, 
                         folders=folders, 
                         folder_course_counts=folder_course_counts,
                         courses_in_progress=courses_in_progress,
                         recommended_courses=recommended_courses,
                         all_courses=all_courses)


# --- MENTOR HOMEPAGE ---
# Dashboard for mentors - shows templates instead of courses
# Similar layout but focused on course creation
@app.route('/mentor/home')
def mentor_homepage():
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    if not user:
        user = User.query.first()
    
    # Get user's folders with template counts
    folders = Folder.query.filter_by(user_id=user.id if user else 1).all()
    folder_template_counts = {}
    for folder in folders:
        count = FolderTemplate.query.filter_by(folder_id=folder.id).count()
        folder_template_counts[folder.id] = count
    
    # Get templates user has started - for "Jump Back In" section
    templates_in_progress = []
    in_progress_ids = []
    in_progress_categories = []  # Track categories for "See what others are creating"
    if user:
        progress_records = TemplateProgress.query.filter_by(user_id=user.id).order_by(TemplateProgress.last_accessed.desc()).all()
        for p in progress_records:
            template = Template.query.get(p.template_id)
            if template:
                templates_in_progress.append({
                    'template': template,
                    'progress': p.progress_percent
                })
                in_progress_ids.append(template.id)
                if template.category and template.category not in in_progress_categories:
                    in_progress_categories.append(template.category)
    
    # Get recommended templates based on user's teaching interests
    recommended_templates = []
    if user and user.teaching_interests:
        interests = [i.strip() for i in user.teaching_interests.split(',')]
        for interest in interests:
            matching = Template.query.filter(Template.category.ilike(f'%{interest}%')).all()
            for template in matching:
                if template.id not in in_progress_ids and template not in recommended_templates:
                    recommended_templates.append(template)
    
    # If no interest-based recommendations, show all templates
    if not recommended_templates:
        recommended_templates = Template.query.filter(~Template.id.in_(in_progress_ids)).all() if in_progress_ids else Template.query.all()
    
    # Get all templates for "Latest trendy templates" section
    if in_progress_ids:
        all_templates = Template.query.filter(~Template.id.in_(in_progress_ids)).order_by(Template.usage_count.desc()).all()
    else:
        all_templates = Template.query.order_by(Template.usage_count.desc()).all()
    
    # Get courses created by others based on in-progress template categories
    # This is for "See what others are creating" section
    related_courses = []
    if in_progress_categories:
        for category in in_progress_categories:
            matching_courses = Course.query.filter(Course.category.ilike(f'%{category}%')).all()
            for course in matching_courses:
                if course not in related_courses:
                    related_courses.append(course)
    
    return render_template('mentor_homepage.html',
                         user=user,
                         folders=folders,
                         folder_template_counts=folder_template_counts,
                         templates_in_progress=templates_in_progress,
                         recommended_templates=recommended_templates,
                         all_templates=all_templates,
                         related_courses=related_courses)


# --- VIEW TEMPLATE ---
# Opens template in view, creates/updates progress record
@app.route('/template/<int:template_id>')
def view_template(template_id):
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    template = Template.query.get_or_404(template_id)
    
    from_folder = request.args.get('from_folder')
    
    # Track progress - creates new record if first time viewing
    if user:
        progress = TemplateProgress.query.filter_by(user_id=user.id, template_id=template_id).first()
        if not progress:
            progress = TemplateProgress(user_id=user.id, template_id=template_id, progress_percent=5)
            db.session.add(progress)
            # Increment usage count
            template.usage_count += 1
        progress.last_accessed = datetime.utcnow()
        db.session.commit()
    
    # Get user's folders for "Add to Folder" dropdown
    folders = Folder.query.filter_by(user_id=user.id if user else 1).all()
    
    return render_template('template_view.html', template=template, user=user, folders=folders, from_folder=from_folder)


# --- ADD TEMPLATE TO FOLDER ---
@app.route('/folder/<int:folder_id>/add-template/<int:template_id>', methods=['POST'])
def add_template_to_folder(folder_id, template_id):
    user_id = session.get('user_id', 1)
    folder = Folder.query.get_or_404(folder_id)
    
    if folder.user_id != user_id:
        flash('Unauthorized', 'error')
        return redirect(url_for('both_homepage'))
    
    # Check if already in folder
    existing = FolderTemplate.query.filter_by(folder_id=folder_id, template_id=template_id).first()
    if not existing:
        folder_template = FolderTemplate(folder_id=folder_id, template_id=template_id)
        db.session.add(folder_template)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Template added to folder!'})
    else:
        return jsonify({'success': True, 'message': 'Template already in folder'})


# --- REMOVE TEMPLATE FROM FOLDER ---
@app.route('/folder/<int:folder_id>/remove-template/<int:template_id>', methods=['POST'])
def remove_template_from_folder(folder_id, template_id):
    user_id = session.get('user_id', 1)
    folder = Folder.query.get_or_404(folder_id)
    
    if folder.user_id != user_id:
        flash('Unauthorized', 'error')
        return redirect(url_for('both_homepage'))
    
    folder_template = FolderTemplate.query.filter_by(folder_id=folder_id, template_id=template_id).first()
    if folder_template:
        db.session.delete(folder_template)
        db.session.commit()
        flash('Template removed from folder', 'success')
    
    return redirect(url_for('mentor_folder_view', folder_id=folder_id))


# --- MENTOR FOLDER LIST ---
@app.route('/mentor/folders')
def mentor_folder_list():
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    if not user:
        user = User.query.first()
    
    folders = Folder.query.filter_by(user_id=user.id if user else 1).all()
    folder_template_counts = {}
    for folder in folders:
        count = FolderTemplate.query.filter_by(folder_id=folder.id).count()
        folder_template_counts[folder.id] = count
    
    return render_template('mentor_folder_list.html', user=user, folders=folders, folder_template_counts=folder_template_counts)


# --- MENTOR FOLDER VIEW ---
@app.route('/mentor/folders/<int:folder_id>')
def mentor_folder_view(folder_id):
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    folder = Folder.query.get_or_404(folder_id)
    
    # Get templates in this folder
    folder_templates = FolderTemplate.query.filter_by(folder_id=folder_id).all()
    templates = [Template.query.get(ft.template_id) for ft in folder_templates]
    templates = [t for t in templates if t]  # Filter out None
    
    return render_template('mentor_folder_view.html', user=user, folder=folder, templates=templates)


# --- ALL TEMPLATES PAGE ---
@app.route('/mentor/templates/all')
def all_templates_page():
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    templates = Template.query.order_by(Template.date_created.desc()).all()
    return render_template('templates_all.html', user=user, templates=templates)


# --- RECOMMENDED TEMPLATES PAGE ---
@app.route('/mentor/templates/recommended')
def recommended_templates_page():
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    
    recommended = []
    if user and user.teaching_interests:
        interests = [i.strip() for i in user.teaching_interests.split(',')]
        for interest in interests:
            matching = Template.query.filter(Template.category.ilike(f'%{interest}%')).all()
            for template in matching:
                if template not in recommended:
                    recommended.append(template)
    
    if not recommended:
        recommended = Template.query.all()
    
    return render_template('templates_recommended.html', user=user, templates=recommended)


# --- IN PROGRESS TEMPLATES PAGE ---
@app.route('/mentor/templates/in-progress')
def in_progress_templates_page():
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    
    templates_in_progress = []
    if user:
        progress_records = TemplateProgress.query.filter_by(user_id=user.id).order_by(TemplateProgress.last_accessed.desc()).all()
        for p in progress_records:
            template = Template.query.get(p.template_id)
            if template:
                templates_in_progress.append({
                    'template': template,
                    'progress': p.progress_percent
                })
    
    return render_template('templates_in_progress.html', user=user, templates_in_progress=templates_in_progress)


# --- CHATBOT PAGE ---
# AI chatbot interface for user assistance
# Shows list of past conversations and allows creating new ones
@app.route('/chat')
def chatbot():
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    if not user:
        user = User.query.first()
    
    # Get all conversations for this user, newest first
    conversations = ChatConversation.query.filter_by(user_id=user.id if user else 1)\
        .order_by(ChatConversation.date_updated.desc()).all()
    
    return render_template('chatbot.html', user=user, conversations=conversations, current_conversation=None)


# --- CHATBOT PAGE WITH SPECIFIC CONVERSATION ---
# Loads a specific past conversation
@app.route('/chat/<int:conversation_id>')
def chatbot_conversation(conversation_id):
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    if not user:
        user = User.query.first()
    
    # Get all conversations for sidebar
    conversations = ChatConversation.query.filter_by(user_id=user.id if user else 1)\
        .order_by(ChatConversation.date_updated.desc()).all()
    
    # Get the specific conversation with messages
    current_conversation = ChatConversation.query.get_or_404(conversation_id)
    
    # Security check - make sure conversation belongs to user
    if current_conversation.user_id != (user.id if user else 1):
        return redirect(url_for('chatbot'))
    
    return render_template('chatbot.html', user=user, conversations=conversations, current_conversation=current_conversation)


# --- CREATE NEW CONVERSATION ---
# API endpoint to create a new chat conversation
@app.route('/api/chat/new', methods=['POST'])
def create_conversation():
    user_id = session.get('user_id', 1)
    
    # Create new conversation
    new_conversation = ChatConversation(
        user_id=user_id,
        title='New Chat'
    )
    db.session.add(new_conversation)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'conversation_id': new_conversation.id
    })


# --- DELETE CONVERSATION ---
# API endpoint to delete a conversation
@app.route('/api/chat/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    user_id = session.get('user_id', 1)
    
    conversation = ChatConversation.query.get_or_404(conversation_id)
    
    # Security check
    if conversation.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(conversation)
    db.session.commit()
    
    return jsonify({'success': True})


# --- CHATBOT API ENDPOINT ---
# This handles the actual AI conversation
# Frontend sends user message via POST, we send to Gemini, return AI response
# Now also saves messages to database
@app.route('/api/chat', methods=['POST'])
def chat_api():
    # 1. Check for API Key
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_API_KEY_HERE":
        return jsonify({
            'error': 'API key not configured. Please check app.py or .env',
            'success': False
        }), 500
    
    user_id = session.get('user_id', 1)
    
    try:
        # Get the user's message from the request
        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        
        # Don't process empty messages
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # --- DATABASE: Get or Create Conversation ---
        if conversation_id:
            conversation = ChatConversation.query.get(conversation_id)
            if not conversation or conversation.user_id != user_id:
                conversation = ChatConversation(user_id=user_id, title='New Chat')
                db.session.add(conversation)
                db.session.commit()
        else:
            conversation = ChatConversation(user_id=user_id, title='New Chat')
            db.session.add(conversation)
            db.session.commit()
        
        # Save user message to database
        user_msg = ChatMessage(
            conversation_id=conversation.id,
            role='user',
            content=user_message
        )
        db.session.add(user_msg)
        
        # Update conversation title from first message
        if conversation.title == 'New Chat':
            conversation.title = user_message[:50] + ('...' if len(user_message) > 50 else '')
        
        # --- PREPARE PROMPT (This was missing!) ---
        # Get conversation history from database
        history_messages = ChatMessage.query.filter_by(conversation_id=conversation.id)\
            .order_by(ChatMessage.date_created).all()
        
        # Build the full prompt with system instruction + history + new message
        full_prompt = BRIDGEBOT_SYSTEM_PROMPT + "\n\n"
        
        # Add conversation history
        for msg in history_messages:
            if msg.role == 'user':
                full_prompt += f"User: {msg.content}\n"
            else:
                full_prompt += f"BridgeBot: {msg.content}\n"
        
        # Add the new user message
        full_prompt += f"User: {user_message}\nBridgeBot:"
        
        # --- SEND TO GEMINI (With Retry Logic) ---
        client = genai.Client(api_key=GEMINI_API_KEY)
        ai_response = "I'm having trouble connecting right now."
        
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Using the stable 1.5-flash model
                response = client.models.generate_content(
                    model="gemini-2.5-flash", 
                    contents=full_prompt
                )
                ai_response = response.text
                break # Success! Exit the loop
            except Exception as e:
                error_str = str(e)
                print(f"Attempt {attempt+1} failed: {error_str}")
                
                # If it's a quota/rate limit error, wait and retry
                if ("429" in error_str or "quota" in error_str.lower()) and attempt < max_retries - 1:
                    time.sleep(base_delay)
                    base_delay *= 2 # Wait longer next time (2s, 4s...)
                    continue
                elif attempt == max_retries - 1:
                    # If we failed all 3 times, re-raise the error
                    raise e
        
        # Save bot response to database
        bot_msg = ChatMessage(
            conversation_id=conversation.id,
            role='bot',
            content=ai_response
        )
        db.session.add(bot_msg)
        
        # Update conversation timestamp
        conversation.date_updated = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'response': ai_response,
            'success': True,
            'conversation_id': conversation.id,
            'conversation_title': conversation.title
        })
        
    except Exception as e:
        print(f"Chatbot error: {type(e).__name__}: {e}")
        
        # Specific error messages for the user
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg:
             return jsonify({
                'error': 'BridgeBot is taking a short break (Rate Limit). Please wait 30 seconds.',
                'success': False
            }), 429
        elif "api key" in error_msg:
            return jsonify({
                'error': 'Configuration Error: Invalid API Key.',
                'success': False
            }), 500
        else:
            return jsonify({
                'error': f'An error occurred: {str(e)[:100]}',
                'success': False
            }), 500


# ============================================================================
# ROLE-SPECIFIC CHATBOT ROUTES
# Separate chatbot pages for student, mentor, and both roles
# ============================================================================

# --- STUDENT CHATBOT ---
@app.route('/student/chat')
def student_chatbot():
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    if not user:
        user = User.query.first()
    conversations = ChatConversation.query.filter_by(user_id=user.id if user else 1)\
        .order_by(ChatConversation.date_updated.desc()).all()
    return render_template('student/chatbot.html', user=user, conversations=conversations, current_conversation=None)

@app.route('/student/chat/<int:conversation_id>')
def student_chatbot_conversation(conversation_id):
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    if not user:
        user = User.query.first()
    conversations = ChatConversation.query.filter_by(user_id=user.id if user else 1)\
        .order_by(ChatConversation.date_updated.desc()).all()
    current_conversation = ChatConversation.query.get_or_404(conversation_id)
    if current_conversation.user_id != (user.id if user else 1):
        return redirect(url_for('student_chatbot'))
    return render_template('student/chatbot.html', user=user, conversations=conversations, current_conversation=current_conversation)

# --- MENTOR CHATBOT ---
@app.route('/mentor/chat')
def mentor_chatbot():
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    if not user:
        user = User.query.first()
    conversations = ChatConversation.query.filter_by(user_id=user.id if user else 1)\
        .order_by(ChatConversation.date_updated.desc()).all()
    return render_template('mentor/chatbot.html', user=user, conversations=conversations, current_conversation=None)

@app.route('/mentor/chat/<int:conversation_id>')
def mentor_chatbot_conversation(conversation_id):
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    if not user:
        user = User.query.first()
    conversations = ChatConversation.query.filter_by(user_id=user.id if user else 1)\
        .order_by(ChatConversation.date_updated.desc()).all()
    current_conversation = ChatConversation.query.get_or_404(conversation_id)
    if current_conversation.user_id != (user.id if user else 1):
        return redirect(url_for('mentor_chatbot'))
    return render_template('mentor/chatbot.html', user=user, conversations=conversations, current_conversation=current_conversation)

# --- BOTH CHATBOT ---
@app.route('/both/chat')
def both_chatbot():
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    if not user:
        user = User.query.first()
    conversations = ChatConversation.query.filter_by(user_id=user.id if user else 1)\
        .order_by(ChatConversation.date_updated.desc()).all()
    return render_template('both/chatbot.html', user=user, conversations=conversations, current_conversation=None)

@app.route('/both/chat/<int:conversation_id>')
def both_chatbot_conversation(conversation_id):
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    if not user:
        user = User.query.first()
    conversations = ChatConversation.query.filter_by(user_id=user.id if user else 1)\
        .order_by(ChatConversation.date_updated.desc()).all()
    current_conversation = ChatConversation.query.get_or_404(conversation_id)
    if current_conversation.user_id != (user.id if user else 1):
        return redirect(url_for('both_chatbot'))
    return render_template('both/chatbot.html', user=user, conversations=conversations, current_conversation=current_conversation)


# --- CREATION AI CHATBOT (Original AI-powered chatbot with Gemini) ---
@app.route('/both/creation-chat')
def creation_chatbot():
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    if not user:
        user = User.query.first()
    conversations = ChatConversation.query.filter_by(user_id=user.id if user else 1)\
        .order_by(ChatConversation.date_updated.desc()).all()
    return render_template('both/creation_chatbot.html', user=user, conversations=conversations, current_conversation=None)

@app.route('/both/creation-chat/<int:conversation_id>')
def creation_chatbot_conversation(conversation_id):
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    if not user:
        user = User.query.first()
    conversations = ChatConversation.query.filter_by(user_id=user.id if user else 1)\
        .order_by(ChatConversation.date_updated.desc()).all()
    current_conversation = ChatConversation.query.get_or_404(conversation_id)
    if current_conversation.user_id != (user.id if user else 1):
        return redirect(url_for('creation_chatbot'))
    return render_template('both/creation_chatbot.html', user=user, conversations=conversations, current_conversation=current_conversation)


# ============================================================================
# ROLE-SPECIFIC FOLDER ROUTES
# Separate folder pages for student, mentor, and both roles
# ============================================================================

# --- STUDENT FOLDER ROUTES ---
@app.route('/student/folders')
def student_folder_list():
    user_id = session.get('user_id', 1)
    folders = Folder.query.filter_by(user_id=user_id).all()
    folder_course_counts = {}
    for folder in folders:
        count = FolderCourse.query.filter_by(folder_id=folder.id).count()
        folder_course_counts[folder.id] = count
    return render_template('student/folder_list.html', folders=folders, folder_course_counts=folder_course_counts)

@app.route('/student/folders/create', methods=['GET', 'POST'])
def student_folder_create():
    user_id = session.get('user_id', 1)
    icons = ['folder', 'heart', 'bookmark', 'star', 'book']
    colors = ['#ECD9B9', '#FFE5C4', '#DEC09A', '#C4B4A7', '#BEBAAF']
    if request.method == 'POST':
        name = request.form.get('folder_name', '').strip()
        desc = request.form.get('description', '').strip()
        icon = request.form.get('icon', 'folder')
        color = request.form.get('color', '#ECD9B9')
        if not name or len(name) < 2:
            flash('Folder name must be at least 2 characters.', 'error')
            return render_template('student/folder_create.html', icons=icons, colors=colors)
        if Folder.query.filter_by(user_id=user_id, folder_name=name).first():
            flash('Folder with this name already exists.', 'error')
            return render_template('student/folder_create.html', icons=icons, colors=colors)
        folder = Folder(user_id=user_id, folder_name=name, description=desc, icon=icon, color=color)
        db.session.add(folder)
        db.session.commit()
        flash('Folder created!', 'success')
        return redirect(url_for('student_folder_list'))
    return render_template('student/folder_create.html', icons=icons, colors=colors)

@app.route('/student/folders/<int:folder_id>')
def student_folder_view(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    folder_courses = FolderCourse.query.filter_by(folder_id=folder_id).all()
    courses = [Course.query.get(fc.course_id) for fc in folder_courses if Course.query.get(fc.course_id)]
    return render_template('student/folder_view.html', folder=folder, courses=courses)

@app.route('/student/folders/<int:folder_id>/edit', methods=['GET', 'POST'])
def student_folder_edit(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    icons = ['folder', 'heart', 'bookmark', 'star', 'book']
    colors = ['#ECD9B9', '#FFE5C4', '#DEC09A', '#C4B4A7', '#BEBAAF']
    if request.method == 'POST':
        name = request.form.get('folder_name', '').strip()
        desc = request.form.get('description', '').strip()
        icon = request.form.get('icon', 'folder')
        color = request.form.get('color', '#ECD9B9')
        if not name or len(name) < 2:
            flash('Folder name must be at least 2 characters.', 'error')
        else:
            folder.folder_name = name
            folder.description = desc
            folder.icon = icon
            folder.color = color
            db.session.commit()
            flash('Folder updated!', 'success')
            return redirect(url_for('student_folder_list'))
    return render_template('student/folder_edit.html', folder=folder, icons=icons, colors=colors)

@app.route('/student/folders/<int:folder_id>/delete', methods=['POST'])
def student_folder_delete(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    if not folder.is_deletable:
        flash('This folder cannot be deleted.', 'error')
        return redirect(url_for('student_folder_list'))
    db.session.delete(folder)
    db.session.commit()
    flash('Folder deleted!', 'success')
    return redirect(url_for('student_folder_list'))

# --- MENTOR FOLDER ROUTES ---
@app.route('/mentor/folders')
def mentor_folder_list_page():
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    folders = Folder.query.filter_by(user_id=user_id).all()
    folder_template_counts = {}
    for folder in folders:
        count = FolderTemplate.query.filter_by(folder_id=folder.id).count()
        folder_template_counts[folder.id] = count
    return render_template('mentor/folder_list.html', user=user, folders=folders, folder_template_counts=folder_template_counts)

@app.route('/mentor/folders/create', methods=['GET', 'POST'])
def mentor_folder_create():
    user_id = session.get('user_id', 1)
    icons = ['folder', 'heart', 'bookmark', 'star', 'book']
    colors = ['#ECD9B9', '#FFE5C4', '#DEC09A', '#C4B4A7', '#BEBAAF']
    if request.method == 'POST':
        name = request.form.get('folder_name', '').strip()
        desc = request.form.get('description', '').strip()
        icon = request.form.get('icon', 'folder')
        color = request.form.get('color', '#ECD9B9')
        if not name or len(name) < 2:
            flash('Folder name must be at least 2 characters.', 'error')
            return render_template('mentor/folder_create.html', icons=icons, colors=colors)
        if Folder.query.filter_by(user_id=user_id, folder_name=name).first():
            flash('Folder with this name already exists.', 'error')
            return render_template('mentor/folder_create.html', icons=icons, colors=colors)
        folder = Folder(user_id=user_id, folder_name=name, description=desc, icon=icon, color=color)
        db.session.add(folder)
        db.session.commit()
        flash('Folder created!', 'success')
        return redirect(url_for('mentor_folder_list_page'))
    return render_template('mentor/folder_create.html', icons=icons, colors=colors)

@app.route('/mentor/folders/<int:folder_id>')
def mentor_folder_view_page(folder_id):
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    folder = Folder.query.get_or_404(folder_id)
    folder_templates = FolderTemplate.query.filter_by(folder_id=folder_id).all()
    templates = [Template.query.get(ft.template_id) for ft in folder_templates if Template.query.get(ft.template_id)]
    return render_template('mentor/folder_view.html', user=user, folder=folder, templates=templates)

@app.route('/mentor/folders/<int:folder_id>/edit', methods=['GET', 'POST'])
def mentor_folder_edit(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    icons = ['folder', 'heart', 'bookmark', 'star', 'book']
    colors = ['#ECD9B9', '#FFE5C4', '#DEC09A', '#C4B4A7', '#BEBAAF']
    if request.method == 'POST':
        name = request.form.get('folder_name', '').strip()
        desc = request.form.get('description', '').strip()
        icon = request.form.get('icon', 'folder')
        color = request.form.get('color', '#ECD9B9')
        if not name or len(name) < 2:
            flash('Folder name must be at least 2 characters.', 'error')
        else:
            folder.folder_name = name
            folder.description = desc
            folder.icon = icon
            folder.color = color
            db.session.commit()
            flash('Folder updated!', 'success')
            return redirect(url_for('mentor_folder_list_page'))
    return render_template('mentor/folder_edit.html', folder=folder, icons=icons, colors=colors)

@app.route('/mentor/folders/<int:folder_id>/delete', methods=['POST'])
def mentor_folder_delete(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    if not folder.is_deletable:
        flash('This folder cannot be deleted.', 'error')
        return redirect(url_for('mentor_folder_list_page'))
    db.session.delete(folder)
    db.session.commit()
    flash('Folder deleted!', 'success')
    return redirect(url_for('mentor_folder_list_page'))

# --- BOTH FOLDER ROUTES ---
@app.route('/both/folders')
def both_folder_list():
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    folders = Folder.query.filter_by(user_id=user_id).all()
    # Count both courses and templates for each folder
    folder_course_counts = {}
    folder_template_counts = {}
    for folder in folders:
        folder_course_counts[folder.id] = FolderCourse.query.filter_by(folder_id=folder.id).count()
        folder_template_counts[folder.id] = FolderTemplate.query.filter_by(folder_id=folder.id).count()
    return render_template('both/folder_list.html', user=user, folders=folders, 
                          folder_course_counts=folder_course_counts, folder_template_counts=folder_template_counts)

@app.route('/both/folders/create', methods=['GET', 'POST'])
def both_folder_create():
    user_id = session.get('user_id', 1)
    icons = ['folder', 'heart', 'bookmark', 'star', 'book']
    colors = ['#ECD9B9', '#FFE5C4', '#DEC09A', '#C4B4A7', '#BEBAAF']
    if request.method == 'POST':
        name = request.form.get('folder_name', '').strip()
        desc = request.form.get('description', '').strip()
        icon = request.form.get('icon', 'folder')
        color = request.form.get('color', '#ECD9B9')
        if not name or len(name) < 2:
            flash('Folder name must be at least 2 characters.', 'error')
            return render_template('both/folder_create.html', icons=icons, colors=colors)
        if Folder.query.filter_by(user_id=user_id, folder_name=name).first():
            flash('Folder with this name already exists.', 'error')
            return render_template('both/folder_create.html', icons=icons, colors=colors)
        folder = Folder(user_id=user_id, folder_name=name, description=desc, icon=icon, color=color)
        db.session.add(folder)
        db.session.commit()
        flash('Folder created!', 'success')
        return redirect(url_for('both_folder_list'))
    return render_template('both/folder_create.html', icons=icons, colors=colors)

@app.route('/both/folders/<int:folder_id>')
def both_folder_view(folder_id):
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    folder = Folder.query.get_or_404(folder_id)
    # Get both courses and templates in this folder
    folder_courses = FolderCourse.query.filter_by(folder_id=folder_id).all()
    courses = [Course.query.get(fc.course_id) for fc in folder_courses if Course.query.get(fc.course_id)]
    folder_templates = FolderTemplate.query.filter_by(folder_id=folder_id).all()
    templates = [Template.query.get(ft.template_id) for ft in folder_templates if Template.query.get(ft.template_id)]
    return render_template('both/folder_view.html', user=user, folder=folder, courses=courses, templates=templates)

@app.route('/both/folders/<int:folder_id>/edit', methods=['GET', 'POST'])
def both_folder_edit(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    icons = ['folder', 'heart', 'bookmark', 'star', 'book']
    colors = ['#ECD9B9', '#FFE5C4', '#DEC09A', '#C4B4A7', '#BEBAAF']
    if request.method == 'POST':
        name = request.form.get('folder_name', '').strip()
        desc = request.form.get('description', '').strip()
        icon = request.form.get('icon', 'folder')
        color = request.form.get('color', '#ECD9B9')
        if not name or len(name) < 2:
            flash('Folder name must be at least 2 characters.', 'error')
        else:
            folder.folder_name = name
            folder.description = desc
            folder.icon = icon
            folder.color = color
            db.session.commit()
            flash('Folder updated!', 'success')
            return redirect(url_for('both_folder_list'))
    return render_template('both/folder_edit.html', folder=folder, icons=icons, colors=colors)

@app.route('/both/folders/<int:folder_id>/delete', methods=['POST'])
def both_folder_delete(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    if not folder.is_deletable:
        flash('This folder cannot be deleted.', 'error')
        return redirect(url_for('both_folder_list'))
    db.session.delete(folder)
    db.session.commit()
    flash('Folder deleted!', 'success')
    return redirect(url_for('both_folder_list'))


# ============================================================================
# BOTH (LEARNER & MENTOR) HOMEPAGE
# This is a combined homepage for users who selected "Learner & Mentor" during signup
# It displays both courses AND templates in each section, giving users access to
# both learning content and teaching tools in one unified interface
# ============================================================================

@app.route('/both/home')
def both_homepage():
    """
    Main homepage for users with 'both' role (Learner & Mentor)
    Shows courses and templates side by side in each section
    """
    # Get the currently logged in user from session
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    if not user:
        user = User.query.first()
    
    # --- MY COLLECTIONS (folders) ---
    # Get all user's folders and count items in each
    folders = Folder.query.filter_by(user_id=user.id if user else 1).all()
    folder_course_counts = {}
    folder_template_counts = {}
    for folder in folders:
        folder_course_counts[folder.id] = FolderCourse.query.filter_by(folder_id=folder.id).count()
        folder_template_counts[folder.id] = FolderTemplate.query.filter_by(folder_id=folder.id).count()
    
    # --- JUMP BACK IN: COURSES ---
    # Shows courses the user has started but not completed
    courses_in_progress = []
    course_in_progress_ids = []
    if user:
        progress_records = UserProgress.query.filter_by(user_id=user.id).order_by(UserProgress.last_accessed.desc()).all()
        for p in progress_records:
            course = Course.query.get(p.course_id)
            if course:
                courses_in_progress.append({'course': course, 'progress': p.progress_percent})
                course_in_progress_ids.append(course.id)
    
    # --- JUMP BACK IN: TEMPLATES ---
    # Shows templates the user has started working with
    templates_in_progress = []
    template_in_progress_ids = []
    if user:
        template_progress = TemplateProgress.query.filter_by(user_id=user.id).order_by(TemplateProgress.last_accessed.desc()).all()
        for p in template_progress:
            template = Template.query.get(p.template_id)
            if template:
                templates_in_progress.append({'template': template, 'progress': p.progress_percent})
                template_in_progress_ids.append(template.id)
    
    # --- RECOMMENDED COURSES (based on learning_interests) ---
    recommended_courses = []
    if user and user.learning_interests:
        interests = [i.strip() for i in user.learning_interests.split(',')]
        for interest in interests:
            matching = Course.query.filter(Course.category.ilike(f'%{interest}%')).all()
            for course in matching:
                if course.id not in course_in_progress_ids and course not in recommended_courses:
                    recommended_courses.append(course)
    if not recommended_courses:
        recommended_courses = Course.query.filter(~Course.id.in_(course_in_progress_ids)).all() if course_in_progress_ids else Course.query.all()
    
    # --- RECOMMENDED TEMPLATES (based on teaching_interests) ---
    recommended_templates = []
    if user and user.teaching_interests:
        interests = [i.strip() for i in user.teaching_interests.split(',')]
        for interest in interests:
            matching = Template.query.filter(Template.category.ilike(f'%{interest}%')).all()
            for template in matching:
                if template.id not in template_in_progress_ids and template not in recommended_templates:
                    recommended_templates.append(template)
    if not recommended_templates:
        recommended_templates = Template.query.filter(~Template.id.in_(template_in_progress_ids)).all() if template_in_progress_ids else Template.query.all()
    
    # --- ALL COURSES (for Latest from us - Courses) ---
    all_courses = Course.query.order_by(Course.date_created.desc()).all()
    
    # --- ALL TEMPLATES (for Latest from us - Templates) ---
    all_templates = Template.query.order_by(Template.usage_count.desc()).all()
    
    # --- RELATED COURSES (based on categories user has used OR interests) ---
    user_categories = set()
    for item in courses_in_progress:
        user_categories.add(item['course'].category)
    for item in templates_in_progress:
        user_categories.add(item['template'].category)
    # Fallback: use user's interests if no in-progress items
    if not user_categories and user:
        if user.learning_interests:
            for i in user.learning_interests.split(','):
                user_categories.add(i.strip())
        if user.teaching_interests:
            for i in user.teaching_interests.split(','):
                user_categories.add(i.strip())
    
    related_courses = []
    related_templates = []
    if user_categories:
        for cat in user_categories:
            matching_courses = Course.query.filter(Course.category.ilike(f'%{cat}%')).all()
            for c in matching_courses:
                if c not in related_courses:
                    related_courses.append(c)
            matching_templates = Template.query.filter(Template.category.ilike(f'%{cat}%')).all()
            for t in matching_templates:
                if t not in related_templates:
                    related_templates.append(t)
    
    return render_template('both_homepage.html',
                         user=user,
                         folders=folders,
                         folder_course_counts=folder_course_counts,
                         folder_template_counts=folder_template_counts,
                         courses_in_progress=courses_in_progress,
                         templates_in_progress=templates_in_progress,
                         recommended_courses=recommended_courses,
                         recommended_templates=recommended_templates,
                         all_courses=all_courses,
                         all_templates=all_templates,
                         related_courses=related_courses,
                         related_templates=related_templates)


# ============================================================================
# COURSE ROUTES
# Handle viewing courses, adding to folders, tracking progress
# ============================================================================

# --- VIEW SINGLE COURSE ---
# Opens course in modal view, creates/updates progress record
@app.route('/course/<int:course_id>')
def view_course(course_id):
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    course = Course.query.get_or_404(course_id)  # 404 if course doesn't exist
    
    # Check if user came from a folder (for back button navigation)
    from_folder = request.args.get('from_folder')
    
    # Track progress - creates new record if first time viewing
    if user:
        progress = UserProgress.query.filter_by(user_id=user.id, course_id=course_id).first()
        if not progress:
            # First time viewing - start at 5% progress
            progress = UserProgress(user_id=user.id, course_id=course_id, progress_percent=5)
            db.session.add(progress)
        else:
            # Update last accessed time
            progress.last_accessed = datetime.utcnow()
        db.session.commit()
    
    return render_template('course_view.html', course=course, user=user, from_folder=from_folder)


# --- ADD COURSE TO FOLDER ---
# Called when user clicks "Add to Folder" in course popup
@app.route('/course/<int:course_id>/add-to-folder', methods=['POST'])
def add_course_to_folder(course_id):
    user_id = session.get('user_id', 1)
    folder_id = request.form.get('folder_id')
    
    if folder_id:
        # Check if already in folder to prevent duplicates
        existing = FolderCourse.query.filter_by(folder_id=folder_id, course_id=course_id).first()
        if not existing:
            folder_course = FolderCourse(folder_id=folder_id, course_id=course_id)
            db.session.add(folder_course)
            db.session.commit()
            flash('Course added to folder!', 'success')
        else:
            flash('Course is already in this folder.', 'error')
    
    return redirect(url_for('both_homepage'))


# --- ADD COURSE TO FOLDER (AJAX) ---
# For popup folder dropdown - returns JSON instead of redirect
@app.route('/folder/<int:folder_id>/add-course/<int:course_id>', methods=['POST'])
def add_course_to_folder_ajax(folder_id, course_id):
    user_id = session.get('user_id', 1)
    folder = Folder.query.get_or_404(folder_id)
    
    if folder.user_id != user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Check if already in folder
    existing = FolderCourse.query.filter_by(folder_id=folder_id, course_id=course_id).first()
    if not existing:
        folder_course = FolderCourse(folder_id=folder_id, course_id=course_id)
        db.session.add(folder_course)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Course added to folder!'})
    else:
        return jsonify({'success': True, 'message': 'Course already in folder'})


# --- REMOVE COURSE FROM FOLDER ---
# Called from folder edit mode when user clicks X on a course
@app.route('/folder/<int:folder_id>/remove-course/<int:course_id>', methods=['POST'])
def remove_course_from_folder(folder_id, course_id):
    folder_course = FolderCourse.query.filter_by(folder_id=folder_id, course_id=course_id).first()
    if folder_course:
        db.session.delete(folder_course)
        db.session.commit()
        flash('Course removed from folder.', 'success')
    return redirect(url_for('folder_view', folder_id=folder_id))


# --- AJAX: TRACK COURSE PROGRESS ---
# Called from popup "Open Course" button before navigating to library
@app.route('/api/track-course/<int:course_id>', methods=['POST'])
def track_course_progress(course_id):
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    course = Course.query.get(course_id)
    if not user or not course:
        return jsonify({'success': False, 'message': 'Not found'}), 404
    progress = UserProgress.query.filter_by(user_id=user.id, course_id=course_id).first()
    if not progress:
        progress = UserProgress(user_id=user.id, course_id=course_id, progress_percent=5)
        db.session.add(progress)
    else:
        progress.last_accessed = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'message': 'Progress tracked'})


# --- AJAX: TRACK TEMPLATE PROGRESS ---
# Called from popup "Use Template" button before navigating
@app.route('/api/track-template/<int:template_id>', methods=['POST'])
def track_template_progress(template_id):
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    template = Template.query.get(template_id)
    if not user or not template:
        return jsonify({'success': False, 'message': 'Not found'}), 404
    progress = TemplateProgress.query.filter_by(user_id=user.id, template_id=template_id).first()
    if not progress:
        progress = TemplateProgress(user_id=user.id, template_id=template_id, progress_percent=5)
        db.session.add(progress)
    else:
        progress.last_accessed = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'message': 'Progress tracked'})


# --- COURSE API ---
# Returns course data as JSON for the popup modal
# Called via JavaScript fetch() when clicking a course card
@app.route('/api/course/<int:course_id>')
def get_course_api(course_id):
    course = Course.query.get_or_404(course_id)
    user_id = session.get('user_id', 1)
    folders = Folder.query.filter_by(user_id=user_id).all()
    
    return {
        'id': course.id,
        'title': course.title,
        'instructor': course.instructor_name,
        'category': course.category,
        'color': course.color,
        'library_id': course.library_id,
        'description': course.description or f'Learn {course.category.lower()} skills with {course.instructor_name}. This course covers fundamental concepts and practical applications.',
        'folders': [{'id': f.id, 'name': f.folder_name} for f in folders]
    }


# --- ALL COURSES PAGE ---
# Shows grid of all available courses with filter options
@app.route('/courses/all')
def all_courses_page():
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    courses = Course.query.order_by(Course.date_created.desc()).all()
    folders = Folder.query.filter_by(user_id=user_id).all()
    return render_template('courses_all.html', user=user, courses=courses, folders=folders, title='All Courses')


# --- RECOMMENDED COURSES PAGE ---
# Same layout as all courses but filtered by user interests
@app.route('/courses/recommended')
def recommended_courses_page():
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    folders = Folder.query.filter_by(user_id=user_id).all()
    
    # Exclude courses already in progress
    in_progress_ids = [p.course_id for p in UserProgress.query.filter_by(user_id=user_id).all()]
    
    # Match courses to user interests
    courses = []
    if user and user.learning_interests:
        interests = [i.strip() for i in user.learning_interests.split(',')]
        for interest in interests:
            matching = Course.query.filter(Course.category.ilike(f'%{interest}%')).all()
            for course in matching:
                if course.id not in in_progress_ids and course not in courses:
                    courses.append(course)
    
    if not courses:
        courses = Course.query.filter(~Course.id.in_(in_progress_ids)).all() if in_progress_ids else Course.query.all()
    
    return render_template('courses_all.html', user=user, courses=courses, folders=folders, title='Recommended For You')


# --- IN PROGRESS COURSES PAGE ---
# Shows only courses user has started, with progress bars
@app.route('/courses/in-progress')
def in_progress_courses_page():
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    folders = Folder.query.filter_by(user_id=user_id).all()
    
    courses_in_progress = []
    progress_records = UserProgress.query.filter_by(user_id=user_id).order_by(UserProgress.last_accessed.desc()).all()
    for p in progress_records:
        course = Course.query.get(p.course_id)
        if course:
            courses_in_progress.append({
                'course': course,
                'progress': p.progress_percent
            })
    
    return render_template('courses_in_progress.html', user=user, courses_in_progress=courses_in_progress, folders=folders)


# --- COURSE HISTORY PAGE ---
# Shows courses user has started, WITHOUT progress bars
@app.route('/courses/history')
def course_history_page():
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    folders = Folder.query.filter_by(user_id=user_id).all()
    
    courses_history = []
    progress_records = UserProgress.query.filter_by(user_id=user_id).order_by(UserProgress.last_accessed.desc()).all()
    for p in progress_records:
        course = Course.query.get(p.course_id)
        if course:
            courses_history.append(course)
    
    return render_template('courses_history.html', user=user, courses=courses_history, folders=folders)


# --- TEMPLATE HISTORY PAGE ---
# Shows templates user has started, WITHOUT progress bars
@app.route('/mentor/templates/history')
def template_history_page():
    user_id = session.get('user_id', 1)
    user = User.query.get(user_id)
    
    templates_history = []
    progress_records = TemplateProgress.query.filter_by(user_id=user_id).order_by(TemplateProgress.last_accessed.desc()).all()
    for p in progress_records:
        template = Template.query.get(p.template_id)
        if template:
            templates_history.append(template)
    
    return render_template('templates_history.html', user=user, templates=templates_history)


# ============================================================================
# STATIC PAGE ROUTES
# About and Contact pages
# ============================================================================

# --- ABOUT PAGE ---
@app.route('/about')
def about():
    faqs = FAQ.query.filter_by(is_active=True).all()
    return render_template('about.html', faqs=faqs)


# --- CONTACT PAGE ---
# Handles both GET (show form) and POST (submit form)
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        topic = request.form.get('topic', '').strip()
        message = request.form.get('message', '').strip()
        
        # Validation - all fields required
        if not all([first_name, last_name, email, topic, message]):
            flash('Please fill in all fields.', 'error')
        else:
            # CREATE - Save message to database
            contact_msg = ContactMessage(
                first_name=first_name,
                last_name=last_name,
                email=email,
                topic=topic,
                message=message
            )
            db.session.add(contact_msg)
            db.session.commit()
            flash('Thank you for your message! We\'ll get back to you soon.', 'success')
            return redirect(url_for('contact'))
    
    faqs = FAQ.query.filter_by(is_active=True).all()
    return render_template('contact.html', faqs=faqs)


# --- SUPPORT PAGE ---
# Support center with FAQs, ticket submission, and ticket history
@app.route('/support', methods=['GET', 'POST'])
def support():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('landing'))
    
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('landing'))
    
    if request.method == 'POST':
        ticket = SupportTicket(
            user_id=user.id,
            subject=request.form.get('subject', '').strip(),
            category=request.form.get('category', '').strip(),
            message=request.form.get('message', '').strip()
        )
        db.session.add(ticket)
        db.session.commit()
        flash('Ticket submitted successfully!', 'success')
        return redirect(url_for('support'))
    
    tickets = SupportTicket.query.filter_by(user_id=user.id).order_by(SupportTicket.created_at.desc()).all()
    faqs = FAQ.query.filter_by(is_active=True).all()
    
    return render_template('support.html', user=user, tickets=tickets, faqs=faqs)


# ============================================================================
# REWARDS PAGE
# Shop for items with Hive Points and complete quests to earn more
# ============================================================================

@app.route('/rewards')
def rewards():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('landing'))
    
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('landing'))
    
    view = request.args.get('view', 'shop')
    category = request.args.get('category', 'all')
    
    # Shop items
    items_query = ShopItem.query
    if category != 'all':
        items_query = items_query.filter_by(category=category)
    items = items_query.all()
    
    # Get owned item IDs
    owned_ids = [ui.item_id for ui in UserItem.query.filter_by(user_id=user.id).all()]
    
    # Quests
    quests = Quest.query.filter_by(is_active=True).all()
    completed_ids = [qc.quest_id for qc in QuestCompletion.query.filter_by(user_id=user.id).all()]
    
    categories = [
        ('all', 'All Items'),
        ('avatar-decoration', 'Decorations'),
        ('profile-effect', 'Profile Effects'),
        ('chat-effect', 'Chat Effects'),
        ('nameplate', 'Nameplates'),
        ('bundle', 'Bundles')
    ]
    
    return render_template('rewards.html',
                         user=user,
                         items=items,
                         owned_ids=owned_ids,
                         quests=quests,
                         completed_ids=completed_ids,
                         categories=categories,
                         current_category=category,
                         view=view)


@app.route('/rewards/buy/<int:item_id>', methods=['POST'])
def buy_item(item_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    item = ShopItem.query.get_or_404(item_id)
    
    # Check if already owned
    existing = UserItem.query.filter_by(user_id=user.id, item_id=item.id).first()
    if existing:
        flash('You already own this item!', 'error')
        return redirect(url_for('rewards'))
    
    if user.hive_points >= item.price:
        user.hive_points -= item.price
        new_item = UserItem(user_id=user.id, item_id=item.id)
        db.session.add(new_item)
        db.session.commit()
        flash(f'Successfully purchased {item.name}!', 'success')
    else:
        flash('Not enough points!', 'error')
    
    return redirect(url_for('rewards'))


@app.route('/api/quest/<int:quest_id>/progress', methods=['POST'])
def quest_progress(quest_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    progress = VideoProgress.query.filter_by(user_id=user_id, quest_id=quest_id).first()
    
    if not progress:
        progress = VideoProgress(user_id=user_id, quest_id=quest_id)
        db.session.add(progress)
    
    progress.watched_duration = data.get('watched', 0)
    progress.completed = data.get('completed', False)
    progress.last_updated = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})


@app.route('/api/quest/<int:quest_id>/claim', methods=['POST'])
def claim_quest(quest_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    quest = Quest.query.get_or_404(quest_id)
    
    # Check if already completed
    existing = QuestCompletion.query.filter_by(user_id=user.id, quest_id=quest_id).first()
    if existing:
        return jsonify({'error': 'Already completed'}), 400
    
    # Check video completion
    progress = VideoProgress.query.filter_by(user_id=user.id, quest_id=quest_id).first()
    if not progress or not progress.completed:
        return jsonify({'error': 'Video not completed'}), 400
    
    # Award points
    user.hive_points += quest.reward_points
    completion = QuestCompletion(user_id=user.id, quest_id=quest_id)
    db.session.add(completion)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'new_points': user.hive_points,
        'message': f'+{quest.reward_points} points!'
    })


# ============================================================================
# ============================================================================
# PROFILE PAGE & RELATED ROUTES
# User profile information display and management
# ============================================================================

# Helper function to get equipped title
def get_equipped_title(user):
    """Get the currently equipped title for a user"""
    equipped = UserTitle.query.filter_by(user_id=user.id, is_equipped=True).first()
    return equipped

def get_title_definitions_for_role(role):
    """Return streak-based title tiers based on user role."""
    normalized_role = (role or 'learner').lower()

    if normalized_role == 'mentor':
        base_label = 'Mentor'
    elif normalized_role == 'both':
        base_label = 'Learner&Mentor'
    else:
        base_label = 'Learner'

    return [
        {'name': base_label, 'rarity': 'common', 'required_streak': 0},
        {'name': f'Intermediate {base_label}', 'rarity': 'common', 'required_streak': 7},
        {'name': f'Astute {base_label}', 'rarity': 'rare', 'required_streak': 14},
        {'name': f'Advanced {base_label}', 'rarity': 'epic', 'required_streak': 30},
    ]

# Helper function to get available titles based on streak
def get_available_titles(streak_days):
    """Get list of available titles based on streak days"""
    return get_available_titles_for_role(streak_days, 'learner')

def get_available_titles_for_role(streak_days, role):
    """Get unlocked title tiers based on streak and role."""
    definitions = get_title_definitions_for_role(role)
    return [title for title in definitions if streak_days >= title['required_streak']]

# Helper function to unlock titles for user
def unlock_titles_for_user(user):
    """Sync and unlock role-based titles for user by streak tier."""
    definitions = get_title_definitions_for_role(user.role)
    definitions_by_streak = {title['required_streak']: title for title in definitions}
    existing_titles = UserTitle.query.filter_by(user_id=user.id).all()
    existing_by_streak = {title.required_streak: title for title in existing_titles}
    unlocked_streaks = {
        title['required_streak'] for title in get_available_titles_for_role(user.streak_days, user.role)
    }

    for required_streak, title_def in definitions_by_streak.items():
        existing = existing_by_streak.get(required_streak)
        if existing:
            existing.title_name = title_def['name']
            existing.title_rarity = title_def['rarity']
            if required_streak in unlocked_streaks and existing.acquired_date is None:
                existing.acquired_date = datetime.utcnow()
        elif required_streak in unlocked_streaks:
            db.session.add(UserTitle(
                user_id=user.id,
                title_name=title_def['name'],
                title_rarity=title_def['rarity'],
                required_streak=required_streak,
                is_equipped=(required_streak == 0)
            ))

    equipped_title = UserTitle.query.filter_by(user_id=user.id, is_equipped=True).first()
    if not equipped_title:
        base_title = UserTitle.query.filter_by(user_id=user.id, required_streak=0).first()
        if base_title:
            base_title.is_equipped = True

    db.session.commit()

def get_title_inventory_for_user(user):
    """Return all role-based title tiers with owned/locked state for profile display."""
    definitions = get_title_definitions_for_role(user.role)
    existing_titles = UserTitle.query.filter_by(user_id=user.id).all()
    existing_by_streak = {title.required_streak: title for title in existing_titles}

    inventory = []
    for title_def in definitions:
        existing = existing_by_streak.get(title_def['required_streak'])
        inventory.append({
            'id': existing.id if existing else None,
            'title_name': title_def['name'],
            'title_rarity': title_def['rarity'],
            'required_streak': title_def['required_streak'],
            'is_equipped': existing.is_equipped if existing else False,
            'is_locked': existing is None
        })

    return inventory


@app.route('/profile')
@app.route('/profile/<int:user_id>')
def profile(user_id=None):
    """View profile with privacy controls"""
    current_user_id = session.get('user_id')
    if not current_user_id:
        return redirect(url_for('landing'))
    
    current_user = User.query.get(current_user_id)
    if not current_user:
        return redirect(url_for('landing'))
    
    # If no user_id specified, show current user's own profile
    if user_id is None:
        user = current_user
        viewing_own_profile = True
    else:
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('homepage'))
        viewing_own_profile = (user.id == current_user_id)
    
    # Privacy Check - if viewing someone else's profile
    if not viewing_own_profile:
        visibility = user.settings.profile_visibility
        
        if visibility == 'private':
            flash('This profile is private', 'error')
            return redirect(url_for('homepage'))
        
        elif visibility == 'friends':
            # Check if users are friends - for now treat as private
            flash('This profile is only visible to friends', 'error')
            return redirect(url_for('homepage'))
        
        # If 'public', continue to show profile
    
    # Unlock any new titles based on streak
    unlock_titles_for_user(user)
    
    # Get user's titles (including locked tiers)
    title_inventory = get_title_inventory_for_user(user)
    equipped_title = get_equipped_title(user)
    
    # Determine if activity status should be shown
    show_activity_status = user.settings.show_activity and (viewing_own_profile or user.settings.profile_visibility == 'public')
    
    return render_template('profile.html', 
                         user=user, 
                         title_inventory=title_inventory,
                         equipped_title=equipped_title,
                         viewing_own_profile=viewing_own_profile,
                         show_activity_status=show_activity_status,
                         current_user=current_user)


@app.route('/profile/edit')
def edit_profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('landing'))
    
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('landing'))
    
    pending_changes = session.get('profile_changes', {})
    unlock_titles_for_user(user)
    title_inventory = get_title_inventory_for_user(user)
    equipped_title = get_equipped_title(user)
    
    return render_template('ProfileEdit.html', 
                         user=user, 
                         pending_changes=pending_changes,
                         title_inventory=title_inventory, 
                         equipped_title=equipped_title)


@app.route('/profile/save_changes')
def save_profile_changes():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('landing'))
    
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('landing'))
    
    if 'profile_changes' in session:
        changes = session['profile_changes']
        if 'username' in changes:
            user.username = changes['username']
        if 'profile_pic' in changes:
            user.profile_pic = changes['profile_pic']
        db.session.commit()
        session.pop('profile_changes', None)
        flash('Profile updated successfully!', 'success')
    
    return redirect(url_for('profile'))


@app.route('/profile/cancel_changes')
def cancel_profile_changes():
    session.pop('profile_changes', None)
    return redirect(url_for('profile'))


@app.route('/profile/edit/username', methods=['GET', 'POST'])
def edit_username():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('landing'))
    
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('landing'))
    
    if request.method == 'GET':
        return render_template('UsernameEdit.html', user=user)
    
    new = request.form.get('new_username')
    if new:
        if 'profile_changes' not in session:
            session['profile_changes'] = {}
        session['profile_changes']['username'] = new
        session.modified = True
    
    return redirect(url_for('edit_profile'))


@app.route('/profile/upload_pfp', methods=['GET', 'POST'])
def upload_pfp():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('landing'))
    
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('landing'))
    
    if request.method == 'GET':
        return render_template('PFPedit.html', user=user)
    
    if 'pfp' in request.files:
        file = request.files['pfp']
        if file.filename:
            from werkzeug.utils import secure_filename
            fname = secure_filename(f"{user.id}_{int(datetime.utcnow().timestamp())}_{file.filename}")
            upload_folder = os.path.join(app.root_path, 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, fname))
            if 'profile_changes' not in session:
                session['profile_changes'] = {}
            session['profile_changes']['profile_pic'] = fname
            session.modified = True
    
    return redirect(url_for('edit_profile'))


@app.route('/profile/equip/<int:user_item_id>', methods=['POST'])
def equip_item(user_item_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('landing'))
    
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('landing'))
    
    target = UserItem.query.get(user_item_id)
    if target and target.user_id == user.id:
        if target.is_equipped:
            # Unequip
            target.is_equipped = False
        else:
            # Unequip others in same category, then equip this one
            cat = target.item.category
            others = UserItem.query.join(ShopItem).filter(
                UserItem.user_id == user.id,
                UserItem.is_equipped == True,
                ShopItem.category == cat
            ).all()
            for o in others:
                o.is_equipped = False
            target.is_equipped = True
        db.session.commit()
    
    return redirect(url_for('profile'))


@app.route('/profile/equip_title/<int:title_id>', methods=['POST'])
def equip_title(title_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('landing'))
    
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('landing'))
    
    target = UserTitle.query.get(title_id)
    if target and target.user_id == user.id:
        if not target.is_equipped:
            # Unequip all other titles first
            others = UserTitle.query.filter_by(user_id=user.id, is_equipped=True).all()
            for o in others:
                o.is_equipped = False
            target.is_equipped = True
            db.session.commit()
    
    return redirect(url_for('profile'))


# ============================================================================
# NOTIFICATIONS PAGE
# ============================================================================

@app.route('/notifications', methods=['GET', 'POST'])
def notifications():
    user_id = session.get('user_id')
    is_admin_logged_in = bool(session.get('admin_logged_in'))

    user = User.query.get(user_id) if user_id else None
    if not user and not is_admin_logged_in:
        return redirect(url_for('landing'))

    if request.method == 'POST':
        flash('Announcements can only be sent from the Admin Dashboard.', 'error')
        if is_admin_logged_in:
            return redirect(url_for('admin_dashboard', tab='announcements'))
        return redirect(url_for('notifications'))

    notifications_data = []
    if user:
        notifications_data.extend([
            {'title': 'Welcome to BridgeHive', 'message': 'Your account is ready. Start exploring courses and rewards.', 'time': 'Just now', 'is_unread': True, 'source': 'system'},
            {'title': 'Streak Update', 'message': f'You are on a {user.streak_days}-day streak. Keep it going!', 'time': 'Today', 'is_unread': True, 'source': 'system'},
            {'title': 'Rewards Reminder', 'message': 'Visit Rewards to check newly available profile items.', 'time': 'Yesterday', 'is_unread': False, 'source': 'system'},
        ])

    broadcasts = BroadcastNotification.query.order_by(BroadcastNotification.created_at.desc()).all()
    for item in broadcasts:
        notifications_data.append({
            'title': item.title,
            'message': item.message,
            'time': item.created_at.strftime('%d %b %Y, %I:%M %p'),
            'is_unread': True,
            'source': f"Admin ({item.created_by})"
        })

    return render_template(
        'notifications.html',
        user=user,
        notifications=notifications_data,
        can_post_notifications=False
    )


# ============================================================================
# SETTINGS PAGE
# User preferences for language, visual, audio, privacy, and security
# ============================================================================

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('landing'))
    
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('landing'))
    
    # Ensure user has settings
    if not user.settings:
        user.settings = UserSettings(user_id=user.id)
        db.session.add(user.settings)
        db.session.commit()
    
    if request.method == 'POST':
        settings = user.settings
        
        # Update settings from form
        for key in request.form:
            if hasattr(settings, key):
                value = request.form[key]
                if isinstance(getattr(settings, key), bool):
                    setattr(settings, key, value.lower() in ['true', '1', 'on', 'yes'])
                else:
                    setattr(settings, key, value)
        
        db.session.commit()
        return jsonify({'status': 'success'})
    
    return render_template('settings.html', user=user)


@app.route('/settings/password', methods=['POST'])
def update_password():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    current = request.form.get('current_password')
    new = request.form.get('new_password')
    confirm = request.form.get('confirm_password')
    
    if not all([current, new, confirm]):
        return jsonify({'status': 'error', 'message': 'All fields required'})
    
    if user.password != current:
        return jsonify({'status': 'error', 'message': 'Incorrect current password'})
    
    if new != confirm:
        return jsonify({'status': 'error', 'message': 'Passwords do not match'})
    
    if len(new) < 8:
        return jsonify({'status': 'error', 'message': 'Password must be 8+ characters'})
    
    user.password = new
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Password updated successfully!'})


@app.route('/settings/singpass/toggle', methods=['POST'])
def toggle_singpass():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    if user and user.settings:
        user.settings.singpass_linked = not user.settings.singpass_linked
        db.session.commit()
        status = 'connected' if user.settings.singpass_linked else 'disconnected'
        return jsonify({'success': True, 'status': status})
    
    return jsonify({'error': 'User not found'}), 404


@app.route('/settings/reset', methods=['POST'])
def reset_settings():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('landing'))
    
    user = User.query.get(user_id)
    if user and user.settings:
        settings = user.settings
        settings.language = 'en'
        settings.profile_visibility = 'public'
        settings.show_activity = True
        settings.singpass_linked = False
        settings.sound_effects = False
        settings.text_to_speech = False
        settings.dark_mode = False
        settings.high_contrast = False
        settings.font_size = 'standard'
        db.session.commit()
        flash('Settings reset to default.', 'success')
    
    return redirect(url_for('settings'))


# ============================================================================
# USER AUTH ROUTES
# Login, logout, and onboarding signup wizard
# ============================================================================

# --- LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validation
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('login.html')
        
        # Check credentials against database
        user = User.query.filter_by(email=email).first()
        
        if user and user.password == password:
            # Set session to track logged in user
            session['user_id'] = user.id
            # Mark as returning user (changes welcome message)
            user.is_new_user = False
            db.session.commit()
            
            # Redirect based on user role
            if user.role == 'mentor':
                return redirect(url_for('both_homepage'))
            elif user.role == 'both':
                return redirect(url_for('both_homepage'))
            else:
                return redirect(url_for('both_homepage'))
        else:
            flash('Invalid email or password.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')


# --- LOGOUT ---
# Clears session and redirects to landing
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('landing'))


# --- ONBOARDING ROUTES ---
# Multi-step signup wizard for new users

# Start onboarding as elder
@app.route('/onboarding/elder')
def onboard_elder():
    return render_template('onboarding.html', user_type='elder')

# Start onboarding as youth
@app.route('/onboarding/youth')
def onboard_youth():
    return render_template('onboarding.html', user_type='youth')


# Process completed onboarding form
# CREATE - Creates new User record with all onboarding data
@app.route('/onboarding/submit', methods=['POST'])
def process_onboarding():
    # Get basic account info
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    user_type = request.form.get('user_type')  # elder or youth
    user_role = request.form.get('role')       # learner, mentor, both
    age_group = request.form.get('age_group')
    tech_comfort = request.form.get('tech_comfort')

    # Process learning interests (checkboxes + other field)
    learn_list = request.form.getlist('learning_interests')
    learn_other = request.form.get('learning_others')
    if learn_other:
        learn_list.append(learn_other)
    learn_str = ", ".join(learn_list)  # Convert list to comma-separated string
    
    # Process teaching interests
    teach_list = request.form.getlist('teaching_interests')
    teach_other = request.form.get('teaching_others')
    if teach_other:
        teach_list.append(teach_other)
    teach_str = ", ".join(teach_list)

    # Create new User object with all collected data
    new_user = User(
        username=username,
        email=email,
        password=password,
        user_type=user_type,
        role=user_role,
        age_group=age_group,
        tech_comfort=tech_comfort,
        learning_interests=learn_str,
        teaching_interests=teach_str
    )

    # Save to database
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # Create default settings for user
        user_settings = UserSettings(user_id=new_user.id)
        db.session.add(user_settings)
        db.session.commit()
        
        # Set session so user is logged in
        session['user_id'] = new_user.id
        
        # Create default folders based on user role
        if user_role == 'mentor':
            # Mentor gets template-focused folders
            folders = [
                Folder(user_id=new_user.id, folder_name='Liked Templates', folder_type='preset', icon='heart', color='#ECD9B9', is_deletable=False),
                Folder(user_id=new_user.id, folder_name='Use Later', folder_type='preset', icon='bookmark', color='#FFE5C4', is_deletable=False),
            ]
        elif user_role == 'both':
            # Both role gets all 4 folders (learner + mentor)
            folders = [
                Folder(user_id=new_user.id, folder_name='Liked Courses', folder_type='preset', icon='heart', color='#ECD9B9', is_deletable=False),
                Folder(user_id=new_user.id, folder_name='Watch Later', folder_type='preset', icon='bookmark', color='#FFE5C4', is_deletable=False),
                Folder(user_id=new_user.id, folder_name='Liked Templates', folder_type='preset', icon='heart', color='#DEC09A', is_deletable=False),
                Folder(user_id=new_user.id, folder_name='Use Later', folder_type='preset', icon='bookmark', color='#C4B4A7', is_deletable=False),
            ]
        else:
            # Learner gets course-focused folders
            folders = [
                Folder(user_id=new_user.id, folder_name='Liked Courses', folder_type='preset', icon='heart', color='#ECD9B9', is_deletable=False),
                Folder(user_id=new_user.id, folder_name='Watch Later', folder_type='preset', icon='bookmark', color='#FFE5C4', is_deletable=False),
            ]
        db.session.add_all(folders)
        db.session.commit()
        
        print(f"SUCCESS: User {username} saved to database!")
    except Exception as e:
        db.session.rollback()
        print(f"ERROR: Could not save user. {e}")
        flash('Error creating account. Email may already be registered.', 'error')
        return redirect(url_for('landing'))

    # Redirect all users to the unified dashboard after onboarding
    return redirect(url_for('both_homepage'))


# ============================================================================
# FAQ ROUTES
# FAQ listing and search functionality
# ============================================================================

# --- FAQ LIST PAGE ---
# READ - Shows all FAQs grouped by category
@app.route('/faq')
def faq_list():
    faqs = FAQ.query.filter_by(is_active=True).order_by(FAQ.category).all()
    categories = list(set([f.category for f in faqs]))  # Get unique categories
    return render_template('faq/list.html', faqs=faqs, categories=categories)


# --- FAQ SEARCH ---
# Searches FAQs using fuzzy matching algorithm
@app.route('/faq/search')
def faq_search():
    query = request.args.get('q', '').strip().lower()
    if not query:
        return redirect(url_for('faq_list'))
    
    faqs = FAQ.query.filter_by(is_active=True).all()
    results = []
    for faq in faqs:
        q_lower = faq.question.lower()
        # Calculate similarity score using SequenceMatcher
        ratio = SequenceMatcher(None, query, q_lower).ratio()
        # Also check how many words from query appear in question
        words = query.split()
        word_score = sum(1 for w in words if w in q_lower) / len(words) if words else 0
        # Combined score (weighted average)
        score = (ratio * 0.4) + (word_score * 0.6)
        if score > 0.2:  # Only include if reasonably relevant
            results.append({'faq': faq, 'score': score})
    results.sort(key=lambda x: x['score'], reverse=True)  # Best matches first
    return render_template('faq/search_results.html', results=results, query=query)


# --- FAQ API ---
# Returns matching FAQs as JSON for live search suggestions
@app.route('/api/faq/search')
def api_faq_search():
    query = request.args.get('q', '').strip().lower()
    if not query or len(query) < 2:
        return jsonify([])
    
    faqs = FAQ.query.filter_by(is_active=True).all()
    results = []
    for faq in faqs:
        if query in faq.question.lower():
            results.append({'id': faq.id, 'question': faq.question, 'answer': faq.answer})
    return jsonify(results[:5])  # Return max 5 suggestions


# ============================================================================
# FOLDER ROUTES (User Collections)
# Full CRUD operations for user folders
# ============================================================================

# --- FOLDER LIST ---
# READ - Shows all user's folders with course counts
@app.route('/folders')
def folder_list():
    user_id = session.get('user_id', 1)
    folders = Folder.query.filter_by(user_id=user_id).all()
    
    # Count courses in each folder
    folder_course_counts = {}
    for folder in folders:
        count = FolderCourse.query.filter_by(folder_id=folder.id).count()
        folder_course_counts[folder.id] = count
    
    return render_template('folder/list.html', folders=folders, folder_course_counts=folder_course_counts)


# --- CREATE FOLDER ---
# CREATE - Form to make new folder with custom icon/color
@app.route('/folders/create', methods=['GET', 'POST'])
def folder_create():
    user_id = session.get('user_id', 1)
    icons = ['folder', 'heart', 'bookmark', 'star', 'book']
    colors = ['#ECD9B9', '#FFE5C4', '#DEC09A', '#C4B4A7', '#BEBAAF']
    
    if request.method == 'POST':
        name = request.form.get('folder_name', '').strip()
        desc = request.form.get('description', '').strip()
        icon = request.form.get('icon', 'folder')
        color = request.form.get('color', '#ECD9B9')
        
        # Validation - name must be at least 2 characters
        if not name or len(name) < 2:
            flash('Folder name must be at least 2 characters.', 'error')
            return render_template('folder/create.html', icons=icons, colors=colors)
        
        # Check for duplicate folder name for this user
        if Folder.query.filter_by(user_id=user_id, folder_name=name).first():
            flash('Folder with this name already exists.', 'error')
            return render_template('folder/create.html', icons=icons, colors=colors)
        
        # Create and save new folder
        folder = Folder(user_id=user_id, folder_name=name, description=desc, icon=icon, color=color)
        db.session.add(folder)
        db.session.commit()
        flash('Folder created!', 'success')
        return redirect(url_for('folder_list'))
    
    return render_template('folder/create.html', icons=icons, colors=colors)


# --- VIEW FOLDER ---
# READ - Shows contents of a specific folder
@app.route('/folders/<int:folder_id>')
def folder_view(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    
    # Get all courses in this folder through junction table
    folder_courses = FolderCourse.query.filter_by(folder_id=folder_id).all()
    courses = []
    for fc in folder_courses:
        course = Course.query.get(fc.course_id)
        if course:
            courses.append(course)
    
    return render_template('folder/view.html', folder=folder, courses=courses)


# --- EDIT FOLDER ---
# UPDATE - Modify folder name, description, icon, color
@app.route('/folders/<int:folder_id>/edit', methods=['GET', 'POST'])
def folder_edit(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    icons = ['folder', 'heart', 'bookmark', 'star', 'book']
    colors = ['#ECD9B9', '#FFE5C4', '#DEC09A', '#C4B4A7', '#BEBAAF']
    
    if request.method == 'POST':
        name = request.form.get('folder_name', '').strip()
        desc = request.form.get('description', '').strip()
        icon = request.form.get('icon', 'folder')
        color = request.form.get('color', '#ECD9B9')
        
        # Validation
        if not name or len(name) < 2:
            flash('Folder name must be at least 2 characters.', 'error')
        else:
            # Update folder fields
            folder.folder_name = name
            folder.description = desc
            folder.icon = icon
            folder.color = color
            db.session.commit()
            flash('Folder updated!', 'success')
            return redirect(url_for('folder_list'))
    
    return render_template('folder/edit.html', folder=folder, icons=icons, colors=colors)


# --- DELETE FOLDER ---
# DELETE - Remove folder (only if is_deletable=True)
@app.route('/folders/<int:folder_id>/delete', methods=['POST'])
def folder_delete(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    # Preset folders (Liked, Watch Later) can't be deleted
    if not folder.is_deletable:
        flash('This folder cannot be deleted.', 'error')
        return redirect(url_for('folder_list'))
    db.session.delete(folder)
    db.session.commit()
    flash('Folder deleted!', 'success')
    return redirect(url_for('folder_list'))


# ============================================================================
# ADMIN ROUTES
# Admin panel for managing all platform content
# Requires separate admin login (not regular user)
# ============================================================================

# --- ADMIN DASHBOARD ---
# Main admin page with tabs for different content types
@app.route('/admin')
def admin_dashboard():
    # Check if admin is logged in
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    # Get active tab from URL (default to overview)
    active_tab = request.args.get('tab', 'overview')
    
    # Fetch all data for all tabs
    users = User.query.order_by(User.date_joined.desc()).all()
    courses = Course.query.order_by(Course.date_created.desc()).all()
    templates = Template.query.order_by(Template.usage_count.desc()).all()
    folders = Folder.query.order_by(Folder.date_created.desc()).all()
    faqs = FAQ.query.order_by(FAQ.date_created.desc()).all()
    messages = ContactMessage.query.order_by(ContactMessage.date_created.desc()).all()
    announcements = BroadcastNotification.query.order_by(BroadcastNotification.created_at.desc()).all()
    
    return render_template('admin/dashboard.html',
                         active_tab=active_tab,
                         users=users,
                         courses=courses,
                         templates=templates,
                         folders=folders,
                         faqs=faqs,
                         messages=messages,
                         announcements=announcements,
                         user_count=len(users),
                         course_count=len(courses),
                         template_count=len(templates),
                         folder_count=len(folders),
                         faq_count=len(faqs),
                         message_count=len(messages),
                         announcement_count=len(announcements))


# --- ADMIN LOGIN ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        admin = Admin.query.filter_by(username=username).first()
        # Check hashed password
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_logged_in'] = True
            session['admin_username'] = admin.username
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('admin/login.html')


# --- ADMIN LOGOUT ---
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))


# ============================================================================
# ADMIN FAQ MANAGEMENT (Full CRUD)
# ============================================================================

# READ - List all FAQs
@app.route('/admin/faqs')
def admin_faq_list():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    faqs = FAQ.query.order_by(FAQ.date_created.desc()).all()
    return render_template('admin/faq_list.html', faqs=faqs)


# CREATE - Add new FAQ
@app.route('/admin/faqs/create', methods=['GET', 'POST'])
def admin_faq_create():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    categories = ['General', 'Account', 'Courses', 'Technical']
    
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        answer = request.form.get('answer', '').strip()
        category = request.form.get('category', '').strip()
        
        # Validation with specific error messages
        errors = []
        if len(question) < 10:
            errors.append('Question must be at least 10 characters.')
        if len(answer) < 20:
            errors.append('Answer must be at least 20 characters.')
        if category not in categories:
            errors.append('Select a valid category.')
        
        if errors:
            for e in errors:
                flash(e, 'error')
        else:
            faq = FAQ(question=question, answer=answer, category=category)
            db.session.add(faq)
            db.session.commit()
            flash('FAQ created!', 'success')
            return redirect(url_for('admin_faq_list'))
    
    return render_template('admin/faq_create.html', categories=categories)


# UPDATE - Edit existing FAQ
@app.route('/admin/faqs/<int:faq_id>/edit', methods=['GET', 'POST'])
def admin_faq_edit(faq_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    faq = FAQ.query.get_or_404(faq_id)
    categories = ['General', 'Account', 'Courses', 'Technical']
    
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        answer = request.form.get('answer', '').strip()
        category = request.form.get('category', '').strip()
        is_active = request.form.get('is_active') == 'on'
        
        if len(question) >= 10 and len(answer) >= 20 and category in categories:
            faq.question = question
            faq.answer = answer
            faq.category = category
            faq.is_active = is_active
            db.session.commit()
            flash('FAQ updated!', 'success')
            return redirect(url_for('admin_faq_list'))
        flash('Please check all fields.', 'error')
    
    return render_template('admin/faq_edit.html', faq=faq, categories=categories)


# DELETE - Remove FAQ
@app.route('/admin/faqs/<int:faq_id>/delete', methods=['POST'])
def admin_faq_delete(faq_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    faq = FAQ.query.get_or_404(faq_id)
    db.session.delete(faq)
    db.session.commit()
    flash('FAQ deleted!', 'success')
    return redirect(url_for('admin_dashboard', tab='faqs'))


# ============================================================================
# ADMIN USER MANAGEMENT
# ============================================================================

# DELETE - Remove user and their related data
@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
def admin_user_delete(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    user = User.query.get_or_404(user_id)
    # Delete user's folders and progress records first (foreign key constraint)
    Folder.query.filter_by(user_id=user_id).delete()
    UserProgress.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    flash('User deleted!', 'success')
    return redirect(url_for('admin_dashboard', tab='users'))


# UPDATE - Edit user details
@app.route('/admin/users/<int:user_id>/edit', methods=['POST'])
def admin_user_edit(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    user = User.query.get_or_404(user_id)
    user.username = request.form.get('username', user.username)
    user.email = request.form.get('email', user.email)
    user.user_type = request.form.get('user_type', user.user_type)
    user.role = request.form.get('role', user.role)
    db.session.commit()
    flash('User updated!', 'success')
    return redirect(url_for('admin_dashboard', tab='users'))


# ============================================================================
# ADMIN COURSE MANAGEMENT (Full CRUD)
# ============================================================================

# CREATE - Add new course
@app.route('/admin/courses/create', methods=['POST'])
def admin_course_create():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    title = request.form.get('title', '').strip()
    instructor = request.form.get('instructor_name', '').strip()
    category = request.form.get('category', '').strip()
    color = request.form.get('color', '#FEFAF1')
    
    # Validation - all required fields
    if title and instructor and category:
        course = Course(title=title, instructor_name=instructor, category=category, color=color)
        db.session.add(course)
        db.session.commit()
        flash('Course created!', 'success')
    else:
        flash('All fields are required.', 'error')
    return redirect(url_for('admin_dashboard', tab='courses'))


# UPDATE - Edit course
@app.route('/admin/courses/<int:course_id>/edit', methods=['POST'])
def admin_course_edit(course_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    course = Course.query.get_or_404(course_id)
    course.title = request.form.get('title', course.title)
    course.instructor_name = request.form.get('instructor_name', course.instructor_name)
    course.category = request.form.get('category', course.category)
    course.color = request.form.get('color', course.color)
    db.session.commit()
    flash('Course updated!', 'success')
    return redirect(url_for('admin_dashboard', tab='courses'))


# DELETE - Remove course and related records
@app.route('/admin/courses/<int:course_id>/delete', methods=['POST'])
def admin_course_delete(course_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    course = Course.query.get_or_404(course_id)
    # Remove from all folders and progress tracking first
    FolderCourse.query.filter_by(course_id=course_id).delete()
    UserProgress.query.filter_by(course_id=course_id).delete()
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted!', 'success')
    return redirect(url_for('admin_dashboard', tab='courses'))


# ============================================================================
# ADMIN TEMPLATE MANAGEMENT
# CRUD operations for templates through admin panel
# ============================================================================

# CREATE - Add new template
@app.route('/admin/templates/create', methods=['POST'])
def admin_template_create():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    title = request.form.get('title', '').strip()
    category = request.form.get('category', '').strip()
    description = request.form.get('description', '').strip()
    color = request.form.get('color', '#FEFAF1')
    
    if title and category:
        template = Template(title=title, category=category, description=description, color=color)
        db.session.add(template)
        db.session.commit()
        flash('Template created!', 'success')
    else:
        flash('Title and category are required.', 'error')
    return redirect(url_for('admin_dashboard', tab='templates'))


# UPDATE - Edit template
@app.route('/admin/templates/<int:template_id>/edit', methods=['POST'])
def admin_template_edit(template_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    template = Template.query.get_or_404(template_id)
    template.title = request.form.get('title', template.title)
    template.category = request.form.get('category', template.category)
    template.description = request.form.get('description', template.description)
    template.color = request.form.get('color', template.color)
    db.session.commit()
    flash('Template updated!', 'success')
    return redirect(url_for('admin_dashboard', tab='templates'))


# DELETE - Remove template and related records
@app.route('/admin/templates/<int:template_id>/delete', methods=['POST'])
def admin_template_delete(template_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    template = Template.query.get_or_404(template_id)
    # Remove from all folders and progress tracking first
    FolderTemplate.query.filter_by(template_id=template_id).delete()
    TemplateProgress.query.filter_by(template_id=template_id).delete()
    db.session.delete(template)
    db.session.commit()
    flash('Template deleted!', 'success')
    return redirect(url_for('admin_dashboard', tab='templates'))


# ============================================================================
# ADMIN FOLDER MANAGEMENT
# ============================================================================

# DELETE - Remove folder
@app.route('/admin/folders/<int:folder_id>/delete', methods=['POST'])
def admin_folder_delete(folder_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    folder = Folder.query.get_or_404(folder_id)
    FolderCourse.query.filter_by(folder_id=folder_id).delete()  # Remove folder-course links
    db.session.delete(folder)
    db.session.commit()
    flash('Folder deleted!', 'success')
    return redirect(url_for('admin_dashboard', tab='folders'))


# ============================================================================
# ADMIN MESSAGE MANAGEMENT
# ============================================================================

# DELETE - Remove contact message
@app.route('/admin/messages/<int:message_id>/delete', methods=['POST'])
def admin_message_delete(message_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    message = ContactMessage.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash('Message deleted!', 'success')
    return redirect(url_for('admin_dashboard', tab='messages'))


# UPDATE - Toggle message read/unread status
@app.route('/admin/messages/<int:message_id>/toggle-read', methods=['POST'])
def admin_message_toggle_read(message_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    message = ContactMessage.query.get_or_404(message_id)
    message.is_read = not message.is_read  # Toggle boolean
    db.session.commit()
    return redirect(url_for('admin_dashboard', tab='messages'))


# ============================================================================
# ADMIN ANNOUNCEMENT MANAGEMENT
# ============================================================================

@app.route('/admin/announcements/create', methods=['POST'])
def admin_announcement_create():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    title = request.form.get('title', '').strip()
    message = request.form.get('message', '').strip()
    if not title or not message:
        flash('Announcement title and message are required.', 'error')
        return redirect(url_for('admin_dashboard', tab='announcements'))

    db.session.add(BroadcastNotification(
        title=title,
        message=message,
        created_by=session.get('admin_username', 'admin')
    ))
    db.session.commit()
    flash('Announcement sent to all users.', 'success')
    return redirect(url_for('admin_dashboard', tab='announcements'))


@app.route('/admin/announcements/<int:announcement_id>/delete', methods=['POST'])
def admin_announcement_delete(announcement_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    announcement = BroadcastNotification.query.get_or_404(announcement_id)
    db.session.delete(announcement)
    db.session.commit()
    flash('Announcement deleted.', 'success')
    return redirect(url_for('admin_dashboard', tab='announcements'))


# ============================================================================
# DATABASE INITIALIZATION
# Creates tables and adds sample data on first run
# ============================================================================
def init_db():
    with app.app_context():
        # Initialize SocialHub models and routes BEFORE create_all
        sh_models = init_sh_models(db)
        init_socialhub_routes(db, sh_models, User)
        SHUser, SHPost, SHComment, SHLike, SHPrivateMessage = sh_models
        
        db.create_all()  # Create all tables based on models
        
        # Add sample FAQs if empty
        if FAQ.query.count() == 0:
            faqs = [
                FAQ(question='What is BridgeHive?', answer='BridgeHive is a platform connecting youth and seniors through shared learning experiences.', category='General'),
                FAQ(question='How do I create an account?', answer='Click Sign Up on our landing page and choose whether you are a Youth or Senior to get started.', category='Account'),
                FAQ(question='How do I join a course?', answer='Browse our course library, find one you like, and click Enroll to begin your learning journey.', category='Courses'),
                FAQ(question='Is BridgeHive free?', answer='Yes! BridgeHive is completely free for all users to learn and teach.', category='General'),
                FAQ(question='How do I contact support?', answer='You can reach our support team through the Contact page or use our chatbot for quick help.', category='Technical'),
                FAQ(question='Can I create my own course?', answer='Absolutely! Both youth and seniors can create and share courses through the Create menu.', category='Courses'),
            ]
            db.session.add_all(faqs)
        
        # Add demo user (learner) if no users exist
        if User.query.count() == 0:
            # Demo learner user
            learner = User(username='John', email='john@example.com', password='demo123', user_type='youth', 
                          role='learner', streak_days=6, is_new_user=False, learning_interests='Cooking, Technology')
            db.session.add(learner)
            db.session.flush()
            
            # Create settings for learner
            db.session.add(UserSettings(user_id=learner.id))
            
            # Create default folders for learner
            learner_folders = [
                Folder(user_id=learner.id, folder_name='Liked Courses', folder_type='preset', icon='heart', color='#ECD9B9', is_deletable=False),
                Folder(user_id=learner.id, folder_name='Watch Later', folder_type='preset', icon='bookmark', color='#FFE5C4', is_deletable=False),
            ]
            db.session.add_all(learner_folders)
            
            # Demo mentor user
            mentor = User(username='Sarah', email='sarah@example.com', password='demo123', user_type='youth',
                         role='mentor', streak_days=4, is_new_user=False, teaching_interests='Cooking, Arts & Creativity, Language')
            db.session.add(mentor)
            db.session.flush()
            
            # Create settings for mentor
            db.session.add(UserSettings(user_id=mentor.id))
            
            # Create default folders for mentor
            mentor_folders = [
                Folder(user_id=mentor.id, folder_name='Liked Templates', folder_type='preset', icon='heart', color='#ECD9B9', is_deletable=False),
                Folder(user_id=mentor.id, folder_name='Use Later', folder_type='preset', icon='bookmark', color='#FFE5C4', is_deletable=False),
            ]
            db.session.add_all(mentor_folders)
            
            # Demo both (learner & mentor) user
            both_user = User(username='Alex', email='alex@example.com', password='demo123', user_type='youth',
                            role='both', streak_days=8, is_new_user=False, 
                            learning_interests='Technology, Finance', teaching_interests='Language, Health & Wellness')
            db.session.add(both_user)
            db.session.flush()
            
            # Create settings for both user
            db.session.add(UserSettings(user_id=both_user.id))
            
            # Create default folders for both user (all 4 folders)
            both_folders = [
                Folder(user_id=both_user.id, folder_name='Liked Courses', folder_type='preset', icon='heart', color='#ECD9B9', is_deletable=False),
                Folder(user_id=both_user.id, folder_name='Watch Later', folder_type='preset', icon='bookmark', color='#FFE5C4', is_deletable=False),
                Folder(user_id=both_user.id, folder_name='Liked Templates', folder_type='preset', icon='heart', color='#DEC09A', is_deletable=False),
                Folder(user_id=both_user.id, folder_name='Use Later', folder_type='preset', icon='bookmark', color='#C4B4A7', is_deletable=False),
            ]
            db.session.add_all(both_folders)
        
        # Reset and add sample courses (21 courses across 7 categories)
        Course.query.delete()
        courses = [
            # Courses matching Courses Library (port 8080) - 13 courses across 8 categories
            # Cooking (1)
            Course(title='Traditional Peranakan Cooking', instructor_name='Mrs. Wong Mei Ling', category='Cooking', color='#FEFAF1', library_id=1,
                   description='Master the art of Nyonya cuisine with secret family recipes passed down for 50 years. Learn to make Laksa and Kueh Pie Tee.',
                   image_url='https://images.unsplash.com/photo-1563865436874-9aef32095fad?q=80&w=800'),
            # Technology (4)
            Course(title='Social Media for Beginners', instructor_name='Sarah Ng', category='Technology', color='#FFE5C4', library_id=2,
                   description='Don\'t get left behind! Connect with your grandchildren on Instagram and TikTok. Safety and privacy focused.',
                   image_url='https://images.unsplash.com/photo-1611162617474-5b21e879e113?q=80&w=800'),
            Course(title='Social Media Mastery for Seniors', instructor_name='Sarah Ng', category='Technology', color='#ECD9B9', library_id=5,
                   description='Don\'t get left behind! Connect with your grandchildren and friends on Instagram, TikTok, and Facebook.',
                   image_url='https://images.unsplash.com/photo-1562577309-4932fdd64cd1?q=80&w=800'),
            Course(title='Excel & Spreadsheet Mastery', instructor_name='Michael Wong', category='Technology', color='#DEC09A', library_id=8,
                   description='Master Excel like a pro! Learn formulas, data analysis, pivot tables, and automation.',
                   image_url='https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=800'),
            Course(title='Introduction to AI & Machine Learning', instructor_name='Dr. Priya Sharma', category='Technology', color='#C4B4A7', library_id=13,
                   description='Demystify artificial intelligence! Learn the basics of AI, machine learning, and how they\'re transforming our world.',
                   image_url='https://images.unsplash.com/photo-1677442136019-21780ecad995?q=80&w=800'),
            # Language (2)
            Course(title='Conversational Malay', instructor_name='Siti Fatimah', category='Language', color='#BEBAAF', library_id=3,
                   description='Learn the language of the community. Bridge cultural gaps today with essential phrases.',
                   image_url='https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?q=80&w=800'),
            Course(title='Conversational Malay for Beginners', instructor_name='Siti Fatimah', category='Language', color='#8F7B6A', library_id=6,
                   description='Learn the language of the community and bridge cultural gaps. Master essential phrases, pronunciation, and daily conversations.',
                   image_url='https://images.unsplash.com/photo-1457369804613-52c61a468e7d?q=80&w=800'),
            # Sports & Fitness (1)
            Course(title='Modern Football Tactics', instructor_name='Coach Marcus Thompson', category='Sports & Fitness', color='#FEFAF1', library_id=4,
                   description='Master modern football strategy and tactics! Learn attacking play, defensive organization, and set pieces.',
                   image_url='https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?q=80&w=800'),
            # Arts & Creativity (2)
            Course(title='Digital Photography Fundamentals', instructor_name='David Chen', category='Arts & Creativity', color='#FFE5C4', library_id=7,
                   description='Discover the art of photography! Learn composition, lighting, camera settings, and post-processing.',
                   image_url='https://images.unsplash.com/photo-1542038784456-1ea8e935640e?q=80&w=800'),
            Course(title='Creative Writing Essentials', instructor_name='Elizabeth Foster', category='Arts & Creativity', color='#ECD9B9', library_id=10,
                   description='Unleash your creativity! Learn storytelling, character development, dialogue, and plot structure.',
                   image_url='https://images.unsplash.com/photo-1455390582262-044cdead277a?q=80&w=800'),
            # Health & Wellness (1)
            Course(title='Mindfulness & Meditation for Wellness', instructor_name='Aisha Kumar', category='Health & Wellness', color='#DEC09A', library_id=9,
                   description='Reduce stress and improve mental clarity through guided meditation and mindfulness practices.',
                   image_url='https://images.unsplash.com/photo-1506126613408-eca07ce68773?q=80&w=800'),
            # Gardening (1)
            Course(title='Home Gardening & Urban Farming', instructor_name='Mr. Raj Patel', category='Gardening', color='#C4B4A7', library_id=11,
                   description='Grow your own food in limited spaces! Learn about composting, plant care, seasonal gardening, and organic techniques.',
                   image_url='https://images.unsplash.com/photo-1416879595882-3373a0480b5b?q=80&w=800'),
            # Finance (1)
            Course(title='Personal Finance & Investing Basics', instructor_name='Dr. James Mitchell', category='Finance', color='#BEBAAF', library_id=12,
                   description='Take control of your money! Learn budgeting, saving, investing, and financial planning.',
                   image_url='https://images.unsplash.com/photo-1554224155-6726b3ff858f?q=80&w=800'),
        ]
        db.session.add_all(courses)
        
        # Reset and add sample templates matching courses library categories
        Template.query.delete()
        templates = [
            # Cooking Templates (2)
            Template(title='Recipe Sharing Framework', description='A structured template for sharing traditional recipes with step-by-step instructions and ingredient lists.', category='Cooking', color='#FEFAF1', usage_count=45),
            Template(title='Cooking Tutorial Guide', description='Create engaging cooking tutorials with video placeholders and timing guides.', category='Cooking', color='#FFE5C4', usage_count=38),
            # Technology Templates (2)
            Template(title='Digital Basics Tutorial', description='Step-by-step template for teaching smartphone, social media, and computer basics.', category='Technology', color='#ECD9B9', usage_count=89),
            Template(title='AI & Tech Concepts Course', description='Template for building courses on AI, machine learning, and emerging technologies.', category='Technology', color='#DEC09A', usage_count=72),
            # Language Templates (2)
            Template(title='Language Learning Course', description='Structured template for teaching conversational language skills with phrase guides and pronunciation tips.', category='Language', color='#C4B4A7', usage_count=56),
            Template(title='Cultural Exchange Workshop', description='Template for facilitating cross-cultural dialogue and language immersion activities.', category='Language', color='#BEBAAF', usage_count=44),
            # Sports & Fitness Templates (2)
            Template(title='Sports Tactics Workshop', description='Template for teaching sports strategy, formations, and game analysis techniques.', category='Sports & Fitness', color='#8F7B6A', usage_count=41),
            Template(title='Fitness & Wellness Plan', description='Structured template for creating exercise routines and physical wellness programs.', category='Sports & Fitness', color='#FEFAF1', usage_count=35),
            # Arts & Creativity Templates (2)
            Template(title='Photography Masterclass', description='Template for teaching photography composition, lighting, and editing techniques.', category='Arts & Creativity', color='#FFE5C4', usage_count=43),
            Template(title='Creative Writing Workshop', description='Structured template for teaching storytelling, character development, and narrative craft.', category='Arts & Creativity', color='#ECD9B9', usage_count=37),
            # Health & Wellness Templates (2)
            Template(title='Mindfulness Course Builder', description='Template for creating guided meditation and mindfulness practice sessions.', category='Health & Wellness', color='#DEC09A', usage_count=52),
            Template(title='Wellness Journey Guide', description='Template for building holistic wellness programs covering mental and physical health.', category='Health & Wellness', color='#C4B4A7', usage_count=33),
            # Gardening Templates (2)
            Template(title='Garden Planning Course', description='Template for teaching garden layout, composting, and seasonal planting schedules.', category='Gardening', color='#BEBAAF', usage_count=39),
            Template(title='Urban Farming Workshop', description='Step-by-step template for teaching small-space gardening and organic growing techniques.', category='Gardening', color='#8F7B6A', usage_count=28),
            # Finance Templates (2)
            Template(title='Financial Literacy Course', description='Comprehensive template for teaching budgeting, saving, and investment fundamentals.', category='Finance', color='#FEFAF1', usage_count=67),
            Template(title='Retirement Planning Guide', description='Template for creating courses on long-term financial planning and wealth management.', category='Finance', color='#FFE5C4', usage_count=48),
        ]
        db.session.add_all(templates)
        
        # Add admin account if none exists
        if Admin.query.count() == 0:
            admin = Admin(username='admin', password_hash=generate_password_hash('admin123'))
            db.session.add(admin)
        
        # --- SocialHub seed data ---
        if SHUser.query.count() == 0:
            sh_u1 = SHUser(username="Jason_Youth")
            sh_u2 = SHUser(username="Grandma_Lee")
            sh_u3 = SHUser(username="Uncle_Tan")
            db.session.add_all([sh_u1, sh_u2, sh_u3])
            db.session.flush()  # get IDs before creating posts
            
            sh_p1 = SHPost(
                body="Just finished teaching the 'Digital Banking 101' workshop! It was so heartwarming to see everyone set up their PayNow for the first time.",
                author=sh_u1, post_type="general"
            )
            sh_p2 = SHPost(
                body="Finally mastered the Zoom mute button! Thank you Jason for the patient guidance. Here is a photo of my orchid blooming today.",
                author=sh_u2, post_type="course_completed", related_course="Smartphone Basics"
            )
            sh_p3 = SHPost(
                body="Does anyone have a good recipe for Sambal Kang Kong? My harvest is ready!",
                author=sh_u2, post_type="general"
            )
            db.session.add_all([sh_p1, sh_p2, sh_p3])
            print("--- SocialHub seed data created ---")
        
        # --- Shop Items seed data ---
        if ShopItem.query.count() == 0:
            items = [
                ("Cosmic Galaxy Ring", "avatar-decoration", 500, "legendary", "bi-vinyl"),
                ("Cherry Blossom Wreath", "avatar-decoration", 300, "epic", "bi-flower1"),
                ("Inferno Ring", "avatar-decoration", 400, "epic", "bi-fire"),
                ("Frost Crystal Frame", "avatar-decoration", 350, "rare", "bi-snow"),
                ("Northern Lights", "profile-effect", 600, "legendary", "bi-stars"),
                ("Golden Dust", "profile-effect", 250, "rare", "bi-magic"),
                ("Shooting Stars", "profile-effect", 400, "epic", "bi-star-fill"),
                ("Rainbow Messages", "chat-effect", 350, "epic", "bi-chat-heart-fill"),
                ("Confetti Burst", "chat-effect", 300, "rare", "bi-cone-striped"),
                ("Royal Elegance", "nameplate", 500, "legendary", "bi-card-heading"),
                ("Neon Cyberpunk", "nameplate", 450, "epic", "bi-cpu-fill"),
                ("Vintage Classic", "nameplate", 350, "rare", "bi-postcard-fill"),
                ("Ultimate Hive Bundle", "bundle", 1500, "legendary", "bi-box-seam-fill"),
            ]
            for name, cat, price, rarity, icon in items:
                item = ShopItem(name=name, category=cat, price=price, rarity=rarity, icon=icon)
                db.session.add(item)
            print("--- Shop items seed data created ---")
        
        # --- Quests seed data ---
        if Quest.query.count() == 0:
            quests_data = [
                ("Introduction to Scams", "Learn how to identify and avoid digital scams.", 50,
                 "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800",
                 "https://www.youtube-nocookie.com/embed/cRUpM9MS3-k", "CyberSafe SG"),
                ("Digital Banking Safety", "Essential tips for secure online banking.", 75,
                 "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=800",
                 "https://www.youtube.com/embed/dQw4w9WgXcQ", "Bank Smart SG"),
                ("Social Media Privacy", "Protect your personal information on social platforms.", 60,
                 "https://images.unsplash.com/photo-1611162617474-5b21e879e113?w=800",
                 "https://www.youtube.com/embed/dQw4w9WgXcQ", "Privacy First"),
                ("Password Security", "Create strong passwords and manage them safely.", 50,
                 "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800",
                 "https://www.youtube.com/embed/dQw4w9WgXcQ", "SecureLife"),
                ("Phishing Awareness", "Recognize and avoid phishing attempts.", 65,
                 "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800",
                 "https://www.youtube.com/embed/dQw4w9WgXcQ", "SafeWeb"),
                ("Online Shopping Safety", "Shop online securely and avoid scams.", 55,
                 "https://images.unsplash.com/photo-1472851294608-062f824d29cc?w=800",
                 "https://www.youtube.com/embed/dQw4w9WgXcQ", "ShopSafe"),
            ]
            for title, desc, points, banner, video, promo in quests_data:
                quest = Quest(
                    title=title, description=desc, reward_points=points,
                    banner_image=banner, video_url=video, promoted_by=promo,
                    ends_date=datetime.utcnow() + timedelta(days=14)
                )
                db.session.add(quest)
            print("--- Quests seed data created ---")
        else:
            # Update existing Introduction to Scams quest to use correct video URL
            scams_quest = Quest.query.filter_by(title="Introduction to Scams").first()
            if scams_quest and 'youtube.com/embed/cRUpM9MS3-k' in (scams_quest.video_url or ''):
                scams_quest.video_url = "https://www.youtube-nocookie.com/embed/cRUpM9MS3-k"
                db.session.commit()
                print("--- Updated Introduction to Scams video URL ---")
        
        db.session.commit()
        print("Database initialized!")


# ============================================================================
# RUN APPLICATION
# ============================================================================
if __name__ == '__main__':
    init_db()  # Initialize database on startup
    init_lib_db(app)  # Initialize courses library database
    sh_socketio.run(app, debug=True, port=5000)
