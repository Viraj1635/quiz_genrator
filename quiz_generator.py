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

    # This is the most important part: The Prompt!
    # We instruct the model to return a valid JSON object.
    prompt_template = f"""
    You are an expert technical interviewer.
    Your task is to generate {num_questions} multiple-choice questions for a quiz on the topic of {topic}.
    The difficulty level for these questions should be {difficulty}.

    Each question must have:
    1. A 'question' text.
    2. An 'options' list with 4 possible answers.
    3. A 'correct_answer' field indicating the correct option.
    4. A brief 'explanation' for why the answer is correct.

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
        "explanation": "A closure is a function object that has access to variables in its enclosing lexical scope, even when the enclosing scope has finished execution."
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

# --- Let's Test It! ---
if __name__ == "__main__":
    quiz_topic = "Java OOP"
    quiz_difficulty = "Medium"
    
    generated_questions = generate_quiz_questions(quiz_topic, quiz_difficulty, num_questions=2)
    
    if generated_questions:
        print("\n--- Successfully Generated Quiz Questions ---")
        # pprint is used for "pretty printing" the output
        pprint(generated_questions)