"""
Script to create comprehensive quizzes for Modern Football Tactics course
Based on the videos available in static/lib/videos
"""

import sqlite3
import os

# Database path
DB_PATH = os.getenv('LIB_DB_PATH', os.path.join(os.path.dirname(__file__), 'bridgehive_enterprise.db'))

def create_quizzes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Modern Football Tactics course ID is 4
    COURSE_ID = 4
    
    # Get the modules for this course
    cursor.execute('SELECT id, title, order_index FROM modules WHERE course_id = ? ORDER BY order_index', (COURSE_ID,))
    modules = cursor.fetchall()
    
    # MODULE 1: Introduction & Welcome & Defending Principles
    module_1_questions = [
        ("What is the primary objective of the 1v1 defending principle?", 
         "To win the ball by sliding tackle", 
         "To deny the opponent space and force them to make a decision",
         "To push the opponent out of bounds",
         "To commit a tactical foul", 1, 1, 1),
        
        ("In 11v11 defending, what does 'shape' refer to?",
         "The physical appearance of players",
         "The organized positioning of players relative to the ball",
         "The formation number (like 4-3-3)",
         "The colors of the team jersey", 1, 1, 2),
        
        ("When defending 1v1, which body part should you lead with?",
         "Your head",
         "Your shoulders",
         "Your side/hip",
         "Your hands", 2, 1, 3),
        
        ("What is a key principle when defending against a faster opponent?",
         "Always stay goal-side of them",
         "Keep tight on them at all times",
         "Increase physical contact",
         "Push them backwards towards their goal", 0, 1, 4),
        
        ("In team defending, what is 'pressing'?",
         "Reducing the space of the opponent with the ball quickly",
         "Running faster than the opponent",
         "Tackling immediately on contact",
         "Marking the nearest player", 0, 2, 5),
        
        ("When should a defender make a tackle?",
         "Whenever they are near an opponent",
         "Only when instructed by the coach",
         "When they have a high probability of winning the ball",
         "On every opportunity to show effort", 2, 2, 6),
    ]
    
    # MODULE 2: Core Concepts & Attacking Play
    module_2_questions = [
        ("What does 'building the attack' involve?",
         "Scoring goals directly",
         "Creating organized, structured movements to develop attacking play",
         "Running fast with the ball",
         "Passing backwards only", 1, 1, 1),
        
        ("In attacking, what is the primary advantage of width?",
         "To make the field longer",
         "To stay away from defenders",
         "To create space and attacking opportunities at the sides",
         "To confuse the referee", 2, 1, 2),
        
        ("What are set pieces in football?",
         "Pieces of the field that are set in place",
         "Predetermined plays from dead ball situations (corners, free kicks, throw-ins)",
         "Plays that happen when the ball is moving",
         "Defensive formations", 1, 1, 3),
        
        ("Which is NOT an advantage of set pieces?",
         "You can practice and plan specific plays",
         "The ball is stationary when you execute them",
         "They guarantee a goal",
         "You have time to organize your team", 2, 2, 4),
        
        ("What is the 'near post' in a corner kick?",
         "The post farthest from where the corner is taken",
         "The post closest to where the corner is taken",
         "The middle of the goal line",
         "The goal line itself", 1, 1, 5),
        
        ("In a well-executed attacking sequence, what should happen?",
         "Each pass should be longer than the last",
         "Players move into space created by teammates to maintain possession and create scoring chances",
         "The ball should always be played forward",
         "Only the striker touches the ball in the final third", 1, 2, 6),
    ]
    
    # MODULE 3: Practical Application & Match Analysis
    module_3_questions = [
        ("The first step in match analysis is to:",
         "Predict the score",
         "Watch the entire match and observe the team's overall performance",
         "Count the shots on goal",
         "Identify the best player", 1, 1, 1),
        
        ("When analyzing defending in a match, what should you focus on?",
         "How many tackles were made",
         "Positioning, spacing, communication, and ability to stop the opposition's attacking patterns",
         "Only the defenders' running speed",
         "How many fouls were committed", 1, 1, 2),
        
        ("In tactical analysis, 'transition' refers to:",
         "The substitution of players",
         "The moment when possession changes from one team to the other",
         "A tactical formation change",
         "When a player switches sides on the field", 1, 2, 3),
        
        ("What is pressing trigger in match analysis?",
         "Pushing a button to start the analysis",
         "The specific moment or event that causes a team to press the opponent",
         "The pressure from the coach",
         "A training drill", 1, 2, 4),
        
        ("How many key phases of play should be analyzed in a match?",
         "2 (Attack and Defense)",
         "3 (Attacking, Defending, and Transition)",
         "5 (based on player positions)",
         "Unlimited", 1, 1, 5),
        
        ("Which is the BEST way to use video analysis for tactical improvement?",
         "Watch all games without taking notes",
         "Identify specific patterns, weaknesses, and strengths to create targeted training sessions",
         "Show the video to all players without discussion",
         "Only analyze losses, not wins", 1, 2, 6),
        
        ("What does 'spacing' in defensive analysis mean?",
         "The distance between the field lines",
         "The distance and positioning between defending players to cover the field effectively",
         "How spread out the spectators are",
         "The gaps in the stadium seating", 1, 1, 7),
        
        ("In analyzing attacking moves, what indicates effective movement?",
         "All players running towards the goal",
         "Players making runs into space created by ball movement and positional shifts",
         "The quickest possible passing",
         "Direct shots every time", 1, 2, 8),
    ]
    
    # FINAL COURSE QUIZ (Comprehensive)
    final_quiz_questions = [
        ("What are the three main defensive levels in football?",
         "Individual (1v1), Team (small group), and Organizational (11v11)",
         "Pressing, Covering, and Blocking",
         "Tackling, Marking, and Clearances",
         "Formation, Positioning, and Movement", 0, 2, 1),
        
        ("Building an attack requires:",
         "Only the strikers to be involved",
         "Quick one-touch passes",
         "Multiple successful passes that create space and scoring opportunities",
         "The goalkeeper to start every play", 2, 2, 2),
        
        ("What makes set pieces valuable in football?",
         "They are easier to defend",
         "They cannot be defended",
         "Players can rehearse and practice specific organized plays with clear objectives",
         "They are less important than open play", 2, 2, 3),
        
        ("When analyzing a match, the three main phases are:",
         "First half, Second half, Extra time",
         "Attack, Defense, and Transition",
         "Beginning, Middle, and End",
         "Goals, Cards, and Substitutions", 1, 2, 4),
        
        ("A successful defending transition means:",
         "Changing to a different formation",
         "Immediately pressing when possession is lost",
         "Quickly reorganizing to prevent the opposition from exploiting the transition moment",
         "Fouling the player with the ball", 2, 2, 5),
        
        ("In a pressing strategy, the 'trigger' timing is crucial because:",
         "It defines when players must sprint",
         "It coordinates when the team begins to pressure the opponent",
         "It tells when to change formations",
         "It signals when to commit fouls", 1, 2, 6),
        
        ("How should a team analyze their own attacking play?",
         "Only count the number of shots",
         "Evaluate how well they created space, moved into position, and converted chances",
         "Focus only on individual player skills",
         "Just look at the final score", 1, 2, 7),
        
        ("What is the relationship between spacing and team defense?",
         "Spacing makes defense weaker",
         "Good spacing between players allows better coverage, communication, and defensive support",
         "Spacing is only for attackers",
         "Spacing is irrelevant to defense", 1, 2, 8),
        
        ("Which tactic helps prevent the opposition from building an attack effectively?",
         "Giving them space to pass",
         "Early pressing and denying time on the ball with good positioning",
         "Only defending near your own goal",
         "Always committing all players forward", 1, 2, 9),
        
        ("After completing this course, you should be able to:",
         "Play professional football",
         "Analyze and understand modern football tactics at both individual and team levels",
         "Coach any team immediately",
         "Guarantee all matches will be won", 1, 3, 10),
    ]
    
    try:
        # Insert Module 1 Quiz Questions
        if modules:
            module_1_id = modules[0][0]
            for q in module_1_questions:
                cursor.execute('''INSERT INTO quiz_questions 
                    (course_id, module_id, question_text, option_a, option_b, option_c, option_d, 
                     correct_index, difficulty, order_index)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (COURSE_ID, module_1_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7]))
            print(f"[OK] Added {len(module_1_questions)} questions for Module 1: Introduction & Welcome")
        
        # Insert Module 2 Quiz Questions
        if len(modules) > 1:
            module_2_id = modules[1][0]
            for q in module_2_questions:
                cursor.execute('''INSERT INTO quiz_questions 
                    (course_id, module_id, question_text, option_a, option_b, option_c, option_d, 
                     correct_index, difficulty, order_index)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (COURSE_ID, module_2_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7]))
            print(f"[OK] Added {len(module_2_questions)} questions for Module 2: Core Concepts")
        
        # Insert Module 3 Quiz Questions
        if len(modules) > 2:
            module_3_id = modules[2][0]
            for q in module_3_questions:
                cursor.execute('''INSERT INTO quiz_questions 
                    (course_id, module_id, question_text, option_a, option_b, option_c, option_d, 
                     correct_index, difficulty, order_index)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (COURSE_ID, module_3_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7]))
            print(f"[OK] Added {len(module_3_questions)} questions for Module 3: Practical Application")
        
        # Insert Final Course Quiz (without module_id)
        for q in final_quiz_questions:
            cursor.execute('''INSERT INTO quiz_questions 
                (course_id, module_id, question_text, option_a, option_b, option_c, option_d, 
                 correct_index, difficulty, order_index)
                VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (COURSE_ID, q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7]))
        print(f"[OK] Added {len(final_quiz_questions)} questions for Final Course Assessment")
        
        conn.commit()
        print("\n[SUCCESS] All quizzes created successfully!")
        print("\n[SUMMARY] Quiz Summary:")
        print(f"   - Module 1: {len(module_1_questions)} questions (Difficulty: 1-2)")
        print(f"   - Module 2: {len(module_2_questions)} questions (Difficulty: 1-2)")
        print(f"   - Module 3: {len(module_3_questions)} questions (Difficulty: 1-2)")
        print(f"   - Final Assessment: {len(final_quiz_questions)} questions (Difficulty: 2-3)")
        print(f"\n[PASSSCORE] Passing Score: 80%")
        print(f"[COURSE] Modern Football Tactics (ID: {COURSE_ID})")
        
    except Exception as e:
        print(f"[ERROR] Error creating quizzes: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    create_quizzes()
