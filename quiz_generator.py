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

def generate_quiz_questions(topic, difficulty, num_questions=5):
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

    # This is the most important part: The Prompt!
    # We instruct the model to return a valid JSON object.
    prompt_template = f"""
    You are an expert technical interviewer.
    Your task is to generate {num_questions} total multiple-choice questions covering the following topics: {topics_string}.
    The difficulty for all questions should be {difficulty}.
    Distribute the questions as evenly as possible across all topics.

    Each question object MUST have:
    1. A 'question' text.
    2. An 'options' list with 4 possible answers.
    3. A 'correct_answer' field.
    4. An 'explanation' for the answer.
    5. A 'topic' field indicating which topic the question belongs to.

    IMPORTANT: Format your entire output as a single, valid JSON array of objects. Do not include any text or formatting outside of the JSON array.
    
    Example format for a single question object:
    {{
        "question": "What is a closure in Python?",
        "options": [
            "A function with no arguments",
            "A nested function that remembers the enclosing scope's variables",
            "A decorator for a class",
            "The process of closing a file"
        ],
        "correct_answer": "A nested function that remembers the enclosing scope's variables",
        "explanation": "A closure is a function object that has access to variables in its enclosing lexical scope, even when the enclosing scope has finished execution.",
        "topic": "Python"
    }}
    """
    
    print("--- Sending Prompt to Gemini ---")
    try:
        # Generate the content
        response = model.generate_content(prompt_template)
        
        # The response text might have markdown formatting ` ```json ... ``` `
        # We need to clean it to get the pure JSON.
        cleaned_json_string = response.text.strip().replace('```json', '').replace('```', '')
        
        # Parse the JSON string into a Python list
        questions = json.loads(cleaned_json_string)
        return questions

    except json.JSONDecodeError:
        print("--- ERROR: Failed to decode JSON from the model's response. ---")
        print("Raw Response Text:")
        print(response.text)
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# In quiz_generator.py

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

# --- Let's Test It! ---
if __name__ == "__main__":
    quiz_topic = "Java OOP"
    quiz_difficulty = "Medium"
    
    generated_questions = generate_quiz_questions(quiz_topic, quiz_difficulty, num_questions=2)
    
    if generated_questions:
        print("\n--- Successfully Generated Quiz Questions ---")
        # pprint is used for "pretty printing" the output
        pprint(generated_questions)