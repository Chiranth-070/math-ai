import streamlit as st
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any
import logging
import tempfile
import os

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.agent import MathExpertWithMemory
from utils.image_to_text import get_text_from_image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="Mathematics Expert",
    page_icon="∫",
    layout="wide"
)

# --- THEME AND LAYOUT CSS ---
st.markdown("""
<style>
    /* === Base Theme === */
    .stApp {
        background-color: #0F1116 !important;
    }
    
    /* === Chat Message Styling === */
    .stChatMessage {
        background-color: #262730 !important;
        border-radius: 15px !important;
        margin: 0.5rem 0 !important;
    }
    
    .stChatMessage[data-testid*="user"] {
        background-color: #1976d2 !important;
    }
    
    .stChatMessage[data-testid*="assistant"] {
        background-color: #262730 !important;
        border-left: 4px solid #1f77b4 !important;
    }
    
    /* === Input Area Styling === */
    .stChatInput {
        background-color: #262730 !important;
    }
    
    .stChatInput > div > div > div > div {
        background-color: #262730 !important;
        color: #FAFAFA !important;
    }
    
    /* === File Uploader in Sidebar === */
    .stFileUploader {
        background-color: #262730 !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }
    
    /* === Section Headers === */
    .section-header {
        font-size: 1.1rem;
        font-weight: bold;
        color: #66b2ff !important;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        border-bottom: 1px solid #333;
        padding-bottom: 0.3rem;
    }
    
    /* === Error Messages === */
    .error-message {
        background-color: #422a2a !important;
        border-left: 4px solid #ff4444 !important;
        padding: 1rem !important;
        border-radius: 10px !important;
        margin: 0.5rem 0 !important;
    }
    
    /* === Welcome Message === */
    .welcome-message {
        text-align: center;
        padding: 2rem;
        background-color: #262730;
        border-radius: 15px;
        margin: 1rem 0;
    }
    
    /* === Math Response Formatting === */
    .math-section {
        margin: 1rem 0;
        padding: 1rem;
        background-color: #1e1e1e;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
    }
    
    .math-section h4 {
        color: #4CAF50 !important;
        margin-bottom: 0.8rem;
    }
    
    .math-steps {
        line-height: 1.8;
    }
    
    .math-formula {
        background-color: #2d2d2d;
        padding: 0.3rem 0.6rem;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        margin: 0.2rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "expert" not in st.session_state:
    st.session_state.expert = None
    st.session_state.current_session_id = None
    st.session_state.initialized = False

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Welcome to the Mathematics Expert! I can help you solve complex math problems. You can type your question or upload an image of a math problem."}
    ]

# --- Sidebar ---
with st.sidebar:
    st.title("📷 Upload Image")
    #note
    st.markdown("- after uploading type solve and press enter to get the answer.")
    st.markdown("- after getting the answer remove the uploaded image.")
    
    
    # File uploader in sidebar - Fixed deprecated parameter
    uploaded_file = st.file_uploader(
        "", 
        type=['png'], 
        help="Upload a PNG image of your math problem"
    )
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
        
    st.markdown("---")
    
    # New chat button
    if st.button("🔄 New Chat", use_container_width=True):
        st.session_state.current_session_id = None
        st.session_state.messages = [
            {"role": "assistant", "content": "👋 Welcome to the Mathematics Expert! I can help you solve complex math problems. You can type your question or upload an image of a math problem."}
        ]
        st.rerun()
    
    st.markdown("---")
    st.markdown("### Features:")
    st.markdown("• Step-by-step solutions")
    st.markdown("• Concept explanations")
    st.markdown("• Alternative methods")
    st.markdown("• Common mistakes to avoid")
    st.markdown("• Image problem solving")

# --- Core Functions ---
def initialize_expert():
    try:
        if not st.session_state.initialized:
            st.session_state.expert = MathExpertWithMemory()
            st.session_state.expert.create_agent()
            st.session_state.initialized = True
            logger.info("Expert initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize expert: {e}")
        st.error(f"Failed to initialize expert: {e}")
        return False

def run_async_query(query: str) -> Dict[str, Any]:
    """Runs an async query in a sync context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(
        st.session_state.expert.handle_math_query_with_memory(  
            query=query, session_id=st.session_state.current_session_id, user_id="streamlit_user"
        )
    )
    if result.get("success"):
        st.session_state.current_session_id = result.get("session_id")
    return result

def process_uploaded_image(uploaded_file) -> str:
    """Process uploaded image and extract text."""
    tmp_file_path = None
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_file_path = tmp_file.name

        # Extract text from image
        extracted_text = get_text_from_image(tmp_file_path)
        return extracted_text
        
    except Exception as e:
        return f"Error processing image: {str(e)}"
    finally:
        # Ensure temporary file is always deleted
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
                logger.info(f"Temporary image file deleted: {tmp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete temporary file {tmp_file_path}: {cleanup_error}")

def format_math_response(response) -> str:
    """Format the structured response into a readable format with better spacing and organization."""
    formatted_parts = []
    
    if response.problem_analysis:
        formatted_parts.append(f"""
### 🔍 Problem Analysis
{response.problem_analysis}
""")
    
    if response.step_by_step_solution:
        # Clean up the step-by-step solution for better readability
        solution = response.step_by_step_solution
        # Add line breaks for better formatting
        solution = solution.replace('. ', '.\n\n')
        solution = solution.replace('=> ', '\n\n**➤** ')
        solution = solution.replace('Set ', '\n**Step:** Set ')
        
        formatted_parts.append(f"""
### 📝 Step-by-Step Solution
{solution}
""")

    if response.concept_explanation:
        explanation = response.concept_explanation
        # Format the explanation for better readability
        explanation = explanation.replace(': ', ':\n\n')
        explanation = explanation.replace(', ', ',\n')
        
        formatted_parts.append(f"""
### 💡 Concept Explanation
{explanation}
""")

    if response.alternative_methods and any(response.alternative_methods):
        methods = []
        for i, method in enumerate(response.alternative_methods, 1):
            methods.append(f"**Method {i}:** {method}")
        methods_text = "\n\n".join(methods)
        formatted_parts.append(f"""
### 🔄 Alternative Methods
{methods_text}
""")

    if response.key_formulas_used and any(response.key_formulas_used):
        formulas = []
        for formula in response.key_formulas_used:
            formulas.append(f"```\n{formula}\n```")
        formulas_text = "\n".join(formulas)
        formatted_parts.append(f"""
### 📐 Key Formulas Used
{formulas_text}
""")
    
    if response.common_mistakes_to_avoid and any(response.common_mistakes_to_avoid):
        mistakes = []
        for i, mistake in enumerate(response.common_mistakes_to_avoid, 1):
            mistakes.append(f"**{i}.** {mistake}")
        mistakes_text = "\n\n".join(mistakes)
        formatted_parts.append(f"""
### ⚠️ Common Mistakes to Avoid
{mistakes_text}
""")
        
    if response.related_jee_topics and any(response.related_jee_topics):
        topics = " • ".join(response.related_jee_topics)
        formatted_parts.append(f"""
### 🔗 Related Math Topics
{topics}
""")
    
    return "\n\n---\n\n".join(formatted_parts)

# --- Main App ---
st.title("Mathematics Expert")

# Auto-initialize the expert
if not st.session_state.initialized:
    with st.spinner("Initializing math expert..."):
        if initialize_expert():
            logger.info("Expert auto-initialized successfully")
        else:
            st.error("Failed to initialize the math expert. Please refresh the page.")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your math question here..."):
    if not st.session_state.initialized:
        st.error("Math expert is not initialized. Please refresh the page.")
        st.stop()
    
    # Determine the final query
    final_query = ""
    has_image = False
    
    # Process image if uploaded
    if uploaded_file is not None:
        with st.spinner("📷 Extracting question from image..."):
            extracted_text = process_uploaded_image(uploaded_file)
            final_query = extracted_text
            has_image = True
            # Clear the uploaded file after processing
            st.session_state.pop('uploaded_file', None)
    
    # Use text query if no image or combine both
    if prompt.strip():
        if final_query:
            final_query = f"Image question: {final_query}\n\nAdditional context: {prompt.strip()}"
        else:
            final_query = prompt.strip()
    
    if final_query:
        # Add user message to chat
        user_content = f"{'📷 ' if has_image else ''}{prompt}"
        st.session_state.messages.append({"role": "user", "content": user_content})
        with st.chat_message("user"):
            st.markdown(user_content)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("🧠 Thinking..."):
                result = run_async_query(final_query)
                
                if result and result.get("success"):
                    response = result.get("structured_response")
                    if response:
                        formatted_response = format_math_response(response)
                        st.markdown(formatted_response)
                        st.session_state.messages.append({"role": "assistant", "content": formatted_response})
                    else:
                        error_msg = "I received an empty response. Could you please try rephrasing your question?"
                        st.markdown(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                else:
                    error_msg = f"❌ **Error:** {result.get('error', 'Unknown error occurred')}"
                    st.markdown(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    else:
        st.warning("Please provide a question or upload an image.")

# Clear uploaded file after each interaction
if uploaded_file and 'uploaded_file' in st.session_state:
    st.session_state.pop('uploaded_file', None)