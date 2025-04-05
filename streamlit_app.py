import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from streamlit_gsheets import GSheetsConnection

# --- SETUP GOOGLE SHEETS CONNECTION ---
def get_gsheets_connection():
    """Authenticate and return a gspread client."""
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return gspread.authorize(credentials)

# --- MAIN APP ---
st.title("Sentence Comparison")

# Read data using streamlit_gsheets (read-only)
# conn = st.connection("gsheets", type=GSheetsConnection)
# df = conn.read()

gc = get_gsheets_connection()
sheet = gc.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
worksheet = sheet.worksheet("Data")  # Change if needed
df = pd.DataFrame(worksheet.get_all_records())


# User inputs
data_id = st.text_input("Input Data ID:")
if data_id:
    try:
        data_id = int(data_id)
    except ValueError:
        st.error("Please enter a valid integer ID.")
name = st.text_input("Input Name:")

df['DataID'] = df['DataID'].astype(int)
if data_id and name:
    # Filter the data based on Data ID
    data_row = df[df['DataID'] == data_id]
    if not data_row.empty:
        reference = data_row.iloc[0]['Reference']
        sentence = data_row.iloc[0]['Sentence']
        s1 = data_row.iloc[0]['S1']
        s2 = data_row.iloc[0]['S2']
        s3 = data_row.iloc[0]['S3']

        st.write(f"Reference: {reference}")
        st.write(f"Sentence: {sentence}")

        # Get user rankings
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"S1: {s1}")
            s1_rank = st.selectbox("S1 Rank", ['', 1, 2, 3], key="s1_rank")
        with col2:
            st.write(f"S2: {s2}")
            s2_rank = st.selectbox("S2 Rank", ['', 1, 2, 3], key="s2_rank")
        with col3:
            st.write(f"S3: {s3}")
            s3_rank = st.selectbox("S3 Rank", ['', 1, 2, 3], key="s3_rank")

        # Validate ranks
        if all([s1_rank, s2_rank, s3_rank]) and len(set([s1_rank, s2_rank, s3_rank])) < 3:
            st.error("Ranks must be unique.")
        else:
            human_score = st.slider("Give a human score (0-5) for the alignment:", 0, 5)

            if st.button("Submit"):
                try:
                    # Write data using gspread
                    gc = get_gsheets_connection()
                    sheet = gc.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
                    worksheet = sheet.worksheet("Score")  # Change if needed
                    
                    # Append new row
                    new_row = [data_id, name, reference, sentence, s1, s2, s3, s1_rank, s2_rank, s3_rank, human_score]
                    worksheet.append_row(new_row)
                    
                    st.success("Response saved successfully!")
                except Exception as e:
                    st.error(f"Error saving response: {str(e)}")
    else:
        st.error("No data found for the given Data ID.")