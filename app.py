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
    layout="wide",
    initial_sidebar_state="collapsed"  # Collapse sidebar by default
)

# Hide sidebar
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# --- THEME AND LAYOUT CSS ---
st.markdown("""
<style>
    /* === Base Theme and Body === */
    html, body, [class*="st-"], .main {
        background-color: #0F1116 !important; /* Dark background */
        color: #FAFAFA !important; /* Light text */
    }

    /* Hide Streamlit's default header and footer */
    .stApp > header, .stApp > footer {
        display: none !important;
    }
    
    /* === Main Layout (Flexbox) === */
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
        height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: space-between; /* Pushes input to bottom */
    }

    /* === Scrollable Message Area === */
    .messages-container {
        flex-grow: 1; /* Allows container to grow */
        overflow-y: auto; /* Enables vertical scrolling */
        padding: 1rem 2rem;
        width: 100%;
    }

    /* === Message Bubbles === */
    .user-message, .bot-response, .error-container, .welcome-container {
        margin: 1rem 0;
        padding: 1.2rem;
        border-radius: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    .user-message *, .bot-response *, .error-container *, .welcome-container * {
        color: #FAFAFA !important; /* White text for all content inside bubbles */
    }
    
    .user-message h3, .bot-response h3, .error-container h3, .welcome-container h3 {
        color: #FAFAFA !important;
    }
    
    .user-message p, .bot-response p, .error-container p, .welcome-container p {
        color: #E0E0E0 !important; /* Slightly off-white for paragraphs */
    }

    .user-message {
        background-color: #262730;
        border-left: 4px solid #1976d2;
        margin-left: 20%;
    }

    .bot-response {
        background-color: #262730;
        border-left: 4px solid #1f77b4;
        margin-right: 20%;
    }
    
    .error-container {
        background-color: #422a2a;
        border-left: 4px solid #ff4444;
    }
    
    .welcome-container {
        background-color: #262730;
        text-align: center;
        padding: 2rem;
    }

    /* === Bot Response Sections === */
    .section-header {
        font-size: 1.3rem;
        font-weight: bold;
        color: #66b2ff !important; /* Bright blue for headers */
        margin-top: 1.5rem;
        border-bottom: 2px solid #333;
        padding-bottom: 0.5rem;
    }

    .session-info {
        background-color: #1e3a4c;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        border-left: 4px solid #4caf50;
        margin-bottom: 1rem;
        font-size: 0.9rem;
    }

    /* === Fixed Input Bar at the Bottom === */
    .input-fixed {
        flex-shrink: 0; /* Prevents the input bar from shrinking */
        background-color: #0F1116; /* Match main background */
        padding: 1rem 2rem;
        border-top: 1px solid #333;
    }
    
    /* Make input text area visible */
    .stTextArea, .stTextArea > div, .stTextArea > div > textarea {
        background-color: #262730 !important;
        color: #FAFAFA !important;
    }

    /* File uploader styling */
    .stFileUploader > div {
        background-color: #262730 !important;
        color: #FAFAFA !important;
    }

    .stForm {
        border: none !important;
        padding: 0 !important;
    }

    /* Image preview styling */
    .uploaded-image {
        border: 2px solid #333;
        border-radius: 10px;
        margin: 0.5rem 0;
    }

</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "expert" not in st.session_state:
    st.session_state.expert = None
    st.session_state.current_session_id = None
    st.session_state.initialized = False
    st.session_state.conversation_history = []

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

def display_conversation():
    """Displays the conversation history."""
    if not st.session_state.conversation_history:
        st.markdown(
            '<div class="welcome-container">'
            '<h3>👋 Welcome to the Mathematics Expert!</h3>'
            '</div>', 
            unsafe_allow_html=True
        )
        return

    for entry in st.session_state.conversation_history:
        # Check if this entry has an image
        if entry.get("has_image"):
            st.markdown(f'<div class="user-message"><strong>🧑‍🎓 You (Image):</strong><p>{entry["query"]}</p></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="user-message"><strong>🧑‍🎓 You:</strong><p>{entry["query"]}</p></div>', unsafe_allow_html=True)
        
        result = entry.get("result")
        if result and result.get("success"):
            response = result.get("structured_response")
            if response:
                if response.problem_analysis:
                    st.markdown('<div class="section-header">Problem Analysis</div>', unsafe_allow_html=True)
                    st.markdown(response.problem_analysis)
                
                if response.step_by_step_solution:
                    st.markdown('<div class="section-header">Step-by-Step Solution</div>', unsafe_allow_html=True)
                    st.markdown(response.step_by_step_solution)

                # Display concept explanation
                if response.concept_explanation:
                    st.markdown('<div class="section-header">Concept Explanation</div>', unsafe_allow_html=True)
                    st.markdown(response.concept_explanation)

                # Display alternative methods
                if response.alternative_methods and any(response.alternative_methods):
                    st.markdown('<div class="section-header">Alternative Methods</div>', unsafe_allow_html=True)
                    for method in response.alternative_methods:
                        st.markdown(f"- {method}")

                # Display key formulas
                if response.key_formulas_used and any(response.key_formulas_used):
                    st.markdown('<div class="section-header">Key Formulas Used</div>', unsafe_allow_html=True)
                    for formula in response.key_formulas_used:
                        st.markdown(f"- `{formula}`")
                
                # Display common mistakes
                if response.common_mistakes_to_avoid and any(response.common_mistakes_to_avoid):
                    st.markdown('<div class="section-header">Common Mistakes to Avoid</div>', unsafe_allow_html=True)
                    for mistake in response.common_mistakes_to_avoid:
                        st.markdown(f"- {mistake}")
                    
                # Display related topics
                if response.related_jee_topics and any(response.related_jee_topics):
                    st.markdown('<div class="section-header">Related Math Topics</div>', unsafe_allow_html=True)
                    st.markdown(", ".join(response.related_jee_topics))
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="bot-response"><p>I received an empty response. Could you please try rephrasing?</p></div>', unsafe_allow_html=True)

        elif result:
            st.markdown(f'<div class="error-container"><strong>🤖 Expert:</strong><p>{result.get("error", "Unknown error")}</p></div>', unsafe_allow_html=True)

def main():
    """Defines the main Streamlit application layout."""
    
    # Auto-initialize the expert
    if not st.session_state.initialized:
        with st.spinner("Initializing math expert..."):
            if initialize_expert():
                logger.info("Expert auto-initialized successfully")
            else:
                st.error("Failed to initialize the math expert. Please refresh the page.")
    
    # --- Main Content Area (Messages + Input) ---
    
    # Add a reset button at the top
    col1, col2 = st.columns([7, 1])
    with col2:
        if st.button("🔄 New Chat"):
            st.session_state.current_session_id = None
            st.session_state.conversation_history = []
            st.rerun()
    
    # Scrollable container for messages
    st.markdown('<div class="messages-container">', unsafe_allow_html=True)
    display_conversation()
    st.markdown('</div>', unsafe_allow_html=True)

    # Fixed input form at the bottom
    st.markdown('<div class="input-fixed">', unsafe_allow_html=True)
    
    with st.form(key="query_form", clear_on_submit=True):
        # Image upload option
        uploaded_file = st.file_uploader("Upload math problem image (PNG only):", type=['png'], key="image_uploader")
        
        # Show uploaded image preview
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Uploaded Image", use_column_width=True, clamp=True)
        
        # Text input
        query = st.text_area("Type your question here (or upload image above):", key="query_input", label_visibility="collapsed", placeholder="e.g., Solve ∫ x * sin(x) dx")
        submitted = st.form_submit_button("Solve")

    if submitted:
        final_query = ""
        has_image = False
        
        # Process image if uploaded
        if uploaded_file is not None:
            with st.spinner("📷 Extracting question from image..."):
                extracted_text = process_uploaded_image(uploaded_file)
                final_query = extracted_text
                has_image = True
        
        # Use text query if no image or if both provided
        if query.strip():
            if final_query:
                final_query = f"Image question: {final_query}\n\nAdditional context: {query.strip()}"
            else:
                final_query = query.strip()
        
        if final_query:
            with st.spinner("🧠 Thinking..."):
                result = run_async_query(final_query)
                st.session_state.conversation_history.append({
                    "query": final_query, 
                    "result": result,
                    "has_image": has_image
                })
            st.rerun()
        else:
            st.warning("Please provide a question or upload an image.")
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()