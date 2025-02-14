import streamlit as st
import requests
import json
import os

# Initialize session state for messages and chat history if they don't exist
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi. I will answer your questions based on the documents in the sidebar. Ask away!"}
    ]
    st.session_state.chat_history = []  # This will store the LangChain format history

def get_document_names():
    """Get list of document names from the docs directory"""
    docs_path = './docs/'
    files = os.listdir(docs_path)
    # Get base names without extensions and sort them
    doc_names = sorted([os.path.splitext(file)[0] for file in files if file.endswith('.pdf')])
    return doc_names

def chat_with_backend(question):
    """Make a POST request to the Flask backend"""
    try:
        # st.write(f"Sending request to backend...")
        
        payload = {
            'question': question,
            'chat_history': st.session_state.chat_history
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'http://localhost:8501'  # Add Streamlit's default port
        }
        
        response = requests.post(
            'http://127.0.0.1:5000/chat',
            json=payload,
            headers=headers,
            timeout=30
        )
        
        # st.write(f"Response status code: {response.status_code}")
        # st.write(f"Response headers: {response.headers}")
        # st.write(f"Raw response: {response.text}")  # Add this for debugging
        
        if response.status_code == 204 or not response.text:  # Handle empty responses
            return "Error: Empty response from server"
            
        try:
            response_data = response.json()
            print(response_data)
            if response.status_code == 200:
                st.session_state.chat_history = response_data['chat_history']
                answer = response_data['answer']
                sources = response_data.get('sources', [])
                
                # Only add source information if we have good matches
                if sources and len(answer)>200:
                    source_text = "\n\nSources:"
                    for source in sources:
                        file_name = source.get('file_name', 'Unknown')
                        page = source.get('page', 'N/A')
                        source_text += f"\n- {file_name} (Page {page})"
                    return f"{answer}{source_text}"
                else:
                    return answer  # Return just the answer without sources if no good matches
                
            else:
                error_msg = response_data.get('error', 'Unknown error occurred')
                st.error(f"Server error: {error_msg}")
                return f"Error: {error_msg}"
        except json.JSONDecodeError as e:
            st.error(f"Failed to decode JSON response. Raw response: {response.text}")
            return "Error: Invalid response from server"
            
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend server. Please make sure the Flask server is running on http://localhost:5000")
        return "Error: Connection failed"
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return f"Error: {str(e)}"

def main():
    st.title('Welcome to QubeGPT')
    
    # Sidebar with document names and user guide
    with st.sidebar:
        st.header("📚 Available Documents")
        doc_names = get_document_names()
        for doc in doc_names:
            st.markdown(f"- {doc}")
        
        st.markdown("---")  # Separator
        
        # st.header("🔍 Coming soon?")
        # st.markdown("Pls email the document in PDF format to beth@qubecinema.com")
        
        if st.button("Reset Chat"):
            st.session_state.messages = [
                {"role": "assistant", "content": "Ask your questions about the documents."}
            ]
            st.session_state.chat_history = []
            st.rerun()
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Handle user input
    if prompt := st.chat_input("What's on your mind?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Fetching..."):
                # Get response from Flask backend
                response = chat_with_backend(prompt)
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()


