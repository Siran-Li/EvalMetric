import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account

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

gc = get_gsheets_connection()
sheet = gc.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
worksheet = sheet.worksheet("Data")  # Change if needed
df = pd.DataFrame(worksheet.get_all_records())

df['DataGroup'] = df['DataGroup'].astype(int)

# Compact input form
with st.form("user_input"):
    col1, col2 = st.columns(2)
    with col1:
        data_id = st.selectbox("DataGroup", ['', 1], key="DataGroup")
    with col2:
        name = st.text_input("Your Name")
    submitted = st.form_submit_button("Load Data")

if data_id:
    data_id = int(data_id)  # Ensure data_id is an integer
if submitted and data_id and name:
    # Filter the data based on Data ID
    data_row = df[df['DataGroup'] == data_id]
    if not data_row.empty:
        reference = data_row.iloc[0]['Reference']
        sentence = data_row.iloc[0]['Sentence']
        s1 = data_row.iloc[0]['S1']
        s2 = data_row.iloc[0]['S2']
        s3 = data_row.iloc[0]['S3']

        # Emphasized Reference and Sentence sections
        st.markdown("#### Reference")
        st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px;'>{reference}</div>", 
                   unsafe_allow_html=True)
        
        st.markdown("#### Sentence")
        st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px;'>{sentence}</div>", 
                   unsafe_allow_html=True)

        st.write("---")
        
        # All settings in one box
        with st.container():
            st.markdown("### Task")
            
            st.write("Rank the three given model scores (0-1) based on how accurately they reflect sentence alignment:")
            
            # Get user rankings
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"Score: {s1}")
                s1_rank = st.selectbox("Rank", ['', 1, 2, 3], key="s1_rank")
            with col2:
                st.write(f"Score: {s2}")
                s2_rank = st.selectbox("Rank", ['', 1, 2, 3], key="s2_rank")
            with col3:
                st.write(f"Score: {s3}")
                s3_rank = st.selectbox("Rank", ['', 1, 2, 3], key="s3_rank")

            # Larger slider text
            st.markdown("""
            <style>
                div[data-baseweb="slider"] > div:first-child {
                    font-size: 18px !important;
                }
            </style>
            """, unsafe_allow_html=True)
            
            st.write("Assign a score (0-5) based on how well the generated sentence aligns with the reference:")
            human_score = st.slider(
                "Score",
                0, 5,
                help="0 = No alignment, 5 = Perfect alignment"
            )

            if st.button("Submit Evaluation"):
                try:
                    # Write data using gspread
                    gc = get_gsheets_connection()
                    sheet = gc.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
                    worksheet = sheet.worksheet("Score")
                    
                    # Append new row
                    new_row = [data_id, name, reference, sentence, s1, s2, s3, s1_rank, s2_rank, s3_rank, human_score]
                    worksheet.append_row(new_row)
                    
                    st.success("Response saved successfully!")
                except Exception as e:
                    st.error(f"Error saving response: {str(e)}")
            
            # Validate ranks only when trying to submit
            if 'human_score' in locals():
                if all([s1_rank, s2_rank, s3_rank]) and len(set([s1_rank, s2_rank, s3_rank])) < 3:
                    st.error("Ranks must be unique.")
    else:
        st.error("No data found for the given Data ID.")