# WriterStrike

WriterStrike is an AI-powered script fact-checker designed to assist writers in improving their scripts by providing creative feedback and identifying factual inaccuracies. The application allows users to create, edit, and visualize their stories while receiving valuable insights from the AI.

## Repository

You can find the source code for this project at [GitHub - WriterStrike](https://github.com/elialabi/WriterStrike).

## Features

- **User Authentication**: Users can register, log in, and manage their accounts.
- **Story Management**: Create, edit, and view stories.
- **Scene Management**: Paste scenes and receive feedback on them.
- **Feedback Overview**: View detailed feedback on each scene, including creative feedback and factual inaccuracies. This feature allows users to see the conversation between the AI and the screenwriter, providing insights into the feedback process.
- **Story Visualization**: Visualize the story's structure and feedback using interactive charts.
- **Responsive Design**: The application is designed to work on various devices.

## Technologies Used

- **Backend**: Python with Flask
- **Frontend**: HTML, CSS, JavaScript
- **Database**: MySQL (or any other relational database)
- **Libraries**: 
  - Flask for web framework
  - SQLAlchemy for ORM
  - D3.js for data visualization
  - SweetAlert2 for alerts

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)
- MySQL (or any other relational database)

### Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/elialabi/WriterStrike.git
   cd WriterStrike
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up the Database**:
   - Create a MySQL database and update the database connection settings in your application.
   - Run the necessary migrations to set up the database schema.

5. **Run the Application**:
   - Start the Flask development server by running:
   ```bash
   python -m flask run
   ```
   - Open your web browser and go to `http://127.0.0.1:5000`.

## How It Works

### Backend Architecture

1. **Flask Framework**: The application is built using Flask, a lightweight web framework for Python. It handles routing, request processing, and response generation.

2. **Database Interaction**: 
   - The application uses SQLAlchemy as an Object-Relational Mapping (ORM) tool to interact with the MySQL database. This allows for easy querying and manipulation of data without writing raw SQL.
   - Key tables include:
     - **Users**: Stores user credentials and authentication details.
     - **Stories**: Contains information about each story created by users.
     - **Scenes**: Holds individual scenes associated with each story.
     - **CreativeFeedback**: Stores feedback provided by the AI for each scene, including various impact metrics and suggestions.

3. **AI Integration**: The application leverages AI algorithms to analyze scenes and provide feedback. This includes:
   - Evaluating the narrative flow, emotional depth, dialogue quality, and character development.
   - Generating suggestions for improvement based on the analysis.

4. **Feedback Overview**: The feedback overview feature allows users to see the conversation between the AI and the screenwriter, displaying both creative feedback and factual inaccuracies in a structured format.

## Usage

1. **Register an Account**: Create a new account to start using the application.
2. **Log In**: Use your credentials to log in.
3. **Create a New Story**: Navigate to the "Create New Story" page to start a new story.
4. **Paste Scenes**: Add scenes to your story and submit them for feedback.
5. **View Feedback**: Access the feedback overview to see the AI's suggestions and identify any factual inaccuracies. This overview allows you to track the conversation between the AI and the screenwriter.
6. **Visualize Your Story**: Use the story visualization feature to see the structure and feedback of your story.

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the contributors and libraries that made this project possible.
- Special thanks to the open-source community for their support and resources.

