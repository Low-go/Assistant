import json
import openai
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import streamlit as st
from dotenv import load_dotenv
import os
from datetime import datetime
import uuid
import pytz


# This is a basic chaatbot template. Use this as the foundation of your altered 
# chatBots. Its basic functionality is API calls to OpenAi and displays it in a streamed 
# format with the user history also displayed using streamlit for its interface.

#this is for the firebase database

if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(uuid.uuid4())[:8]
session_id = st.session_state['session_id']

# For session_start_time, you can do something similar:
if 'session_start_time' not in st.session_state:
    hawaii = pytz.timezone('Pacific/Honolulu')
    st.session_state['session_start_time'] = datetime.now(hawaii)
session_start_time = st.session_state['session_start_time']


@st.cache_data()
def initialize_firebase():
    cred = credentials.Certificate(json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT_KEY"]))
    firebase_admin.initialize_app(cred, { 'databaseURL' : 'https://chatstore-history-default-rtdb.firebaseio.com/'})

initialize_firebase()


#function to record database entrys by user or ai
def record_output(role, output):
    reference = session_ref.child('outputs')
    output_data = {
        'role' : role,
        'content' : output,   
    }
    reference.push(output_data)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Streamlit layout
st.sidebar.markdown("<h1 style='color: grey;'>BYUH Faculty of Math and Computing</h1>", unsafe_allow_html=True)
st.subheader("AI Assistant: Ask Me Anything")

# Initialize session state for chat display and bot reference
if 'chat_display' not in st.session_state:
    st.session_state['chat_display'] = []

for interaction in st.session_state['chat_display']:
    if interaction['role'] == 'user':
        st.markdown(f'<div style="border:2px solid coral; padding:10px; margin:5px; border-radius: 15px;">You: {interaction["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="border:2px solid LightBlue; padding:10px; margin:5px; border-radius: 15px;">AI: {interaction["content"]}</div>', unsafe_allow_html=True)


#User input
res_box = st.empty()
user_input = st.text_area("You", placeholder="Ask me a question here...", key="input")


#maybe limit historys size as it is used as input or context tokens
history = [{"role": "system", "content": "You help users with general questions and stuff."}]
history.extend(st.session_state['chat_display'])
history.append({"role": "user", "content": user_input})

# Submit button action
if st.button("Submit"):
    st.markdown("____")

    #create new entry in the firebase database
    ref = db.reference('sessions')
    session_ref = ref.child(session_id)
    # Check if session already exists
    if not session_ref.get():
        # If not, create new session
        session_ref.set({
        'start_time': session_start_time.strftime("%m/%d/%Y, %H:%M:%S"),
        'outputs': []
    })

    # Update chat display with user input
    st.session_state['chat_display'].append({"role": "user", "content": user_input})
    record_output('user', user_input) #call function to record user input in database

    report = []
    for resp in openai.chat.completions.create(model="gpt-3.5-turbo-16k", messages=history, max_tokens=1024, temperature=0.5, stream=True):
        content = resp.choices[0].delta.content
        if content is not None:
            report.append(content)
            current_output = "".join(report).strip()
            res_box.markdown(f'<div style="border:2px solid lightgreen; padding:10px; margin:5px; border-radius: 15px;"><b>Current Output: </b>{current_output}</div>', unsafe_allow_html=True)


    st.session_state['chat_display'].append({"role": "assistant", "content": current_output})
    record_output('assistant', current_output)



        