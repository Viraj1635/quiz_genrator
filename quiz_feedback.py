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

