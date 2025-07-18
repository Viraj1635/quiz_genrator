import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from quiz_generator import generate_quiz_questions, get_ai_feedback

app = Flask(__name__)

CORS(app)

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


@app.route("/api/get-feedback", methods=['POST'])
def handle_feedback_request():
    # 1. Basic input validation
    data = request.get_json()
    if not data or 'wrong_answers' not in data or 'correct_answers' not in data:
        return jsonify({"error": "Request must include 'correct_answers' and 'wrong_answers'"}), 400

    
    correct_answers = data.get('correct_answers')
    wrong_answers = data.get('wrong_answers')

    # if not all([correct_answers, wrong_answers]):
    #     return jsonify({"error": "Missing 'correct_answers' or 'wrong_answers' in request"}), 400
    
    # 2. Handle the edge case of a perfect score
    if not wrong_answers:
        # The user got a perfect score, no need to call the AI
        perfect_score_feedback = "Congratulations on a perfect score! Keep up the great work. ✨"
        return jsonify({"feedback": perfect_score_feedback})

    # 3. Main logic with a try...except block
    try:
        # Call the AI function to get personalized feedback
        feedback_text = get_ai_feedback(correct_answers, wrong_answers)

        if feedback_text:
            # Send the feedback text back to the UI
            return jsonify({"feedback": feedback_text})
        else:
            # Handle cases where the AI script returns nothing
            return jsonify({"error": "AI model failed to generate feedback."}), 500

    except Exception as e:
        # Catch any other unexpected server errors
        print(f"An unexpected error occurred in feedback generation: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

if __name__ == "__main__":
    # The server will run on http://127.0.0.1:5000
    app.run(debug=True, port=5000)