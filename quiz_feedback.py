import os
import json
import google.generativeai as genai
from pprint import pprint
import time 

def get_ai_feedback(correct_answers, wrong_answers):
    """
    Generates CONCISE and BALANCED feedback for each topic in the quiz.
    """
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    performance_by_topic = {}

    for answer in correct_answers + wrong_answers:
        topic = answer.get('topic', 'General')
        if topic not in performance_by_topic:
            performance_by_topic[topic] = {'correct': [], 'wrong': []}

    for answer in correct_answers:
        topic = answer.get('topic', 'General')
        performance_by_topic[topic]['correct'].append(answer)

    for answer in wrong_answers:
        topic = answer.get('topic', 'General')
        performance_by_topic[topic]['wrong'].append(answer)

    topic_feedback_results = {}

    for topic, performance in performance_by_topic.items():
        correct_str = json.dumps(performance['correct'], indent=2)
        wrong_str = json.dumps(performance['wrong'], indent=2)

        prompt = f"""
        You are a helpful AI teaching assistant. A student just finished a quiz section on the topic of: **{topic}**.

        Here are the questions they answered CORRECTLY on this topic:
        {correct_str}

        Here are the questions they answered INCORRECTLY on this topic:
        {wrong_str}

        Your task is to provide a single, concise sentence of feedback (under 25 words) about their performance ON THIS TOPIC ONLY. Address the user directly. If they got everything right, praise them. If they made mistakes, gently point out the sub-topic to review.
        """
        
        try:
            print(f"--- Sending prompt to Gemini for topic: {topic} ---")
            response = model.generate_content(prompt)
            topic_feedback_results[topic] = response.text.strip()
            time.sleep(1)
        except Exception as e:
            print(f"An error occurred while getting feedback for {topic}: {e}")
            topic_feedback_results[topic] = "Sorry, an error occurred while generating feedback for this topic."

    return topic_feedback_results

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

