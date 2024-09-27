import pymysql
import ssl
from config import Config

# Create an SSL context for secure connection
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def get_connection():
    try:
        return pymysql.connect(
            host=Config.TIDB_HOST,
            port=Config.TIDB_PORT,
            user=Config.TIDB_USER,
            password=Config.TIDB_PASSWORD,
            database=Config.TIDB_DATABASE,
            ssl={'ssl': ssl_context}
        )
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise

def initialize_database():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Create users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            );
            """)

            # Create stories table without the type column
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                story_id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT,
                title VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            """)

            # Create scenes table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS scenes (
                scene_id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT,
                story_id INT,
                scene_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (story_id) REFERENCES stories(story_id) ON DELETE CASCADE
            );
            """)

            # Create CreativeFeedback table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS CreativeFeedback (
                feedback_id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT,
                scene_id INT,
                impact_on_narrative_flow INT,
                impact_on_emotional_depth INT,
                impact_on_dialogue VARCHAR(255),
                impact_on_character_development INT,
                overall_creative_feedback TEXT,
                suggestion VARCHAR(255),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (scene_id) REFERENCES scenes(scene_id) ON DELETE CASCADE
            );
            """)

            # Add scene_id column to CreativeFeedback table if it doesn't exist
            cursor.execute("""
            ALTER TABLE CreativeFeedback ADD COLUMN IF NOT EXISTS scene_id INT;
            """)
            
            # Check if the foreign key constraint exists
            cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.TABLE_CONSTRAINTS
            WHERE CONSTRAINT_SCHEMA = DATABASE()
            AND TABLE_NAME = 'CreativeFeedback'
            AND CONSTRAINT_NAME = 'fk_creative_feedback_scene';
            """)
            constraint_exists = cursor.fetchone()[0]

            # Add foreign key constraint if it doesn't exist
            if not constraint_exists:
                cursor.execute("""
                ALTER TABLE CreativeFeedback 
                ADD CONSTRAINT fk_creative_feedback_scene 
                FOREIGN KEY (scene_id) REFERENCES scenes(scene_id) ON DELETE CASCADE;
                """)

            # Create contexts table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS contexts (
                context_id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT,
                script_id INT,
                work_type VARCHAR(50),
                genre VARCHAR(50),
                target_audience VARCHAR(50),
                time_period VARCHAR(50),
                primary_language VARCHAR(50),
                realism_level INT,
                additional_context TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (script_id) REFERENCES stories(story_id) ON DELETE CASCADE
            );
            """)

            # Create FactualFeedback table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS FactualFeedback (
                feedback_id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT,
                scene_id INT,
                cultural_inaccuracies INT DEFAULT 0,
                historical_inaccuracies INT DEFAULT 0,
                scientific_inaccuracies INT DEFAULT 0,
                mathematical_inaccuracies INT DEFAULT 0,
                feedback_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (scene_id) REFERENCES scenes(scene_id) ON DELETE CASCADE
            );
            """)

        connection.commit()
        print("Database schema updated successfully.")
    except pymysql.err.OperationalError as e:
        if e.args[0] == 1060:  # Duplicate column error
            print("Column already exists, skipping...")
        else:
            print(f"An error occurred: {e}")
    finally:
        connection.close()

def extract_feedback_with_stories():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Query to extract feedback paired with stories and scenes
            cursor.execute("""
            SELECT s.title, 
                   sc.scene_text,
                   cf.overall_creative_feedback, 
                   ff.cultural_inaccuracies, 
                   ff.historical_inaccuracies, 
                   ff.scientific_inaccuracies, 
                   ff.mathematical_inaccuracies
            FROM stories s
            JOIN scenes sc ON s.story_id = sc.story_id
            LEFT JOIN CreativeFeedback cf ON sc.scene_id = cf.scene_id
            LEFT JOIN FactualFeedback ff ON sc.scene_id = ff.scene_id
            """)
            results = cursor.fetchall()
            for row in results:
                print(f"Story Title: {row[0]}, Scene Text: {row[1]}, Creative Feedback: {row[2]}, "
                      f"Cultural Inaccuracies: {row[3]}, Historical Inaccuracies: {row[4]}, "
                      f"Scientific Inaccuracies: {row[5]}, Mathematical Inaccuracies: {row[6]}")
    except Exception as e:
        print(f"Error extracting feedback: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    initialize_database()
    extract_feedback_with_stories()
