import os
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import your AI function from the other file
from quiz_generator import generate_quiz_questions

# Initialize the Flask app
app = Flask(__name__)

# IMPORTANT: Enable CORS to allow your frontend to make requests
CORS(app)

# Define the API endpoint for quiz generation
@app.route("/api/generate-quiz", methods=['POST'])
def handle_quiz_generation():
    """
    Handles requests from the UI to generate a new quiz.
    Expects a JSON body with 'topic', 'difficulty', and 'num_questions'.
    """
    # 1. Get the data from the incoming request
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request: No data provided"}), 400

    topic = data.get('topic')
    difficulty = data.get('difficulty')
    num_questions = data.get('num_questions', 5) # Default to 5 questions

    if not all([topic, difficulty]):
        return jsonify({"error": "Missing 'topic' or 'difficulty' in request"}), 400

    print(f"Received request to generate a {difficulty} quiz on {topic} with {num_questions} questions.")

    # 2. Call your AI script
    try:
        questions = generate_quiz_questions(
            topic=topic,
            difficulty=difficulty,
            num_questions=num_questions
        )

        if questions:
            # 3. Send the questions back to the UI
            print("Successfully generated questions.")
            return jsonify(questions)
        else:
            # Handle cases where the AI script returns nothing
            print("AI script failed to generate questions.")
            return jsonify({"error": "Failed to generate quiz questions from the AI model."}), 500

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

# This allows you to run the app directly
if __name__ == "__main__":
    # The server will run on http://127.0.0.1:5000
    app.run(debug=True, port=5000)