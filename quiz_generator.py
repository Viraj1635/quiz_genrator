import os
import json
import google.generativeai as genai
from pprint import pprint
from dotenv import load_dotenv



try:

    api_key = 'AIzaSyD4ThRw3MzTnmROOlcPeWiRA5Ns_q1A9Ds'
    # if not api_key:
    #     api_key = 'AIzaSyDZPWZPNXtfpA3SWXnnBvTAk-_ieuvcb60'
    #     print("Warning: API key is hardcoded. It's better to use environment variables.")
    
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"Error during configuration: {e}")
    exit()


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
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    topics_string = ", ".join(topic)
    types_str = ", ".join(question_types)

    prompt_template = f"""
    You are an expert technical interviewer.Your most important task is to generate questions in various formats and to include a "type" field in every single object.
    Your task is to generate {num_questions} total questions covering the following topics: {topics_string}.
    The difficulty for all questions should be {difficulty}.
    The questions should be {types_str}.
    Distribute the questions as evenly as possible across all topics.

    Generate a JSON array of question objects. Each object MUST have a "type" field. Adhere strictly to the following formats:

    1.  For "mcq" type:
        {{
          "type": "mcq", "topic": "...", "question": "...", "options": ["...", "...", "...", "..."], "correct_answer": "...", "explanation": "...","isAttemped": false
        }}

    2.  For "true_false" type:
        {{
          "type": "true_false", "topic": "...", "question": "...", "options": ["True", "False"], "correct_answer": "...", "explanation": "...","isAttemped": false
        }}

    3.  For "fill_in_the_blank" type:
        {{
          "type": "fill_in_the_blank", "topic": "...", "question_parts": ["start of sentence ", " end of sentence."], "correct_answer": "word", "explanation": "...","isAttemped": false
        }}

    Ensure the final output is only a single, valid JSON array.

    IMPORTANT: Format your entire output as a single, valid JSON array of objects. Do not include any text or formatting outside of the JSON array.
    
    """
    
    print("--- Sending Prompt to Gemini ---")
    try:
        response = model.generate_content(prompt_template)
        
        
        cleaned_json_string = response.text.strip()
        start = cleaned_json_string.find('[')
        end = cleaned_json_string.rfind(']') + 1
        questions = json.loads(cleaned_json_string[start:end])
        
        return questions

    except json.JSONDecodeError:
        print("--- ERROR: Failed to decode JSON from the model's response. ---")
        print("Raw Response Text:")
        print(response.text)
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def check_for_duplicates(new_question, existing_questions):
    """
    Uses AI to check if a new question is a semantic duplicate of any existing ones.
    """
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

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
        cleaned_json_string = response.text.strip()
        start = cleaned_json_string.find('{')
        end = cleaned_json_string.rfind('}') + 1
        result = json.loads(cleaned_json_string[start:end])
        return result
    except Exception as e:
        print(f"An error occurred during duplicate check: {e}")
        return {"is_duplicate": False, "duplicate_of": None, "reason": "AI check failed."}


def generate_questions_from_text(full_text, num_questions, difficulty, question_types):
    """
    Takes extracted text and quiz options, then calls the AI to generate questions.
    """
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    types_str = ", ".join(question_types)
    if "all_mixed" in types_str:
        types_str = "a mix of mcq, true_false, and fill_in_the_blank"

    prompt = f"""
    You are an expert instructor. Read the following document text and generate {num_questions} questions of {difficulty} difficulty.
    The question types should be {types_str}.

    The questions MUST be based ONLY on the information provided in the document text below.

    DOCUMENT TEXT:
    ---
    {full_text}
    ---

    Respond ONLY with a single, valid JSON array of question objects. Each object must have a "type" field and follow the specific formats for mcq, true_false, or fill_in_the_blank.
    """

    try:
        response = model.generate_content(prompt)
        
        cleaned_json_string = response.text.strip()
        start_index = cleaned_json_string.find('[')
        end_index = cleaned_json_string.rfind(']') + 1
        
        if start_index == -1 or end_index == 0:
            raise json.JSONDecodeError("No JSON array found in the AI response.", cleaned_json_string, 0)
            
        questions = json.loads(cleaned_json_string[start_index:end_index])
        return questions

    except Exception as e:
        print(f"Error in AI generation: {e}")
        raise

if __name__ == "__main__":
    quiz_topic = "Java OOP"
    quiz_difficulty = "Medium"
    
    generated_questions = generate_quiz_questions(quiz_topic, quiz_difficulty, num_questions=2)
    
    if generated_questions:
        print("\n--- Successfully Generated Quiz Questions ---")
        pprint(generated_questions)