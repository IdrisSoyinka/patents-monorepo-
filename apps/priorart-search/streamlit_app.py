import streamlit as st
import uuid
from typing import Dict, Any
import json
import time

# Import your patent search function
from src.patent_search_agent.graph import run_patent_search, create_graph
from langgraph.types import Command

# Configure Streamlit page
st.set_page_config(
    page_title="Patent Search Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .step-header {
        font-size: 1.5rem;
        color: #ff7f0e;
        margin: 1rem 0;
    }
    .keyword-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'app' not in st.session_state:
        st.session_state.app = None
    if 'thread_id' not in st.session_state:
        st.session_state.thread_id = None
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    if 'result' not in st.session_state:
        st.session_state.result = None
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    if 'patent_description_input' not in st.session_state:
        st.session_state.patent_description_input = ""
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = set()

def display_keywords(keywords: Dict, title: str):
    """Display keywords in a formatted box"""
    st.markdown(f"<div class='keyword-box'>", unsafe_allow_html=True)
    st.write(f"**{title}**")
    if keywords:
        for category, kw_list in keywords.items():
            st.write(f"- **{category.replace('_', ' ').title()}**: {', '.join(kw_list)}")
    else:
        st.write("No keywords generated yet.")
    st.markdown("</div>", unsafe_allow_html=True)

def display_result_summary(result: Dict):
    """Display a summary of the search results"""
    st.markdown("<div class='success-box'>", unsafe_allow_html=True)
    st.write("### 🎉 Search Completed Successfully!")
    
    if 'seed_keywords' in result:
        st.write("**Final Keywords:**")
        display_keywords(result['seed_keywords'], "Generated Keywords")
    
    if 'concepts' in result:
        st.write("**Extracted Concepts:**")
        concepts = result['concepts']
        if isinstance(concepts, dict):
            for key, value in concepts.items():
                st.write(f"- **{key}**: {value}")
    
    if 'messages' in result and result['messages']:
        st.write(f"**Total Messages**: {len(result['messages'])}")
    
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    # Initialize session state
    initialize_session_state()
    
    # Main header
    st.markdown("<h1 class='main-header'>🔍 Patent Search Agent</h1>", unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Model selection
        model_name = st.selectbox(
            "Select Model",
            options=["qwen3:4b-instruct-2507-fp16", "llama2", "mistral"],
            index=0,
            help="Choose the LLM model for patent search"
        )
        
        # Max results
        max_results = st.slider(
            "Max Results",
            min_value=5,
            max_value=50,
            value=10,
            help="Maximum number of search results"
        )
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            enable_debug = st.checkbox("Enable Debug Mode", value=False)
            auto_accept = st.checkbox("Auto-accept keywords", value=False)
        
        # Search history
        if st.session_state.search_history:
            st.header("📝 Search History")
            for i, search in enumerate(st.session_state.search_history[-5:]):  # Show last 5
                with st.expander(f"Search {i+1}: {search['description'][:50]}..."):
                    st.write(f"**Model**: {search['model']}")
                    st.write(f"**Max Results**: {search['max_results']}")
                    st.write(f"**Status**: {search['status']}")

    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📝 Patent Description")

        uploaded_files = st.file_uploader(
            "Drag and drop text files or paste your description below",
            type=["txt", "md", "rtf", "csv", "json"],
            accept_multiple_files=True,
            help="Upload text-based files to prefill the patent description"
        )

        if uploaded_files:
            new_files_added = False

            for uploaded_file in uploaded_files:
                file_identifier = (uploaded_file.name, uploaded_file.size)

                if file_identifier in st.session_state.processed_files:
                    continue

                file_bytes = uploaded_file.getvalue()
                text_content = None

                for encoding in ("utf-8", "utf-16", "latin-1"):
                    try:
                        text_content = file_bytes.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue

                if text_content is None:
                    st.warning(f"Unable to read {uploaded_file.name} as text. Please upload a text-based file.")
                    continue

                if st.session_state.patent_description_input:
                    st.session_state.patent_description_input += "\n\n"

                st.session_state.patent_description_input += text_content.strip()
                st.session_state.processed_files.add(file_identifier)
                new_files_added = True

            if new_files_added:
                st.success("Uploaded file content added to the patent description below.")

        # Patent description input
        patent_description = st.text_area(
            "Enter your patent description",
            height=200,
            placeholder="""Example: A smart wearable device for continuous health monitoring that integrates multiple biosensors including heart rate, blood oxygen saturation, skin temperature, and motion sensors. The device uses machine learning algorithms to analyze the collected data and predict potential health issues.""",
            help="Provide a detailed description of your patent or invention",
            key="patent_description_input"
        )

        # Action buttons
        col_btn1, col_btn2, col_btn3 = st.columns(3)

        with col_btn1:
            start_search = st.button("🚀 Start Search", type="primary", use_container_width=True)

        with col_btn2:
            reset_search = st.button("🔄 Reset", use_container_width=True)

        with col_btn3:
            clear_history = st.button("🗑️ Clear History", use_container_width=True)

    with col2:
        st.header("📊 Search Progress")
        
        # Progress indicator
        progress_steps = [
            "Concept Extraction",
            "Keyword Generation", 
            "Human Validation",
            "Enhancement",
            "IPC Classification",
            "Query Generation",
            "Completed"
        ]
        
        for i, step in enumerate(progress_steps):
            if i < st.session_state.current_step:
                st.success(f"✅ {step}")
            elif i == st.session_state.current_step:
                st.info(f"🔄 {step}")
            else:
                st.empty()
                st.write(f"⏳ {step}")

    # Handle button actions
    if clear_history:
        st.session_state.search_history = []
        st.success("Search history cleared!")
        st.rerun()

    if reset_search:
        st.session_state.app = None
        st.session_state.thread_id = None
        st.session_state.current_step = 0
        st.session_state.result = None
        st.session_state.patent_description_input = ""
        st.session_state.processed_files = set()
        st.success("Search reset!")
        st.rerun()

    if start_search and patent_description.strip():
        try:
            # Initialize the search
            with st.spinner("Initializing patent search..."):
                st.session_state.app = create_graph(model_name=model_name)
                st.session_state.thread_id = str(uuid.uuid4())
                st.session_state.current_step = 1
            
            # Prepare initial state
            initial_state = {
                "patent_description": patent_description,
                "max_results": max_results,
                "messages": [],
            }
            
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            
            # Step 1: Run until first interrupt
            st.markdown("<h2 class='step-header'>🚀 Step 1: Initial Processing</h2>", unsafe_allow_html=True)
            
            with st.spinner("Extracting concepts and generating keywords..."):
                result = st.session_state.app.invoke(initial_state, config=config)
                st.session_state.result = result
                st.session_state.current_step = 2
            
            st.success("Initial processing completed!")
            
            # Display generated keywords
            if 'seed_keywords' in result:
                st.markdown("<h3>🔑 Generated Keywords</h3>", unsafe_allow_html=True)
                display_keywords(result['seed_keywords'], "Initial Keywords")
                
                # Keyword validation interface
                st.markdown("<h3>✋ Human Validation Required</h3>", unsafe_allow_html=True)
                
                col_accept, col_edit, col_reject = st.columns(3)
                
                with col_accept:
                    if st.button("✅ Accept Keywords", type="primary", use_container_width=True):
                        with st.spinner("Accepting keywords and continuing..."):
                            accept_command = Command(resume=[{"type": "accept"}])
                            result = st.session_state.app.invoke(accept_command, config=config)
                            st.session_state.result = result
                            st.session_state.current_step = 6
                        
                        display_result_summary(result)
                        
                        # Add to search history
                        st.session_state.search_history.append({
                            "description": patent_description[:100],
                            "model": model_name,
                            "max_results": max_results,
                            "status": "Completed (Accepted)",
                            "timestamp": time.time()
                        })
                
                with col_edit:
                    with st.popover("✏️ Edit Keywords"):
                        st.write("Modify the generated keywords:")
                        
                        # Create editable keyword fields
                        edited_keywords = {}
                        if 'seed_keywords' in result:
                            for category, keywords in result['seed_keywords'].items():
                                edited_keywords[category] = st.text_input(
                                    f"{category.replace('_', ' ').title()}",
                                    value=", ".join(keywords),
                                    key=f"edit_{category}"
                                ).split(", ")
                        
                        if st.button("💾 Save Edits", use_container_width=True):
                            with st.spinner("Applying edits and continuing..."):
                                edit_command = Command(resume=[{
                                    "type": "edit",
                                    "args": {"keywords": edited_keywords}
                                }])
                                result = st.session_state.app.invoke(edit_command, config=config)
                                st.session_state.result = result
                                st.session_state.current_step = 6
                            
                            display_result_summary(result)
                            
                            # Add to search history
                            st.session_state.search_history.append({
                                "description": patent_description[:100],
                                "model": model_name,
                                "max_results": max_results,
                                "status": "Completed (Edited)",
                                "timestamp": time.time()
                            })
                            st.rerun()
                
                with col_reject:
                    if st.button("❌ Reject Keywords", use_container_width=True):
                        with st.spinner("Rejecting keywords and regenerating..."):
                            reject_command = Command(resume=[{"type": "reject"}])
                            result = st.session_state.app.invoke(reject_command, config=config)
                            st.session_state.result = result
                            st.session_state.current_step = 3
                        
                        st.warning("Keywords rejected. New keywords will be generated.")
                        
                        # Add to search history
                        st.session_state.search_history.append({
                            "description": patent_description[:100],
                            "model": model_name,
                            "max_results": max_results,
                            "status": "Rejected - Regenerated",
                            "timestamp": time.time()
                        })
                        st.rerun()
            
            # Debug information
            if enable_debug:
                with st.expander("🐛 Debug Information"):
                    st.json(result)
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            if enable_debug:
                st.exception(e)
    
    elif start_search and not patent_description.strip():
        st.warning("Please enter a patent description before starting the search.")

    # Display current result if available
    if st.session_state.result and st.session_state.current_step >= 6:
        st.markdown("<h2 class='step-header'>📋 Final Results</h2>", unsafe_allow_html=True)
        display_result_summary(st.session_state.result)
        
        # Download results as JSON
        if st.download_button(
            label="📥 Download Results",
            data=json.dumps(st.session_state.result, indent=2),
            file_name=f"patent_search_results_{st.session_state.thread_id[:8]}.json",
            mime="application/json"
        ):
            st.success("Results downloaded!")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "Patent Search Agent - Powered by LangGraph & Streamlit"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
