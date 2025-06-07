import asyncio
import logging
import uuid
from typing import  Optional, Dict, Any
from agents import (
    Agent, 
    Runner, 
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered
)
from tools.rag_search import rag_search
from tools.web_search import web_search
from utils.langfuse_config import configure_langfuse
from utils.guardrails import (
    MathExpertResponse,
    math_input_guardrail_simple,
    math_output_guardrail_simple
)

configure_langfuse("math_expert_agent_with_memory")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("math_expert_agent_with_memory.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MathExpertWithMemory:
    """Math Expert Agent"""
    
    def __init__(self):
        self.agent = None
        self.sessions = {}  # Local session cache
        self.memory_enabled = False  # Disabled for now
        
    def create_agent(self):
        
        self.agent = Agent(
            name="Math Expert",
            instructions="""
            You are a Math expert coach.
            
            Your mission: Help to solve math problems/consepts through clear, comprehensive teaching.
            
            Memory system is not available. Provide standard comprehensive responses:
            - Focus on clear, detailed explanations
            - Include comprehensive coverage of topics
            - Provide general best practices and tips
            - MAINTAIN CONTEXT: When user refers to "previous problem" or "from earlier", use the conversation history provided
            
            APPROACH:
            1. Analyze the problem thoroughly
            2. Use rag_search for Math concepts
            3. Use web_search for advanced techniques
            4. Review conversation history if provided for context
            5. Provide comprehensive solutions
            
            RESPONSE STRUCTURE:
            - Problem Analysis: Break down the question
            - Concept Explanation: Explain underlying principles  
            - Step-by-Step Solution: A very very Detailed logical steps, so anyone reading must understand the solution. This is a perfect place show your expertise and problem solving skills.
            - Alternative Methods: Different approaches
            - Key Formulas: Important formulas used
            - Common Mistakes: Typical errors to avoid
            - Related Topics: Connected JEE concepts
            - Practice Recommendations: Next steps
            - Memory Insights: Learning patterns (not available)
            - Personalized Tips: General advice
            
            QUALITY STANDARDS:
            - Always use both rag_search and web_search
            - Provide multiple solution methods when possible
            - Include rigorous mathematical reasoning
            - Connect to JEE exam patterns
            - Emphasize understanding over memorization
            
            Remember: You're training future engineers. Maintain high standards while being accessible.
            Remember: Always end the conversation with a question seeking for user's feedback. You have to ask a question to the user.
            """,
            model="o4-mini",  # Using o4-mini for orchestration
            tools=[rag_search, web_search],
            input_guardrails=[math_input_guardrail_simple],
            output_guardrails=[math_output_guardrail_simple],
            output_type=MathExpertResponse,
        )
    
    def generate_session_id(self) -> str:
        """Generate a new session ID"""
        return str(uuid.uuid4())
    
    def get_or_create_session(self, session_id: Optional[str] = None, user_id: str = "default_user") -> str:
        """Get existing session or create new one"""
        if session_id and session_id in self.sessions:
            import datetime
            self.sessions[session_id]["last_activity"] = datetime.datetime.now().isoformat()
            self.sessions[session_id]["total_queries"] += 1
            logger.info(f"Using existing session: {session_id}")
            return session_id
        else:
            new_session_id = self.generate_session_id()
            import datetime
            now = datetime.datetime.now().isoformat()
            
            self.sessions[new_session_id] = {
                "session_id": new_session_id,
                "user_id": user_id,
                "created_at": now,
                "last_activity": now,
                "total_queries": 1,
                "conversation_history": []  # Add conversation history
            }
            
            return new_session_id
    
    def add_to_conversation_history(self, session_id: str, query: str, response: str):
        """Add query-response pair to conversation history"""
        if session_id in self.sessions:
            self.sessions[session_id]["conversation_history"].append({
                "query": query,
                "response": response,
                "timestamp": str(uuid.uuid4())[:8]
            })
            # Keep only last 3 exchanges to avoid context overflow
            if len(self.sessions[session_id]["conversation_history"]) > 3:
                self.sessions[session_id]["conversation_history"] = self.sessions[session_id]["conversation_history"][-3:]
    
    def get_conversation_context(self, session_id: str) -> str:
        """Get formatted conversation history for context"""
        if session_id not in self.sessions or not self.sessions[session_id]["conversation_history"]:
            return "No previous conversation in this session."
        
        context = "CONVERSATION HISTORY:\n"
        for i, exchange in enumerate(self.sessions[session_id]["conversation_history"], 1):
            context += f"\nPREVIOUS QUERY {i}: {exchange['query']}\n"
            context += f"PREVIOUS RESPONSE {i} (Summary): {exchange['response'][:500]}...\n"
        
        return context
    
    async def handle_math_query_with_memory(self, query: str, session_id: Optional[str] = None, user_id: str = "default_user") -> Dict[str, Any]:
        """Handle a math query"""
        try:
            current_session_id = self.get_or_create_session(session_id, user_id)
            
            # Get conversation context
            conversation_context = self.get_conversation_context(current_session_id)
            
            # Enhanced query with session context and conversation history
            enhanced_query = f"""
            Session ID: {current_session_id}
            Memory Status: disabled (fallback mode)
            Query #{self.sessions[current_session_id]['total_queries']}
            
            {conversation_context}
            
            CURRENT USER QUERY: {query}
            
            Please provide a comprehensive response using rag_search and web_search.
            If the user refers to "previous problem", "from earlier", or similar context, use the conversation history above.
            """
            
            # Run the agent
            result = await Runner.run(self.agent, enhanced_query)
            response = result.final_output
            
            # Ensure session_id is set
            response.session_id = current_session_id
            
            # Handle missing fields with defaults
            if not hasattr(response, 'memory_insights') or not response.memory_insights:
                response.memory_insights = "Memory system not available - using session context"
            
            if not hasattr(response, 'personalized_tips') or not response.personalized_tips:
                response.personalized_tips = "Focus on practice and concept clarity for success"
            
            # Format response
            formatted_response = f"""

Memory Status: disabled (using session context)
Query #{self.sessions[current_session_id]['total_queries']}

PROBLEM ANALYSIS:
{response.problem_analysis}

CONCEPT EXPLANATION:
{response.concept_explanation}

STEP-BY-STEP SOLUTION:
{response.step_by_step_solution}

ALTERNATIVE METHODS:
{chr(10).join(f"Method {i+1}: {method}" for i, method in enumerate(response.alternative_methods)) if response.alternative_methods else "Standard method provided above"}

KEY FORMULAS USED:
{chr(10).join(f"• {formula}" for formula in response.key_formulas_used) if response.key_formulas_used else "• Basic math formulas"}

COMMON MISTAKES TO AVOID:
{chr(10).join(f"• {mistake}" for mistake in response.common_mistakes_to_avoid) if response.common_mistakes_to_avoid else "• Calculation errors and sign mistakes"}

RELATED TOPICS:
{', '.join(response.related_jee_topics) if response.related_jee_topics else "Math fundamentals"}

DIFFICULTY LEVEL: {response.difficulty_level}
ESTIMATED TIME TO SOLVE: {response.time_to_solve_minutes} minutes

PRACTICE RECOMMENDATIONS:
{response.practice_recommendations}

MEMORY INSIGHTS:
{response.memory_insights}

PERSONALIZED TIPS:
{response.personalized_tips}
{'='*70}
            """
            
            # Add to conversation history for future context
            self.add_to_conversation_history(current_session_id, query, formatted_response)
            
            return {
                "success": True,
                "session_id": current_session_id,
                "response": formatted_response.strip(),
                "structured_response": response,
                "session_info": self.sessions[current_session_id],
                "total_queries": self.sessions[current_session_id]['total_queries'],
                "memory_enabled": self.memory_enabled,
                "has_context": len(self.sessions[current_session_id]["conversation_history"]) > 1
            }
            
        except InputGuardrailTripwireTriggered as e:
            error_msg = "INPUT REJECTED: Please ask math questions only."
            logger.warning(f"Input guardrail triggered: {e}")
            return {
                "success": False,
                "error": error_msg,
                "session_id": session_id,
                "error_type": "input_validation"
            }
            
        except OutputGuardrailTripwireTriggered as e:
            error_msg = "OUTPUT QUALITY CHECK FAILED: Response didn't meet standards. Please try rephrasing."
            logger.warning(f"Output guardrail triggered: {e}")
            return {
                "success": False,
                "error": error_msg,
                "session_id": session_id,
                "error_type": "output_validation"
            }
            
        except Exception as e:
            error_msg = f"SYSTEM ERROR: {str(e)}"
            logger.error(f"Error handling query: {e}")
            return {
                "success": False,
                "error": error_msg,
                "session_id": session_id,
                "error_type": "system_error"
            }

async def main():
    # Simplified testing function
    expert = MathExpertWithMemory()
    expert.create_agent()
    
    # Run a single test query
    test_query = "Solve the integral of x^2 * e^(x^3) dx"
    result = await expert.handle_math_query_with_memory(query=test_query)
    
    if result["success"]:
        print("✓ Test passed!")
        print(result["response"][:500] + "...")  # Print first 500 chars of response
    else:
        print(f"✗ Test failed: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())