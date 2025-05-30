import streamlit as st
import asyncio
import sys
import os

# Add the backend directory to the Python path
# This is a common way to make modules in a sibling directory importable
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Now we can import from the backend
from backend.agent.main import generate_post_for_prompt

st.set_page_config(layout="wide")

st.title("AI LinkedIn Post Generator")

st.sidebar.header("Instructions")
st.sidebar.info(
    """
    1. Enter your post idea or topic in the text box below.
    2. Click the 'Generate Post' button.
    3. The system will analyze your prompt, potentially use tools to gather information (you'll see logs of this process), and then generate a LinkedIn post for you.
    """
)

user_prompt = st.text_area("Enter your LinkedIn post prompt:", height=100, placeholder="e.g., Write a post about the future of AI in asset-based lending, mentioning ABLSoft.")

# Session state to store logs and results
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'generated_post' not in st.session_state:
    st.session_state.generated_post = ""
if 'processing' not in st.session_state:
    st.session_state.processing = False


async def run_generation(prompt):
    st.session_state.processing = True
    st.session_state.logs = ["Starting LinkedIn post generation..."] # Initial log
    st.session_state.generated_post = ""
    
    # Placeholders for dynamic content
    log_placeholder = st.empty() # For logs
    post_placeholder = st.empty() # For the final post

    # Display initial log
    log_placeholder.info("\n".join(st.session_state.logs))

    async def streamlit_log_callback(message):
        """Callback function to update Streamlit UI with new log messages."""
        st.session_state.logs.append(message)
        log_placeholder.info("\n".join(st.session_state.logs)) # Update the placeholder
        await asyncio.sleep(0) # Allow Streamlit to process UI updates

    try:
        # Call the backend function, passing the new callback
        post = await generate_post_for_prompt(prompt, async_log_callback=streamlit_log_callback)
        
        st.session_state.generated_post = post
        
        # Final update to logs (might include backend messages after the last tool log)
        log_placeholder.info("\n".join(st.session_state.logs))

        if st.session_state.generated_post:
            post_placeholder.success("Generated LinkedIn Post:") # Changed from st.write to post_placeholder.success
            post_placeholder.markdown(st.session_state.generated_post)
        else:
            post_placeholder.warning("No post was generated, or an error occurred after logging.")
            
    except Exception as e:
        # Use the callback for errors happening during the backend call if possible,
        # otherwise append directly.
        error_message = f"An error occurred: {str(e)}"
        # If the callback is available and the error is from the backend, it would have used it.
        # This handles errors more broadly in the Streamlit part or if the callback failed.
        st.session_state.logs.append(error_message)
        log_placeholder.error("\n".join(st.session_state.logs))
        # import traceback
        # st.session_state.logs.append(traceback.format_exc())
        # log_placeholder.error("\n".join(st.session_state.logs))
    finally:
        st.session_state.processing = False
        # The permanent log display below will show the final state.

if st.button("Generate Post", disabled=st.session_state.processing):
    if user_prompt:
        # Check if an event loop is already running
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # No event loop is running
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(run_generation(user_prompt))
    else:
        st.warning("Please enter a prompt for the LinkedIn post.")

# Display areas for logs and the generated post
# The log_placeholder and post_placeholder handle dynamic updates during processing.
# These sections below will ensure the final state is visible and correctly formatted,
# especially if the placeholders are cleared or if the user wants to see them in an expander.

if st.session_state.logs: # Always show logs if they exist
    with st.expander("Generation Logs", expanded=True if st.session_state.processing else False):
        # Using st.text_area for a scrollable, selectable log box
        st.text_area("Logs_final", "\n".join(st.session_state.logs), height=300, disabled=True, key="logs_final_area")

if st.session_state.generated_post and not st.session_state.processing: 
    st.subheader("Final Generated LinkedIn Post")
    st.markdown(st.session_state.generated_post)

st.sidebar.markdown("---_Powered by AudienceAI_---") 