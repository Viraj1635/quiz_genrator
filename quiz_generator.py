import os
import json
import google.generativeai as genai
from pprint import pprint

# --- Configuration ---
# It's best practice to store your API key as an environment variable
# For the hackathon, you can hardcode it, but this is better:
# os.environ['GOOGLE_API_KEY'] = 'YOUR_API_KEY_HERE'

try:
    # Or, get it from your environment variables
    api_key = 'AIzaSyBy7P_FMxdo3PWGbyi9HAHFMbOnzo4qjzM'
    if not api_key:
        # Replace this with your actual API key if not using environment variables
        api_key = 'AIzaSyBy7P_FMxdo3PWGbyi9HAHFMbOnzo4qjzM'
        print("Warning: API key is hardcoded. It's better to use environment variables.")
    
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"Error during configuration: {e}")
    # Exit if configuration fails
    exit()

# --- The Core Function ---

def generate_quiz_questions(topic, difficulty, num_questions,question_types):
    """
    Generates a set of unique quiz questions using the Gemini API.

    Args:
        topic (str): The subject of the quiz (e.g., 'Python', 'React', 'SQL').
        difficulty (str): The difficulty level (e.g., 'Easy', 'Intermediate', 'Hard').
        num_questions (int): The number of questions to generate.

    Returns:
        list: A list of question dictionaries, or None if an error occurs.
    """
    # Create an instance of the Gemini Pro model
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    topics_string = ", ".join(topic)
    types_str = ", ".join(question_types)

    # This is the most important part: The Prompt!
    # We instruct the model to return a valid JSON object.
    prompt_template = f"""
    You are an expert technical interviewer.Your most important task is to generate questions in various formats and to include a "type" field in every single object.
    Your task is to generate {num_questions} total questions covering the following topics: {topics_string}.
    The difficulty for all questions should be {difficulty}.
    The questions should be {types_str}.
    Distribute the questions as evenly as possible across all topics.

    Generate a JSON array of question objects. Each object MUST have a "type" field. Adhere strictly to the following formats:

    1.  For "mcq" type:
        {{
          "type": "mcq", "topic": "...", "question": "...", "options": ["...", "...", "...", "..."], "correct_answer": "...", "explanation": "..."
        }}

    2.  For "true_false" type:
        {{
          "type": "true_false", "topic": "...", "question": "...", "options": ["True", "False"], "correct_answer": "...", "explanation": "..."
        }}

    3.  For "fill_in_the_blank" type:
        {{
          "type": "fill_in_the_blank", "topic": "...", "question_parts": ["start of sentence ", " end of sentence."], "correct_answer": "word", "explanation": "..."
        }}

    Ensure the final output is only a single, valid JSON array.

    IMPORTANT: Format your entire output as a single, valid JSON array of objects. Do not include any text or formatting outside of the JSON array.
    
    """
    
    print("--- Sending Prompt to Gemini ---")
    try:
        # Generate the content
        response = model.generate_content(prompt_template)
        
        # The response text might have markdown formatting ` ```json ... ``` `
        # We need to clean it to get the pure JSON.
        
        # cleaned_json_string = response.text.strip().replace('```json', '').replace('```', '')
        
        cleaned_json_string = response.text.strip()
        start = cleaned_json_string.find('[')
        end = cleaned_json_string.rfind(']') + 1
        questions = json.loads(cleaned_json_string[start:end])
        
        # Parse the JSON string into a Python list
        # questions = json.loads(cleaned_json_string)
        return questions

    except json.JSONDecodeError:
        print("--- ERROR: Failed to decode JSON from the model's response. ---")
        print("Raw Response Text:")
        print(response.text)
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def get_ai_feedback(correct_answers, wrong_answers):
    """
    Generates CONCISE and BALANCED feedback based on quiz performance.
    """
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    # Convert lists to JSON strings for the prompt
    correct_str = json.dumps(correct_answers, indent=2)
    wrong_str = json.dumps(wrong_answers, indent=2)

    # New prompt for concise, balanced feedback
    prompt = f"""
    You are a helpful AI teaching assistant. A student has just finished a quiz.

    Here are the questions they answered CORRECTLY:
    {correct_str}

    Here are the questions they answered INCORRECTLY:
    {wrong_str}

    Your task is to provide feedback that is both encouraging and helpful. Follow these rules:
    1.  Acknowledge their strengths based on the topics of the correct answers.
    2.  Briefly point out 1-2 topics they could improve on, based on the wrong answers.
    3.  Keep the entire feedback short, positive, and under 75 words.
    """
    print("--- Sending Prompt to Gemini ---")

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"An error occurred while getting AI feedback: {e}")
        return "Sorry, an error occurred while generating feedback."


def get_long_term_feedback(all_correct_answers, all_wrong_answers):
    """
    Analyzes a user's ENTIRE history to provide balanced, long-term feedback.
    """
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    correct_str = json.dumps(all_correct_answers, indent=2)
    wrong_str = json.dumps(all_wrong_answers, indent=2)

    prompt = f"""
        You are an expert data analyst and programming tutor. A student has just finished a quiz, and you are analyzing their entire performance history to give them personalized feedback.

        **Address the user directly using 'you' and 'your'.**

        STRENGTHS (based on questions they consistently answer correctly):
        {correct_str}

        WEAKNESSES (based on questions they consistently answer incorrectly):
        {wrong_str}

        Based on this complete history, provide a concise, balanced summary under 90 words. Start by praising **their** specific, recurring strengths. Then, identify the 1-2 most critical concepts **they** need to review to improve.
        """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"An error occurred while getting long-term feedback: {e}")
        return "Sorry, an error occurred while analyzing the performance history."


def check_for_duplicates(new_question, existing_questions):
    """
    Uses AI to check if a new question is a semantic duplicate of any existing ones.
    """
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    # We only need the text of the questions for comparison
    new_question_text = new_question.get('question')
    existing_questions_text = [q.get('question') for q in existing_questions]

    prompt = f"""
    You are a quality assurance expert for a technical quiz platform. Compare the "New Question" to the "List of Existing Questions".

    Your task is to determine if the New Question is a semantic duplicate of any question in the existing list. A duplicate is a question that tests the exact same core knowledge, even if worded differently.

    New Question:
    "{new_question_text}"

    List of Existing Questions:
    {json.dumps(existing_questions_text, indent=2)}

    Respond ONLY with a single JSON object with the following format:
    {{
      "is_duplicate": boolean,
      "duplicate_of": "text of the duplicate question or null",
      "reason": "brief explanation"
    }}
    """

    try:
        response = model.generate_content(prompt)
        # Add robust cleaning for the JSON response
        cleaned_json_string = response.text.strip()
        start = cleaned_json_string.find('{')
        end = cleaned_json_string.rfind('}') + 1
        result = json.loads(cleaned_json_string[start:end])
        return result
    except Exception as e:
        print(f"An error occurred during duplicate check: {e}")
        # Default to assuming it's not a duplicate if the check fails
        return {"is_duplicate": False, "duplicate_of": None, "reason": "AI check failed."}

# --- Let's Test It! ---
if __name__ == "__main__":
    quiz_topic = "Java OOP"
    quiz_difficulty = "Medium"
    
    generated_questions = generate_quiz_questions(quiz_topic, quiz_difficulty, num_questions=2)
    
    if generated_questions:
        print("\n--- Successfully Generated Quiz Questions ---")
        # pprint is used for "pretty printing" the output
        pprint(generated_questions)