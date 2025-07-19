import os
import easyocr
import io
from flask import Flask, request, jsonify
from flask_cors import CORS
import fitz
from PIL import Image

from quiz_generator import generate_quiz_questions, check_for_duplicates, generate_questions_from_text
from quiz_feedback import get_ai_feedback, get_long_term_feedback

app = Flask(__name__)

CORS(app)

@app.route("/api/generate-quiz", methods=['POST'])
def handle_quiz_generation():
    """
    Handles requests from the UI to generate a new quiz.
    Expects a JSON body with 'topic', 'difficulty', and 'num_questions'.
    """

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request: No data provided"}), 400

    topic = data.get('topic')
    difficulty = data.get('difficulty')
    num_questions = data.get('num_questions', 5) # Default to 5 questions
    question_types = data.get('question_types', ['mcq'])


    if not all([topic, difficulty]):
        return jsonify({"error": "Missing 'topic' or 'difficulty' in request"}), 400

    print(f"Received request to generate a {difficulty} quiz on {topic} with {num_questions} questions.")


    try:
        questions = generate_unique_quiz_questions(
            topic=topic,
            difficulty=difficulty,
            num_questions=num_questions,
            question_types=question_types
        )

        if questions:

            print("Successfully generated questions.")
            return jsonify(questions)
        else:

            print("AI script failed to generate questions.")
            return jsonify({"error": "Failed to generate quiz questions from the AI model."}), 500

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


@app.route("/api/generate-from-pdf", methods=['POST'])
def handle_pdf_quiz_generation_with_ocr():
    print("Loading OCR model into memory...")
    ocr_reader = easyocr.Reader(['en']) # 'en' for English
    print("OCR model loaded.")
    """
    Handles PDF uploads, extracts text from text layers AND images,
    and then calls the AI logic function.
    """
    try:
        if 'pdf_file' not in request.files:
            return jsonify({"error": "No PDF file provided"}), 400

        file = request.files['pdf_file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        num_questions = request.form.get('num_questions', 10, type=int)
        difficulty = request.form.get('difficulty', 'Medium')
        question_types_str = request.form.get('question_types', 'mcq')
        question_types = [qt.strip() for qt in question_types_str.split(',')]
        
        pdf_document = fitz.open(stream=file.read(), filetype="pdf")
        full_text = ""

        print("Starting PDF processing...")
        for page_num, page in enumerate(pdf_document):
            print(f"  - Processing page {page_num + 1}...")
            full_text += page.get_text() + "\n"

            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]
                

                print(f"    - Performing OCR on image {img_index + 1}...")
                ocr_results = ocr_reader.readtext(image_bytes)
                

                for (bbox, text, prob) in ocr_results:
                    full_text += text + " "
                full_text += "\n"

        if not full_text.strip():
            return jsonify({"error": "Could not extract any text from the PDF."}), 400

        print("PDF processing complete. Sending text to AI...")

        questions = generate_questions_from_text(
            full_text=full_text,
            num_questions=num_questions,
            difficulty=difficulty,
            question_types=question_types
        )
        
        return jsonify({"questions": questions})

    except Exception as e:
        print(f"An unexpected error occurred in the endpoint: {e}")
        return jsonify({"error": f"An internal server error occurred."}), 500


@app.route("/api/get-feedback", methods=['POST'])
def handle_feedback_request():
    data = request.get_json()
    if not data or 'wrong_answers' not in data or 'correct_answers' not in data:
        return jsonify({"error": "Request must include 'correct_answers' and 'wrong_answers'"}), 400

    
    correct_answers = data.get('correct_answers')
    wrong_answers = data.get('wrong_answers')

    # if not all([correct_answers, wrong_answers]):
    #     return jsonify({"error": "Missing 'correct_answers' or 'wrong_answers' in request"}), 400
    
    if not wrong_answers:
        perfect_score_feedback = "Congratulations on a perfect score! Keep up the great work. ✨"
        return jsonify({"feedback": perfect_score_feedback})


    try:
        feedback_text = get_ai_feedback(correct_answers, wrong_answers)

        if feedback_text:
            return jsonify({"feedback": feedback_text})
        else:
            return jsonify({"error": "AI model failed to generate feedback."}), 500

    except Exception as e:
        print(f"An unexpected error occurred in feedback generation: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


@app.route("/api/get-long-term-feedback", methods=['POST'])
# def handle_long_term_feedback():
#     data = request.get_json()
#     if not data or 'candidate_name' not in data:
#         return jsonify({"error": "Request must include 'candidate_name'"}), 400
    
#     candidate_name = data['candidate_name']

#     try:
#         # --- Database query commented out ---
#         # all_correct_answers = db.get_all_correct_answers(candidate_name)
#         # all_wrong_answers = db.get_all_wrong_answers(candidate_name)

#         all_correct_answers = [
#             {"topic": "React", "question": "What is state in React?"},
#             {"topic": "React", "question": "How do you pass props?"},
#             {"topic": "SQL", "question": "What is a SELECT statement?"}
#         ]
#         all_wrong_answers = [
#             {"topic": "SQL", "question": "What is a LEFT JOIN?"},
#             {"topic": "Python", "question": "Explain Python's GIL."},
#             {"topic": "SQL", "question": "What is the difference between INNER JOIN and LEFT JOIN?"}
#         ]


#         if not all_correct_answers and not all_wrong_answers:
#             welcome_message = "Welcome! This is your first quiz. Complete it to start tracking your progress over time."
#             return jsonify({"feedback": welcome_message})


#         feedback_text = get_long_term_feedback(all_correct_answers, all_wrong_answers)

#         if feedback_text:
#             return jsonify({"feedback": feedback_text})
#         else:
#             return jsonify({"error": "AI model failed to generate long-term feedback."}), 500

#     except Exception as e:
#         # 5. Catch any other unexpected server errors
#         print(f"An unexpected error occurred in long-term feedback: {e}")
#         return jsonify({"error": "An internal server error occurred."}), 500


def generate_unique_quiz_questions(topic, difficulty, num_questions, question_types=['mcq']):
    """
    Generates a list of unique quiz questions, filtering out semantic duplicates.
    """
    print(f"Attempting to generate {num_questions} unique questions...")

    try:
        candidate_questions = generate_quiz_questions(
            topic, difficulty, num_questions + 5, question_types
        )
        if not candidate_questions:
            print("Initial generation failed, returning empty list.")
            return []
    except Exception as e:
        print(f"Error during initial generation: {e}")
        return []

    existing_questions_from_db = [
        {"question": "Which SQL constraint ensures each record is unique?"},
        {"question": "How do you sort records in SQL?"}
    ]

    unique_new_questions = []
    for new_q in candidate_questions:
        if len(unique_new_questions) >= num_questions:
            break

        print(f"Checking new question for duplicates: '{new_q.get('question', '')[:30]}...'")
        dupe_check_result = check_for_duplicates(new_q, existing_questions_from_db)
        
        if not dupe_check_result.get("is_duplicate"):
            print("  > Status: Unique. Adding to list.")
            unique_new_questions.append(new_q)
            existing_questions_from_db.append(new_q)
        else:
            print(f"  > Status: Duplicate found. Discarding.")

    print(f"Finished. Returning {len(unique_new_questions)} unique questions.")
    return unique_new_questions


if __name__ == "__main__":
    # The server will run on http://127.0.0.1:5000
    app.run(debug=True, port=5000)