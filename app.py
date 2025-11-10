# =====================================================
# ⚡ Electric Vehicle Type Predictor Chatbot (Streamlit)
# =====================================================

import pandas as pd
import re
import streamlit as st

# --- Load dataset ---
@st.cache_data
def load_data():
    df = pd.read_csv("Electric_Vehicle_Population_Data.csv")
    df['Make'] = df['Make'].astype(str).str.lower().str.strip()
    df['Model'] = df['Model'].astype(str).str.lower().str.strip()
    df['Electric Vehicle Type'] = df['Electric Vehicle Type'].astype(str).str.strip()
    df['Electric Range'] = pd.to_numeric(df['Electric Range'], errors='coerce').fillna(0)
    return df

df = load_data()

# --- Utility Functions ---
def normalize_text(text):
    return re.sub(r'\s+', ' ', text.strip().lower())

def find_vehicle(make_model):
    key = normalize_text(make_model)
    match = df[(df['Make'] + ' ' + df['Model']).str.contains(key, case=False, regex=False)]
    return match if not match.empty else None

def predict_vehicle_type(make_model, user_range=None):
    vehicle_data = find_vehicle(make_model)

    if vehicle_data is None:
        return f"❌ Sorry, I couldn’t find '{make_model}' in the dataset. Please try another make and model."

    ev_type = vehicle_data['Electric Vehicle Type'].iloc[0]
    avg_range = vehicle_data['Electric Range'].mean()

    if user_range:
        if abs(user_range - avg_range) > 50:
            return (f"The range you mentioned (**{user_range} miles**) differs from the dataset's average (**{avg_range:.0f} miles**). "
                    f"However, according to records, the **{make_model}** is a **{ev_type}**.")
        else:
            description = (
                "Battery Electric Vehicle (BEV), running solely on electricity."
                if "BEV" in ev_type
                else "Plug-in Hybrid Electric Vehicle (PHEV), combining electric and gasoline power."
            )
            return (f"Based on your provided range (**{user_range} miles**) and the dataset, "
                    f"the **{make_model}** is a **{ev_type}** — {description}")
    else:
        return f"According to the dataset, the **{make_model}** is classified as a **{ev_type}**."


# --- Streamlit Chatbot ---
st.set_page_config(page_title="Electric Vehicle Type Predictor", page_icon="⚡", layout="centered")

st.title("⚡ Electric Vehicle Type Predictor Chatbot")
st.write("Chat with me to find out whether an electric vehicle is a **BEV** or **PHEV**, based on real dataset records.")

# --- Initialize session state ---
if "history" not in st.session_state:
    st.session_state.history = []
if "step" not in st.session_state:
    st.session_state.step = "greet"
if "make_model" not in st.session_state:
    st.session_state.make_model = None

# --- Chat Interface ---
user_input = st.chat_input("Type your message here...")

if user_input:
    user_message = user_input.strip()
    bot_response = ""

    # Step 1: Greeting
    if st.session_state.step == "greet":
        bot_response = "What’s the make and model of the electric vehicle you want me to look up?"
        st.session_state.step = "make_model"

    # Step 2: Make & Model
    elif st.session_state.step == "make_model":
        st.session_state.make_model = user_message
        vehicle_data = find_vehicle(user_message)
        if vehicle_data is None:
            bot_response = "❌ Sorry, I couldn’t find that make and model. Please try another."
        else:
            bot_response = f"✅ Great! Can you tell me the approximate electric range (in miles) for the {user_message}?"
            st.session_state.step = "range"

    # Step 3: Range
    elif st.session_state.step == "range":
        match = re.search(r'\d+', user_message)
        if not match:
            bot_response = "⚠️ Please provide a valid numeric range, like '333 miles'."
        else:
            user_range = int(match.group())
            bot_response = predict_vehicle_type(st.session_state.make_model, user_range)
            bot_response += " Would you like to check another vehicle?"
            st.session_state.step = "followup"

    # Step 4: Follow-up
    elif st.session_state.step == "followup":
        if user_message.lower() in ["no", "n", "exit", "quit"]:
            bot_response = "👋 Goodbye! Have a great day!"
            st.session_state.step = "greet"
        else:
            bot_response = "Alright! 🚘 What’s the make and model of the next vehicle?"
            st.session_state.step = "make_model"

    # Save conversation
    st.session_state.history.append(("You", user_message))
    st.session_state.history.append(("Bot", bot_response))

# --- Display Chat History ---
for sender, msg in st.session_state.history:
    if sender == "You":
        with st.chat_message("user"):
            st.markdown(msg)
    else:
        with st.chat_message("assistant"):
            st.markdown(msg)

# --- Clear Chat Button ---
if st.button("🧹 Clear Chat"):
    st.session_state.history = []
    st.session_state.step = "greet"
    st.session_state.make_model = None
    st.rerun()
