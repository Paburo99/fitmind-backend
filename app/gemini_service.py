import google.generativeai as genai
from config import Config

genai.configure(api_key=Config.GEMINI_API_KEY)

# Generation Configuration
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048, # Adjust as needed
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash", # Or other suitable model
    generation_config=generation_config,
    safety_settings=safety_settings
)

def generate_text_from_gemini(prompt_parts):
    """
    Generates text using the Gemini API.
    prompt_parts: A list of strings forming the prompt.
    """
    try:
        response = model.generate_content(prompt_parts)
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        # Check response.prompt_feedback for blockage reasons
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            print(f"Prompt Feedback: {response.prompt_feedback}")
        return "Sorry, I couldn't generate a response at this time. Please try again later."

# Example usage (will be called from routes)
# if __name__ == '__main__':
#     prompt = ["Suggest a 3-day beginner workout plan focusing on full body strength."]
#     recommendation = generate_text_from_gemini(prompt)
#     print(recommendation)