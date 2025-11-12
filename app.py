import streamlit as st
import pandas as pd
import re
import zipfile
import io
import os

# --- Load Dataset Automatically ---
zip_path = "Electric_Vehicle_Population_Data.zip"

if os.path.exists(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
        if not csv_files:
            st.error("❌ No CSV file found inside the ZIP.")
            st.stop()

        with zip_ref.open(csv_files[0]) as file:
            df = pd.read_csv(file)

    df['Make'] = df['Make'].astype(str).str.lower().str.strip()
    df['Model'] = df['Model'].astype(str).str.lower().str.strip()
    df['Electric Vehicle Type'] = df['Electric Vehicle Type'].astype(str).str.strip()
    df['Electric Range'] = pd.to_numeric(df['Electric Range'], errors='coerce').fillna(0)

    st.success(f"✅ Dataset loaded successfully! File: `{csv_files[0]}` | Shape: {df.shape}")

else:
    st.error("❌ ZIP file not found. Please ensure 'Electric_Vehicle_Population_Data.zip' is in the same directory as this script.")
    st.stop()


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
            return (f"⚠️ The range you mentioned ({user_range} miles) differs from the dataset's average ({avg_range:.0f} miles). "
                    f"However, according to records, the {make_model} is a **{ev_type}**.")
        else:
            description = "Battery Electric Vehicle (BEV) — runs solely on electricity." if "BEV" in ev_type else \
                          "Plug-in Hybrid Electric Vehicle (PHEV) — combines electric and gasoline power."
            return (f"🔋 Based on your provided range ({user_range} miles) and dataset info, "
                    f"the {make_model} is a **{ev_type}** — {description}")
    else:
        return f"According to the dataset, the {make_model} is classified as a **{ev_type}**."


# --- Streamlit Chat UI ---
st.title("⚡ Electric Vehicle Type Predictor Chatbot")
st.markdown("Chat with me to find out whether an electric vehicle is a **BEV** or **PHEV**, based on real dataset records.")

if "step" not in st.session_state:
    st.session_state.step = "greet"
if "make_model" not in st.session_state:
    st.session_state.make_model = None
if "history" not in st.session_state:
    st.session_state.history = [
        {"user": None, "bot": "Hi there! ⚡ I'm your EV Type Assistant. I can help you determine whether an electric vehicle is a BEV or PHEV."}
    ]

def chatbot_response(message):
    step = st.session_state.step

    if step == "greet":
        st.session_state.step = "make_model"
        return "What’s the make and model of the electric vehicle you want me to look up?"

    elif step == "make_model":
        st.session_state.make_model = message
        vehicle_data = find_vehicle(message)
        if vehicle_data is None:
            return "Sorry, I couldn’t find that make and model in the dataset. Please try another."
        st.session_state.step = "range"
        return f"Great! Can you tell me the approximate electric range (in miles) for the {message}?"

    elif step == "range":
        match = re.search(r'\d+', message)
        if not match:
            return "Please provide a valid numeric range, like '333 miles'."
        user_range = int(match.group())
        response = predict_vehicle_type(st.session_state.make_model, user_range)
        st.session_state.step = "followup"
        return response + " Would you like to check another vehicle?"

    elif step == "followup":
        if message.lower() in ["no", "n", "exit", "quit"]:
            st.session_state.step = "greet"
            return "Goodbye! 👋"
        else:
            st.session_state.step = "make_model"
            st.session_state.make_model = None
            return "Alright! What is the make and model of the next vehicle?"


for chat in st.session_state.history:
    if chat["user"]:
        st.chat_message("user").write(chat["user"])
    st.chat_message("assistant").write(chat["bot"])

user_message = st.chat_input("Type your message...")

if user_message:
    response = chatbot_response(user_message)
    st.session_state.history.append({"user": user_message, "bot": response})
    st.rerun()
