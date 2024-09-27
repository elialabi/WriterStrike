import os
from flask import Flask, request, render_template, redirect, url_for, session, jsonify, flash
import openai
import pymysql
import ssl
import re 
from werkzeug.security import generate_password_hash, check_password_hash
import json
import logging  
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

app = Flask(__name__, static_folder='static')
CORS(app)  
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.urandom(24).hex()

# Set OpenAI API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Database connection
def get_connection():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    connection = pymysql.connect(
        host='gateway01.eu-central-1.prod.aws.tidbcloud.com',
        port=4000,
        user='coMP9hperszXc6a.root',
        password='AFRmGLwwVc05PDZO',
        db='feedback_system',
        ssl={'ssl': ssl_context},
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

# Helper to extract sections from AI response
def extract_section(text, section_name):
    pattern = rf"{section_name}s?:?\s*(.*?)(?=(?:\n\n|\Z))"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        content = match.group(1).strip()
        # Remove the "ies:" prefix if it exists
        content = re.sub(r'^ies:\s*', '', content)
        return content if content and not content.lower().startswith("none") else "None observed."
    return "None observed."

# Retrieve context from the database for a specific user
def get_user_context(user_id):
    connection = get_connection()
    context = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM contexts WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", (user_id,))
            context = cursor.fetchone()
    except Exception as e:
        print(f"Error retrieving context: {str(e)}")
    finally:
        connection.close()
    return context

# Landing page
@app.route('/')
def index():
    return render_template('index.html')

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, email, hashed_password)
                    VALUES (%s, %s, %s);
                """, (username, email, hashed_password))
                connection.commit()
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            connection.close()

        return redirect(url_for('login'))
    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT user_id, username, hashed_password FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                if user and check_password_hash(user['hashed_password'], password):
                    session['user_id'] = user['user_id']
                    return redirect(url_for('stories'))
                else:
                    return jsonify({'error': 'Invalid username or password'}), 401
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            connection.close()
    return render_template('login.html')

# Store context in the database
@app.route('/context_form/<int:story_id>', methods=['GET', 'POST'])
def context_form(story_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = get_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT title FROM stories WHERE story_id = %s", (story_id,))
            story = cursor.fetchone()
            story_title = story['title'] if story else "Unknown Story"

            if request.method == 'POST':
                form_data = request.form.to_dict()
                form_data['user_id'] = session['user_id']
                form_data['script_id'] = story_id

                cursor.execute("""
                    INSERT INTO contexts 
                    (user_id, script_id, work_type, genre, target_audience, time_period, 
                    primary_language, realism_level, additional_context)
                    VALUES (%(user_id)s, %(script_id)s, %(work_type)s, %(genre)s, %(target_audience)s,
                    %(time_period)s, %(primary_language)s, %(realism_level)s, %(additional_context)s)
                    ON DUPLICATE KEY UPDATE
                    work_type = VALUES(work_type), genre = VALUES(genre), 
                    target_audience = VALUES(target_audience), time_period = VALUES(time_period),
                    primary_language = VALUES(primary_language), realism_level = VALUES(realism_level),
                    additional_context = VALUES(additional_context)
                """, form_data)
                connection.commit()

                flash('Context saved successfully', 'success')
                return redirect(url_for('progress', story_id=story_id))

            cursor.execute("SELECT * FROM contexts WHERE script_id = %s", (story_id,))
            context = cursor.fetchone()
            
            return render_template('context_form.html', 
                                   story_id=story_id, 
                                   context=context or {}, 
                                   story_title=story_title)
    except Exception as e:
        flash(f'Error processing context form: {str(e)}', 'error')
        return redirect(url_for('stories'))
    finally:
        connection.close()

# Paste scene and analyze
@app.route('/paste_scene/<int:story_id>', methods=['GET', 'POST'])
def paste_scene(story_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        scene_text = request.form.get('scene_text', '')
        
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO scenes (user_id, story_id, scene_text)
                    VALUES (%s, %s, %s);
                """, (session.get('user_id'), story_id, scene_text))
                connection.commit()
                scene_id = cursor.lastrowid
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            connection.close()

        return redirect(url_for('analyze_scene', scene_id=scene_id))

    return render_template('paste_scene.html', story_id=story_id)

# New route for progress tracking
@app.route('/progress/<int:story_id>')
def progress(story_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = get_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Fetch story details
            cursor.execute("SELECT * FROM stories WHERE story_id = %s AND user_id = %s", (story_id, session['user_id']))
            story = cursor.fetchone()

            if not story:
                flash('Story not found', 'error')
                return redirect(url_for('stories'))

            # Fetch context
            cursor.execute("SELECT * FROM contexts WHERE script_id = %s", (story_id,))
            story['context'] = cursor.fetchone()

            # Fetch scenes with analysis results and feedback
            cursor.execute("""
                SELECT s.*, 
                       CASE WHEN a.scene_id IS NOT NULL THEN TRUE ELSE FALSE END as analysis_result,
                       CASE WHEN f.scene_id IS NOT NULL THEN TRUE ELSE FALSE END as feedback
                FROM scenes s
                LEFT JOIN (SELECT DISTINCT scene_id FROM CreativeFeedback) f ON s.scene_id = f.scene_id
                LEFT JOIN (SELECT DISTINCT scene_id FROM scenes WHERE analysis_result IS NOT NULL) a ON s.scene_id = a.scene_id
                WHERE s.story_id = %s
                ORDER BY s.created_at
            """, (story_id,))
            scenes = cursor.fetchall()

        return render_template('progress.html', story=story, scenes=scenes)
    except Exception as e:
        flash(f'Error loading progress: {str(e)}', 'error')
        return redirect(url_for('stories'))
    finally:
        connection.close()

# Modify the analyze_scene route to handle scene revisions
@app.route('/analyze_scene/<int:scene_id>', methods=['GET', 'POST'])
def analyze_scene(scene_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT scene_text, story_id, analysis_result FROM scenes WHERE scene_id = %s", (scene_id,))
            scene = cursor.fetchone()

        if scene['analysis_result']:
            # If analysis result exists, use the stored result
            result = json.loads(scene['analysis_result'])
        else:
            # If no analysis result, perform the analysis
            context = get_user_context(session.get('user_id'))
            if not context:
                return jsonify({'error': 'No context found for this user.'}), 400

            combined_text = f"""
            Context:
            Medium: {context['work_type']}
            Genre: {context['genre']}
            Time Period: {context['time_period']}
            Level of Realism: {context['realism_level']}
            Target Audience: {context['target_audience']}
            Additional Context: {context['additional_context']}

            Scene:
            {scene['scene_text']}

            Please fact-check this scene and focus on identifying:
            1. Cultural inaccuracies
            2. Historical inaccuracies
            3. Scientific inaccuracies
            4. Mathematical inaccuracies
            
            List each category explicitly, and provide detailed explanations for any inaccuracies found. If no inaccuracies are found in a category, state 'None observed.'
            """

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a fact-checking assistant for screenwriters."},
                        {"role": "user", "content": combined_text}
                    ]
                )
                ai_response = response['choices'][0]['message']['content'].strip()

                result = {
                    "Cultural": extract_section(ai_response, "Cultural Inaccurac"),
                    "Historical": extract_section(ai_response, "Historical Inaccurac"),
                    "Scientific": extract_section(ai_response, "Scientific Inaccurac"),
                    "Mathematical": extract_section(ai_response, "Mathematical Inaccurac")
                }

                # Save the analysis result to the database
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE scenes SET analysis_result = %s WHERE scene_id = %s", 
                                   (json.dumps(result), scene_id))
                    connection.commit()

            except Exception as e:
                print(f"Error in AI processing: {str(e)}")
                result = {
                    "Cultural Inaccuracies": f"Error checking this text: {e}",
                    "Historical Inaccuracies": f"Error checking this text: {e}",
                    "Scientific Inaccuracies": f"Error checking this text: {e}",
                    "Mathematical Inaccuracies": f"Error checking this text: {e}"
                }

    except Exception as e:
        print(f"Error retrieving scene: {str(e)}")
        return jsonify({'error': f'Error retrieving scene: {str(e)}'}), 500
    finally:
        connection.close()

    return render_template('fact_check.html', scene=scene['scene_text'], result=result, scene_id=scene_id, story_id=scene['story_id'])

@app.route('/creative_feedback/<int:scene_id>')
def creative_feedback(scene_id):
    print(f"Rendering creative feedback for scene_id: {scene_id}")
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    story_id = request.args.get('story_id')
    return render_template('creative_feedback.html', scene_id=scene_id, story_id=story_id)

@app.route('/submit_creative_feedback/<int:scene_id>', methods=['GET', 'POST'])
def submit_creative_feedback(scene_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    if request.method == 'POST':
        try:
            # Get form data
            impact_on_narrative_flow = request.form.get('impact_on_narrative_flow')
            impact_on_emotional_depth = request.form.get('impact_on_emotional_depth')
            impact_on_dialogue = request.form.get('impact_on_dialogue')
            impact_on_character_development = request.form.get('impact_on_character_development')
            overall_creative_feedback = request.form.get('overall_creative_feedback')
            suggestion = request.form.get('suggestion')

            # Convert string values to integers, handling 'None' or empty strings
            def safe_int(value):
                return int(value) if value and value.isdigit() else 0

            # Insert feedback into database
            connection = get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO CreativeFeedback 
                        (user_id, scene_id, impact_on_narrative_flow, impact_on_emotional_depth, 
                        impact_on_dialogue, impact_on_character_development, 
                        overall_creative_feedback, suggestion)
                        VALUES (%s, %s, %s, %s, %
                    """, (session['user_id'], scene_id, safe_int(impact_on_narrative_flow), safe_int(impact_on_emotional_depth), safe_int(impact_on_dialogue), safe_int(impact_on_character_development), overall_creative_feedback, suggestion))
                    connection.commit()
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
            finally:
                connection.close()

            return jsonify({'success': True, 'message': 'Feedback submitted successfully'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/submit_creative_feedback/<int:scene_id>', methods=['GET', 'POST'])
def submit_creative_feedback(scene_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    if request.method == 'POST':
        try:
            # Get form data
            impact_on_narrative_flow = request.form.get('impact_on_narrative_flow')
            impact_on_emotional_depth = request.form.get('impact_on_emotional_depth')
            impact_on_dialogue = request.form.get('impact_on_dialogue')
            impact_on_character_development = request.form.get('impact_on_character_development')
            overall_creative_feedback = request.form.get('overall_creative_feedback')
            suggestion = request.form.get('suggestion')

            # Convert string values to integers, handling 'None' or empty strings
            def safe_int(value):
                return int(value) if value and value.isdigit() else 0

            # Insert feedback into database
            connection = get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO CreativeFeedback 
                        (user_id, scene_id, impact_on_narrative_flow, impact_on_emotional_depth, 
                        impact_on_dialogue, impact_on_character_development, 
                        overall_creative_feedback, suggestion)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        session.get('user_id'),
                        scene_id,
                        safe_int(impact_on_narrative_flow),
                        safe_int(impact_on_emotional_depth),
                        impact_on_dialogue,
                        safe_int(impact_on_character_development),
                        overall_creative_feedback,
                        suggestion
                    ))
                connection.commit()
            finally:
                connection.close()

            # Get the story_id from the form data
            story_id = request.form.get('story_id')
            
            # Redirect to the new feedback submitted page
            return redirect(url_for('feedback_submitted', story_id=story_id))
        except Exception as e:
            app.logger.error(f"Error submitting feedback: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    else:
        # Handle GET request
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT story_id FROM scenes WHERE scene_id = %s", (scene_id,))
                result = cursor.fetchone()
                if result:
                    story_id = result['story_id']
                else:
                    flash('Scene not found', 'error')
                    return redirect(url_for('stories'))
        finally:
            connection.close()

        return render_template('creative_feedback.html', scene_id=scene_id, story_id=story_id)

@app.route('/feedback_submitted/<int:story_id>')
def feedback_submitted(story_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('feedback_submitted.html', story_id=story_id)

# Logout route
@app.route('/logout')
def logout():
    session.clear()  # This will remove all session data
    return redirect(url_for('index'))  # Redirect to the home page after logout

# New route for creating a new story
@app.route('/new_story', methods=['GET', 'POST'])
def new_story():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        
        logging.debug(f"Attempting to create new story: title={title}, user_id={session.get('user_id')}")

        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO stories (user_id, title)
                    VALUES (%s, %s);
                """, (session.get('user_id'), title))
                connection.commit()
                story_id = cursor.lastrowid
                logging.debug(f"Successfully created story with ID: {story_id}")
        except Exception as e:
            logging.error(f"Error creating story: {str(e)}")
            return jsonify({'error': str(e)}), 500
        finally:
            connection.close()

        return redirect(url_for('context_form', story_id=story_id))

    return render_template('new_story.html')

# Route for the stories page
@app.route('/stories')
def stories():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT story_id, title, type, created_at
                FROM stories
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (session['user_id'],))
            stories = cursor.fetchall()
    except Exception as e:
        print(f"Error retrieving stories: {str(e)}")
        return jsonify({'error': f'Error retrieving stories: {str(e)}'}), 500
    finally:
        connection.close()

    return render_template('stories.html', stories=stories)

# New route for story visualization [test]
@app.route('/story_visualization/<int:story_id>')
def story_visualization(story_id):
    story = get_story(story_id)
    if not story:
        flash('Story not found', 'error')
        return redirect(url_for('stories'))

    scenes = get_scenes(story_id)
    data = []
    for i, scene in enumerate(scenes):
        feedback = get_factual_feedback(scene['scene_id'])
        if feedback:
            total_inaccuracies = sum(feedback.values())
            max_category = max(feedback, key=feedback.get)
            data.append({
                "id": f"Scene {i+1}",
                "group": max_category.replace('_inaccuracies', ''),
                "value": total_inaccuracies,
                "cultural": feedback['cultural_inaccuracies'],
                "historical": feedback['historical_inaccuracies'],
                "scientific": feedback['scientific_inaccuracies'],
                "mathematical": feedback['mathematical_inaccuracies']
            })
        else:
            data.append({
                "id": f"Scene {i+1}",
                "group": "no_feedback",
                "value": 0,
                "cultural": 0,
                "historical": 0,
                "scientific": 0,
                "mathematical": 0
            })

    return render_template('story_visualization.html', story=story, data=data)

def get_factual_feedback(scene_id):
    connection = get_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT cultural_inaccuracies, historical_inaccuracies, 
                       scientific_inaccuracies, mathematical_inaccuracies
                FROM FactualFeedback
                WHERE scene_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (scene_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Error getting factual feedback: {str(e)}")
        return None
    finally:
        connection.close()

# Helper functions for story visualization
def get_story(story_id):
    connection = get_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM stories WHERE story_id = %s", (story_id,))
            story = cursor.fetchone()
    except Exception as e:
        print(f"Error retrieving story: {str(e)}")
        story = None
    finally:
        connection.close()
    return story

def get_scenes(story_id):
    connection = get_connection()
    scenes = []
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM scenes WHERE story_id = %s ORDER BY created_at", (story_id,))
            scenes = cursor.fetchall()
    except Exception as e:
        print(f"Error retrieving scenes: {str(e)}")
    finally:
        connection.close()
    return scenes

def get_creative_feedback(scene_id):
    connection = get_connection()
    feedback = None
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM CreativeFeedback WHERE scene_id = %s", (scene_id,))
            feedback = cursor.fetchone()
    except Exception as e:
        print(f"Error retrieving creative feedback: {str(e)}")
    finally:
        connection.close()
    return feedback

def get_scenes(story_id):
    connection = get_connection()
    scenes = []
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM scenes WHERE story_id = %s ORDER BY created_at", (story_id,))
            scenes = cursor.fetchall()
    except Exception as e:
        print(f"Error retrieving scenes: {str(e)}")
    finally:
        connection.close()
    return scenes

def get_story(story_id):
    connection = get_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM stories WHERE story_id = %s", (story_id,))
            story = cursor.fetchone()
    except Exception as e:
        print(f"Error retrieving story: {str(e)}")
        story = None
    finally:
        connection.close()
    return story

def get_creative_feedback(scene_id):
    connection = get_connection()
    feedback = None
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM CreativeFeedback WHERE scene_id = %s", (scene_id,))
            feedback = cursor.fetchone()
    except Exception as e:
        print(f"Error retrieving creative feedback: {str(e)}")
    finally:
        connection.close()
    return feedback

def get_story(story_id):
    connection = get_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM stories WHERE story_id = %s", (story_id,))
            story = cursor.fetchone()
    except Exception as e:
        print(f"Error retrieving story: {str(e)}")
        story = None
    finally:
        connection.close()
    return story

def get_scenes(story_id):
    connection = get_connection()
    scenes = []
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM scenes WHERE story_id = %s ORDER BY created_at", (story_id,))
            scenes = cursor.fetchall()
    except Exception as e:
        print(f"Error retrieving scenes: {str(e)}")
    finally:
        connection.close()
    return scenes

def get_creative_feedback(scene_id):
    connection = get_connection()
    feedback = None
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM CreativeFeedback WHERE scene_id = %s", (scene_id,))
            feedback = cursor.fetchone()
    except Exception as e:
        print(f"Error retrieving creative feedback: {str(e)}")
    finally:
        connection.close()
    return feedback

@app.route('/extract_feedback/<int:story_id>')
def extract_feedback(story_id):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT s.scene_id, 
                   s.scene_text,
                   s.analysis_result,
                   cf.impact_on_narrative_flow,
                   cf.impact_on_emotional_depth,
                   cf.impact_on_dialogue,
                   cf.impact_on_character_development,
                   cf.overall_creative_feedback,
                   cf.suggestion
            FROM scenes s
            LEFT JOIN CreativeFeedback cf ON s.scene_id = cf.scene_id
            WHERE s.story_id = %s
            ORDER BY s.created_at
            """, (story_id,))
            results = cursor.fetchall()

            feedback_data = []
            for row in results:
                feedback_data.append({
                    "scene_id": row['scene_id'],
                    "scene_text": row['scene_text'],
                    "analysis_result": json.loads(row['analysis_result']) if row['analysis_result'] else None,
                    "creative_feedback": {
                        "impact_on_narrative_flow": row['impact_on_narrative_flow'],
                        "impact_on_emotional_depth": row['impact_on_emotional_depth'],
                        "impact_on_dialogue": row['impact_on_dialogue'],
                        "impact_on_character_development": row['impact_on_character_development'],
                        "overall_creative_feedback": row['overall_creative_feedback'],
                        "suggestion": row['suggestion']
                    }
                })

            return jsonify(feedback_data)  
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/feedback_overview/<int:story_id>')
def feedback_overview(story_id):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT s.scene_id, 
                   s.scene_text,
                   s.analysis_result
            FROM scenes s
            WHERE s.story_id = %s
            ORDER BY s.created_at
            """, (story_id,))
            results = cursor.fetchall()

            conversation_data = []
            for row in results:
                creative_feedback = get_creative_feedback(row['scene_id'])  
                conversation_data.append({
                    "scene_id": row['scene_id'],
                    "scene_text": row['scene_text'],
                    "analysis_result": json.loads(row['analysis_result']) if row['analysis_result'] else None,
                    "creative_feedback": creative_feedback  
                })

            return render_template('feedback_overview.html', conversation_data=conversation_data, story_id=story_id)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
