from flask import Blueprint, request, jsonify
from auth_utils import token_required
from gemini_service import generate_text_from_gemini
import json
from datetime import datetime

chat_bp = Blueprint('chat_bp', __name__)

@chat_bp.route('/chat/context-aware', methods=['POST'])
@token_required
def context_aware_chat(current_user_id):
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_history = data.get('conversation_history', [])
        page_context = data.get('page_context', 'dashboard')
        user_constraints = data.get('user_constraints', [])
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Build enhanced context-aware prompt
        enhanced_prompt = build_enhanced_context_prompt(
            user_message, 
            conversation_history, 
            page_context, 
            user_constraints,
            current_user_id
        )
        
        # Generate response using Gemini
        ai_response = generate_text_from_gemini(enhanced_prompt)
        
        if not ai_response:
            return jsonify({
                'reply': 'I apologize, but I\'m having trouble generating a response right now. Please try rephrasing your question or try again in a moment.'
            }), 200
        
        # Clean and format the response
        formatted_response = format_chat_response(ai_response, page_context)
        
        return jsonify({
            'reply': formatted_response,
            'context': page_context,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error in context-aware chat: {str(e)}")
        return jsonify({
            'reply': 'I\'m experiencing some technical difficulties right now. Please try again later or contact support if the issue persists.',
            'error': 'Internal server error'
        }), 500

def build_enhanced_context_prompt(user_message, conversation_history, page_context, user_constraints, user_id):
    """Build a comprehensive context-aware prompt for the AI"""
    
    # Define context-specific knowledge and capabilities
    context_knowledge = {
        'dashboard': {
            'focus': 'fitness metrics overview, daily summaries, and motivational insights',
            'capabilities': [
                'Interpret fitness dashboard data and trends',
                'Provide motivational insights based on progress',
                'Suggest daily action items and improvements',
                'Explain metric relationships and patterns'
            ],
            'data_types': 'workout counts, calorie tracking, water intake, weight trends'
        },
        'profile': {
            'focus': 'personal settings, goal establishment, and profile optimization',
            'capabilities': [
                'Guide through profile setup and optimization',
                'Recommend appropriate fitness levels and goals',
                'Explain dietary preferences and their impact',
                'Assist with personal information and privacy settings'
            ],
            'data_types': 'fitness goals, dietary preferences, personal metrics, activity levels'
        },
        'track_data': {
            'focus': 'data logging, workout recording, and nutrition tracking',
            'capabilities': [
                'Guide through workout and nutrition logging',
                'Explain tracking best practices and accuracy',
                'Help categorize exercises and food items',
                'Assist with consistent data recording habits'
            ],
            'data_types': 'workout logs, nutrition entries, water intake, activity tracking'
        },
        'recommendations': {
            'focus': 'AI-powered suggestions for workouts and meals',
            'capabilities': [
                'Explain AI recommendation algorithms and reasoning',
                'Help customize and interpret suggestions',
                'Guide implementation of workout and meal plans',
                'Provide alternatives and modifications to recommendations'
            ],
            'data_types': 'personalized workout plans, meal suggestions, AI insights'
        },
        'progress': {
            'focus': 'analytics, trends, and progress interpretation',
            'capabilities': [
                'Interpret charts, graphs, and progress metrics',
                'Identify patterns and trends in fitness data',
                'Provide actionable insights from analytics',
                'Guide goal adjustment based on progress'
            ],
            'data_types': 'progress charts, trend analysis, comparative metrics, goal tracking'
        }
    }
    
    current_context = context_knowledge.get(page_context, context_knowledge['dashboard'])
    
    # Build conversation context
    conversation_context = ""
    if conversation_history:
        recent_history = conversation_history[-3:]  # Last 3 exchanges
        conversation_context = "\\n\\nRECENT CONVERSATION CONTEXT:\\n"
        for i, exchange in enumerate(recent_history, 1):
            conversation_context += f"  {i}. User: {exchange.get('user', 'N/A')}\\n"
            conversation_context += f"     Bot: {exchange.get('bot', 'N/A')}\\n"
    
    # Construct the comprehensive prompt
    enhanced_prompt = f"""
🤖 FITMIND AI ASSISTANT - CONTEXT-AWARE RESPONSE SYSTEM

ROLE & IDENTITY:
You are FitMind AI, an expert fitness and wellness assistant integrated into the FitMind fitness tracking application. You provide personalized, context-aware guidance to help users achieve their health and fitness goals.

CURRENT SESSION CONTEXT:
📍 Page Focus: {page_context.title()} - {current_context['focus']}
🎯 User ID: {user_id}
⏰ Session Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SPECIALIZED CAPABILITIES FOR {page_context.upper()}:
{chr(10).join(f"  • {capability}" for capability in current_context['capabilities'])}

DATA CONTEXT: {current_context['data_types']}

OPERATIONAL CONSTRAINTS:
{chr(10).join(f"  • {constraint}" for constraint in user_constraints)}

RESPONSE GUIDELINES:
✅ Keep responses concise but comprehensive (2-4 sentences unless complex explanation needed)
✅ Stay focused on {page_context}-related topics and fitness/wellness domain
✅ Use encouraging, motivational, and professional tone
✅ Provide specific, actionable advice when possible
✅ Reference relevant FitMind features and capabilities
✅ Use fitness/health terminology appropriately
✅ Include relevant emojis sparingly for engagement

❌ Don't provide medical diagnoses or replace professional medical advice
❌ Don't discuss topics outside fitness, nutrition, wellness, and the FitMind platform
❌ Don't make assumptions about user's personal data without context
❌ Avoid overly technical jargon without explanation

{conversation_context}

USER'S CURRENT QUESTION:
"{user_message}"

TASK: Provide a helpful, context-aware response that addresses the user's question while staying within the {page_context} context and following all guidelines above.

RESPONSE:"""

    return enhanced_prompt

def format_chat_response(ai_response, page_context):
    """Format and clean the AI response for chat display"""
    
    # Remove any unwanted prefixes or system text
    response = ai_response.strip()
    
    # Remove common AI response prefixes
    prefixes_to_remove = [
        "RESPONSE:",
        "Here's my response:",
        "Based on the context:",
        "According to the information provided:",
        "As FitMind AI,",
        "As your FitMind AI assistant,"
    ]
    
    for prefix in prefixes_to_remove:
        if response.lower().startswith(prefix.lower()):
            response = response[len(prefix):].strip()
    
    # Ensure response isn't too long for chat (max ~500 characters for good UX)
    if len(response) > 500:
        # Try to cut at a sentence boundary
        sentences = response.split('. ')
        truncated = []
        char_count = 0
        
        for sentence in sentences:
            if char_count + len(sentence) + 2 <= 480:  # Leave room for "..."
                truncated.append(sentence)
                char_count += len(sentence) + 2
            else:
                break
        
        if truncated:
            response = '. '.join(truncated) + '.'
            if len(sentences) > len(truncated):
                response += " ..."
        else:
            # If no sentence boundaries work, hard truncate
            response = response[:480] + "..."
    
    # Ensure response ends with proper punctuation
    if response and not response[-1] in '.!?':
        response += '.'
    
    return response
