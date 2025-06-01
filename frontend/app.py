import streamlit as st
import asyncio
import sys
import os
import time

# Add the backend directory to the Python path
# This is a common way to make modules in a sibling directory importable
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Now we can import from the backend
from backend.agent.main import generate_post_for_prompt
from backend.agent.pdf_extractor import process_and_add_pdf

st.set_page_config(layout="wide")

# --- Session State Initialization ---
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'generated_post' not in st.session_state:
    st.session_state.generated_post = ""
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'user_prompt_input' not in st.session_state:
    st.session_state.user_prompt_input = ""
if 'show_pdf_uploader' not in st.session_state: # For controlling uploader visibility
    st.session_state.show_pdf_uploader = False
if 'pdf_upload_messages' not in st.session_state: # To store messages for batch upload
    st.session_state.pdf_upload_messages = []

# --- Function Definitions (Must be before calls) ---
# --- Dynamic Log Display for Post Generation ---
dynamic_log_display_placeholder = st.empty()

def update_dynamic_logs():
    print(f"[DEBUG] update_dynamic_logs called - processing: {st.session_state.processing}, logs count: {len(st.session_state.logs)}")
    
    if st.session_state.processing and st.session_state.logs:
        print(f"[DEBUG] Showing logs: {st.session_state.logs}")
        # Use with statement for better control
        with dynamic_log_display_placeholder.container():
            st.text_area(
                "Current Generation Logs",
                "\n".join(st.session_state.logs),
                height=150,
                disabled=True,
                key=f"dynamic_logs_{int(time.time() * 1000000)}"  # More unique key
            )
    else:
        dynamic_log_display_placeholder.empty()

async def run_generation(prompt):
    print(f"[DEBUG] Starting run_generation with prompt: {prompt}")
    # Initial state (processing, logs, generated_post) and initial UI update
    # are now handled by the button click handler before this function is called.

    async def streamlit_log_callback(message):
        print(f"[DEBUG] Log callback received: {message}")
        st.session_state.logs.append(message)
        update_dynamic_logs()
        st.rerun() # Force a rerun to update the UI
        # await asyncio.sleep(0.1) # Removed as requested and because st.rerun() makes it unreachable here

    try:
        print(f"[DEBUG] Calling generate_post_for_prompt...")
        post = await generate_post_for_prompt(prompt, async_log_callback=streamlit_log_callback)
        print(f"[DEBUG] Generated post: {post[:100]}...")
        st.session_state.generated_post = post
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(f"[DEBUG] Error occurred: {error_message}")
        st.session_state.logs.append(error_message)
        update_dynamic_logs()
    finally:
        st.session_state.processing = False
        print(f"[DEBUG] Processing completed, final logs: {st.session_state.logs}")
        st.rerun()

# Test the import right away
try:
    print("[DEBUG] Testing backend import...")
    from backend.agent.main import generate_post_for_prompt
    print("[DEBUG] Backend import successful!")
    
    # Test if we can call the function (without awaiting)
    print("[DEBUG] Testing function call...")
    import inspect
    print(f"[DEBUG] Function signature: {inspect.signature(generate_post_for_prompt)}")
    print("[DEBUG] Function test completed!")
    
except Exception as import_error:
    print(f"[ERROR] Import failed: {import_error}")
    import traceback
    print(f"[ERROR] Full traceback: {traceback.format_exc()}")
    st.error(f"Backend import failed: {import_error}")

# Add a simple test that calls the function directly
async def test_function_call():
    """Test if we can actually call the function"""
    print("[DEBUG] test_function_call started")
    try:
        result = await generate_post_for_prompt("test prompt", None)
        print(f"[DEBUG] Function call succeeded: {result[:100] if result else 'No result'}")
        return result
    except Exception as e:
        print(f"[ERROR] Function call failed: {e}")
        import traceback
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        raise

# --- Main App Layout ---
st.title("Hi, I'm Audy, your AI Social Media Marketing Expert.")

col1, col2 = st.columns(2)

with col1:
    st.header("Instructions")
    st.info(
        """
        1. Enter your post idea or topic in the text box below.
        2. Click 'Generate Post' or manage documents via 'Upload PDFs'.
        3. System logs and generated posts will appear below.
        """
    )
    
    st.session_state.user_prompt_input = st.text_area(
        "Enter your LinkedIn post prompt:", 
        value=st.session_state.user_prompt_input,
        height=150,
        placeholder="e.g., Write a post about the future of AI in asset-based lending...",
        key="user_prompt_input_widget"
    )

    # Buttons side-by-side - adjusted for two buttons
    btn_generate_col, btn_upload_col = st.columns(2)

    with btn_generate_col:
        if st.button("Generate Post", disabled=st.session_state.processing, key="generate_button"):
            if st.session_state.user_prompt_input:
                try:
                    print(f"[DEBUG] Generate button clicked with prompt: {st.session_state.user_prompt_input}")
                    # Set initial state for UI update BEFORE blocking asyncio.run
                    st.session_state.processing = True
                    st.session_state.logs = ["Starting LinkedIn post generation..."] # Clear previous logs and set initial message
                    st.session_state.generated_post = ""
                    update_dynamic_logs() # Populate log area with initial message and show processing state
                    
                    # The st.rerun() that was here is removed, allowing asyncio.run to be called.
                    # The UI updates above will be visible while asyncio.run blocks.
                    asyncio.run(run_generation(st.session_state.user_prompt_input))
                        
                except Exception as button_error: # This catches errors from asyncio.run or initial setup
                    error_msg = f"Button click error or error during generation setup: {str(button_error)}"
                    print(f"[ERROR] {error_msg}")
                    st.session_state.logs.append(error_msg)
                    st.session_state.processing = False # Ensure processing is reset
                    update_dynamic_logs() # Show error in logs
                    st.rerun() # Rerun to reflect error state
            else:
                st.warning("Please enter a prompt for the LinkedIn post.")
                
    with btn_upload_col:
        if st.button("Upload PDFs", key="show_upload_button"):
            st.session_state.show_pdf_uploader = True
            st.session_state.pdf_upload_messages = [] # Clear old messages
            st.rerun()

# --- PDF Uploader Section (Modal-like) ---
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

if st.session_state.show_pdf_uploader:
    with st.container(): # Use a container for the modal content area
        st.markdown("***") # Visual separator
        st.subheader("Upload PDF Documents to Knowledge Base")
        uploaded_files = st.file_uploader(
            f"Select PDF files (max {MAX_FILE_SIZE_MB}MB each)", 
            type=["pdf"], 
            accept_multiple_files=True, 
            key="pdf_multi_uploader"
        )

        col_process, col_close_uploader = st.columns(2)
        with col_process:
            if st.button("Process Uploaded Files", key="process_multi_pdf_button"):
                if uploaded_files:
                    st.session_state.pdf_upload_messages = [] # Clear before processing new batch
                    with st.spinner("Processing uploaded PDFs..."):
                        for uploaded_file in uploaded_files:
                            if uploaded_file.size > MAX_FILE_SIZE_BYTES:
                                msg = f"File '{uploaded_file.name}' exceeds {MAX_FILE_SIZE_MB}MB limit and was not processed."
                                st.session_state.pdf_upload_messages.append((msg, "error"))
                                print(f"[App WARNING] {msg}")
                                continue
                            try:
                                pdf_bytes = uploaded_file.getvalue()
                                print(f"[App DEBUG] Processing PDF: {uploaded_file.name}")
                                success, message = process_and_add_pdf(pdf_bytes, uploaded_file.name)
                                if success:
                                    st.session_state.pdf_upload_messages.append((message, "success"))
                                    print(f"[App SUCCESS] {message}")
                                else:
                                    st.session_state.pdf_upload_messages.append((message, "error"))
                                    print(f"[App ERROR] {message}")
                            except Exception as e_process:
                                error_msg = f"Unexpected error processing '{uploaded_file.name}': {e_process}"
                                st.session_state.pdf_upload_messages.append((error_msg, "error"))
                                print(f"[App CRITICAL ERROR] PDF processing: {error_msg}")
                    st.rerun() # Rerun to show messages and clear uploader
                else:
                    st.warning("Please upload at least one PDF file to process.")
        with col_close_uploader:
            if st.button("Close Uploader", key="close_uploader_button"):
                st.session_state.show_pdf_uploader = False
                st.session_state.pdf_upload_messages = [] # Clear messages on close
                st.rerun()

        # Display messages for the current upload batch
        if st.session_state.pdf_upload_messages:
            st.markdown("**Upload Results:**")
            for msg, msg_type in st.session_state.pdf_upload_messages:
                if msg_type == "success":
                    st.success(msg)
                else:
                    st.error(msg)
        st.markdown("***") # Visual separator

# --- Generated Post Display (col2) ---
with col2:
    st.subheader("Generated LinkedIn Post")
    st.text_area(
        "Editable Generated Post", 
        value=st.session_state.generated_post, 
        height=400, 
        key="final_post_output_area",
        help="This is the generated post. You can edit it here."
    )

# --- Final Logs Expander (Full Width) ---
if st.session_state.logs and not st.session_state.processing:
    with st.expander("View Full Generation Logs", expanded=False):
        st.text_area("All Logs", "\n".join(st.session_state.logs), height=200, disabled=True, key="final_logs_expander_area")

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center;'>--- Powered by AudienceAI ---</div>", unsafe_allow_html=True) 