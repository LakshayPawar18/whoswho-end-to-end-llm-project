from main import get_few_shot_db_chain

import streamlit as st

# Title of the app
st.title("Consumer Affairs WhosWho")

# Initialize session state for conversation
if 'conversation' not in st.session_state:
    st.session_state.conversation = []

# Display conversation
for message in st.session_state.conversation:
    st.write(message)

# Ambiguity detection function (simple implementation)
def is_ambiguous_query(query):
    # Check if the query is a single word (name)
    return len(query.split()) == 1

# Text input for user message
user_input = st.text_input("Ask the Query:")

# Process user message
if st.button("Send"):
    if is_ambiguous_query(user_input):  # Check if the input is a single name
        response = "When you say '{}', I'm not sure what you're looking for. Could you please provide more details? (Name,Designation, Room Number, Email, etc.)".format(user_input)
    else:
        chain = get_few_shot_db_chain()
        response = chain.run(user_input)
    
    st.session_state.conversation.append(f"User: {user_input}")
    st.session_state.conversation.append(f"AI: {response}")
    st.rerun()  # Rerun the app to update the conversation