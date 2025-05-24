import google.generativeai as genai
from config import Config

genai.configure(api_key=Config.GEMINI_API_KEY)

# Enhanced Generation Configuration for Fitness AI
generation_config = {
    "temperature": 0.8,  # Increased for more creative and engaging responses
    "top_p": 0.95,       # Allow for diverse vocabulary while maintaining focus
    "top_k": 64,         # Increased for more varied word choices
    "max_output_tokens": 3072, # Increased for detailed workout plans and insights
    "response_mime_type": "text/plain",
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-preview-04-17", # Latest model for enhanced capabilities
    generation_config=generation_config,
    safety_settings=safety_settings,
    system_instruction="""You are FitMind AI, an expert fitness and nutrition coach with advanced knowledge in:
    - Exercise physiology and program design
    - Sports nutrition and meal planning  
    - Behavioral psychology and motivation
    - Data analysis and progress tracking
    
    Always provide evidence-based, personalized recommendations that are:
    ✓ Safe and appropriate for the user's fitness level
    ✓ Aligned with their specific goals and preferences
    ✓ Motivating and encouraging in tone
    ✓ Actionable with clear instructions
    ✓ Backed by fitness science principles
    
    Format responses to be engaging, using emojis appropriately, and structure information clearly for easy reading."""
)

def generate_text_from_gemini(prompt_parts):
    """
    Generates text using the enhanced Gemini API for fitness coaching.
    prompt_parts: A list of strings forming the prompt.
    Returns: Generated text response or error message.
    """
    try:
        # Convert list to single string if needed
        if isinstance(prompt_parts, list):
            full_prompt = '\n'.join(str(part) for part in prompt_parts)
        else:
            full_prompt = str(prompt_parts)
        
        response = model.generate_content(full_prompt)
        
        # Check if response was blocked
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            feedback = response.prompt_feedback
            if hasattr(feedback, 'block_reason') and feedback.block_reason:
                print(f"Content blocked. Reason: {feedback.block_reason}")
                return "I'm unable to generate this recommendation due to content policies. Please try a different request."
        
        # Return the generated text or handle empty response
        if hasattr(response, 'text') and response.text:
            return response.text.strip()
        else:
            print("Empty response received from Gemini API")
            return "I'm having trouble generating a detailed response right now. Please try again in a moment."
            
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        error_msg = str(e).lower()
        
        # Provide specific error messages for common issues
        if 'quota' in error_msg or 'limit' in error_msg:
            return "I'm currently experiencing high demand. Please try again in a few minutes."
        elif 'safety' in error_msg or 'blocked' in error_msg:
            return "I'm unable to process this request due to content guidelines. Please try rephrasing your request."
        elif 'network' in error_msg or 'connection' in error_msg:
            return "I'm having connectivity issues. Please check your internet connection and try again."
        else:
            return "I'm temporarily unavailable. Please try again later."

# Example usage (will be called from routes)
# if __name__ == '__main__':
#     prompt = ["Suggest a 3-day beginner workout plan focusing on full body strength."]
#     recommendation = generate_text_from_gemini(prompt)
#     print(recommendation)