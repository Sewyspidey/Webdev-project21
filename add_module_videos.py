"""
Script to add videos to Modern Football Tactics course modules
Maps video files from static/lib/videos to course modules
"""

import sqlite3
import os

DB_PATH = os.getenv('LIB_DB_PATH', os.path.join(os.path.dirname(__file__), 'bridgehive_enterprise.db'))

# Video mapping to modules
VIDEOS = {
    # Module 1: Introduction & Welcome (ID 10) - Defending Principles
    10: {
        'title': 'Soccer TRAINING - Principles of Defending 1v1 to 11v11',
        'filename': 'Soccer TRAINING - Principles of Defending 1v1 to 11v11 Part 1.mp4',
        'description': 'Learn the fundamental principles of defensive play at all levels - from one-on-one defending to full team organization. Master positioning, communication, and tactical awareness.',
        'duration': 45
    },
    # Module 2: Core Concepts & Fundamentals (ID 11) - Attacking & Set Pieces  
    11: {
        'title_part1': 'Building The Attack - FA Learning Coaching Session',
        'filename_part1': 'Building The Attack   FA Learning Coaching Session From David Powderly.mp4',
        'description_part1': 'Discover how to structure attacking play and build effective attacking movements. Learn from Coach David Powderly.',
        'duration_part1': 35,
        'title_part2': 'Football Tactics 101 - Set Pieces',
        'filename_part2': 'Football Tactics 101 What are Set Pieces How to use them to your advantage.mp4',
        'description_part2': 'Master set piece tactics - corners, free kicks, and throw-ins. Learn how to use these scoring opportunities.',
        'duration_part2': 25
    },
    # Module 3: Practical Application Workshop (ID 12) - Match Analysis
    12: {
        'title': 'How to ANALYSE a Football Match - Step-By-Step Guide',
        'filename': 'How to ANALYSE a football match (Step-By-Step Guide).mp4',
        'description': 'Learn systematic approach to analyzing football matches. Understand tactical patterns, player positioning, and match dynamics.',
        'duration': 50
    }
}

# External video links (YouTube) to replace local files
EXTERNAL = {
    # embed versions so they play inside iframes; start=675 seconds corresponds
    # to the original timestamp parameter
    10: [
        'https://www.youtube.com/embed/-MIewD-cW_I'
    ],
    # reuse the same embedded link for all modules for now
    11: [
        'https://www.youtube.com/embed/x_H_Q-tJVS8',
        'https://www.youtube.com/embed/x_H_Q-tJVS8'
    ],
    12: [
        'https://www.youtube.com/embed/KQGS5HR8JTQ?start=675'
    ],
}

def add_module_videos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("ADDING VIDEOS TO MODERN FOOTBALL TACTICS MODULES")
    print("=" * 60)
    
    try:
        # Module 1: Introduction & Welcome with Defending video
        module_id = 10
        course_id = 4
        video = VIDEOS[module_id]
        
        # determine URL (external if configured, otherwise local file)
        if module_id in EXTERNAL:
            # use first external link for module resource, but still insert all
            ext_links = EXTERNAL[module_id]
            resource_url = ext_links[0]
            video_url = ext_links[0]
        else:
            video_url = f'videos/{video["filename"]}'  # Relative path for Flask static
            resource_url = f'/static/lib/videos/{video["filename"]}'  # Full URL for learning_resources
        
        cursor.execute('''INSERT INTO learning_resources 
            (course_id, resource_type, title, description, url, duration_mins, content_approved)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (course_id, 'video', video['title'], video['description'], resource_url, video['duration'], 1))
        
        # Update module with video URL (relative path or external link)
        cursor.execute('''UPDATE modules SET resource_url = ?, duration_mins = ? WHERE id = ?''',
            (video_url, video['duration'], module_id))
        
        print(f"[Module 1] Added: {video['title']}")
        print(f"  Duration: {video['duration']} minutes")
        print(f"  Module URL: {video_url}\n")
        
        # Module 2: Core Concepts with two videos
        module_id = 11
        module_videos = [
            {
                'title': VIDEOS[module_id]['title_part1'],
                'filename': VIDEOS[module_id]['filename_part1'],
                'description': VIDEOS[module_id]['description_part1'],
                'duration': VIDEOS[module_id]['duration_part1']
            },
            {
                'title': VIDEOS[module_id]['title_part2'],
                'filename': VIDEOS[module_id]['filename_part2'],
                'description': VIDEOS[module_id]['description_part2'],
                'duration': VIDEOS[module_id]['duration_part2']
            }
        ]
        
        total_duration = 0
        links = EXTERNAL.get(module_id)
        for i, video in enumerate(module_videos, 1):
            if links and i <= len(links):
                video_url_full = links[i-1]
                resource_url = links[i-1]
            else:
                video_url_full = f'/static/lib/videos/{video["filename"]}'
                resource_url = video_url_full

            cursor.execute('''INSERT INTO learning_resources 
                (course_id, resource_type, title, description, url, duration_mins, content_approved)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (course_id, 'video', video['title'], video['description'], resource_url, video['duration'], 1))

            print(f"[Module 2.{i}] Added: {video['title']}")
            print(f"  Duration: {video['duration']} minutes")
            total_duration += video['duration']
        
        # Use first video/external link as primary resource_url
        if links and len(links) > 0:
            first_video_url = links[0]
        else:
            first_video_url = f'videos/{module_videos[0]["filename"]}'
        cursor.execute('''UPDATE modules SET resource_url = ?, duration_mins = ? WHERE id = ?''',
            (first_video_url, total_duration, module_id))
        print(f"  Total duration: {total_duration} minutes\n")
        
        # Module 3: Practical Application with Match Analysis video
        module_id = 12
        video = VIDEOS[module_id]
        
        if module_id in EXTERNAL:
            video_url = EXTERNAL[module_id][0]
            resource_url_full = EXTERNAL[module_id][0]
        else:
            video_url = f'videos/{video["filename"]}'  # Relative path for Flask static
            resource_url_full = f'/static/lib/videos/{video["filename"]}'  # Full URL for learning_resources
        
        cursor.execute('''INSERT INTO learning_resources 
            (course_id, resource_type, title, description, url, duration_mins, content_approved)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (course_id, 'video', video['title'], video['description'], resource_url_full, video['duration'], 1))
        
        cursor.execute('''UPDATE modules SET resource_url = ?, duration_mins = ? WHERE id = ?''',
            (video_url, video['duration'], module_id))
        
        print(f"[Module 3] Added: {video['title']}")
        print(f"  Duration: {video['duration']} minutes")
        print(f"  Module URL: {video_url}\n")
        
        conn.commit()
        print("=" * 60)
        print("SUCCESS: All videos added to modules!")
        print("\nModule Summary:")
        print("  Module 1: Introduction & Welcome - 45 min video")
        print("  Module 2: Core Concepts - 60 min (2 videos)")
        print("  Module 3: Practical Application - 50 min video")
        print("\nTotal Course Video Time: 155 minutes")
        
    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    add_module_videos()
