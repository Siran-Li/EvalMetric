import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account

def score_card(title, score):
    return f"""
    <div style='
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    '>
        <div style='font-size:14px; color:#666;'>{title}</div>
        <div style='font-size:24px; font-weight:bold; color:#2c3e50;'>
            {score:.4f}
        </div>
    </div>
    """


# --- SETUP GOOGLE SHEETS CONNECTION ---
@st.cache_resource(ttl=600)  # Cache the connection for 10 minutes
def get_gsheets_connection():
    """Authenticate and return a gspread client."""
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return gspread.authorize(credentials)

@st.cache_data(ttl=1200)  # Cache the data for 10 minutes
def load_data():
    """Load data from Google Sheets with caching."""
    gc = get_gsheets_connection()
    sheet = gc.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
    worksheet = sheet.worksheet("Data")
    return pd.DataFrame(worksheet.get_all_records())

# --- MAIN APP ---
st.title("Sentence Comparison")

# Initialize session state
if 'loaded_data' not in st.session_state:
    st.session_state.loaded_data = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'ranks' not in st.session_state:
    st.session_state.ranks = {'s1': '', 's2': '', 's3': ''}
if 'human_score' not in st.session_state:
    st.session_state.human_score = 0

# Load data with caching
df = load_data()
df['DataGroup'] = df['DataGroup'].astype(int)

# Data loading form
with st.form("user_input"):
    col1, col2 = st.columns(2)
    with col1:
        data_id = st.selectbox("Data Group", [''] + sorted(df['DataGroup'].unique().tolist()), key="DataGroup")
    with col2:
        name = st.text_input("Your Name", value=st.session_state.user_name, key="name_input")
    submitted = st.form_submit_button("Load Data")

if submitted and data_id and name:
    data_id = int(data_id)
    st.session_state.user_name = name
    data_row = df[df['DataGroup'] == data_id]
    if not data_row.empty:
        st.session_state.loaded_data = {
            'data_id': data_id,
            'reference': data_row.iloc[0]['Reference'],
            'sentence': data_row.iloc[0]['Sentence'],
            's1': data_row.iloc[0]['S1'],
            's2': data_row.iloc[0]['S2'],
            's3': data_row.iloc[0]['S3']
        }
        # Reset ranks when loading new data
        st.session_state.ranks = {'s1': '', 's2': '', 's3': ''}
        st.session_state.human_score = 0
    else:
        st.error("No data found for the given Data ID.")

# Display loaded data and evaluation form
if st.session_state.loaded_data:
    data = st.session_state.loaded_data
    
    st.write("---")

    st.markdown("## Test 1")
    # Evaluation form
    with st.form("evaluation_form"):

        # Emphasized Reference and Sentence sections
        # st.markdown("#### Reference")
        # st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px;'>{data['reference']}</div>", 
        #         unsafe_allow_html=True)
        
        # st.markdown("#### Sentence")
        # st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px;'>{data['sentence']}</div>", 
        #         unsafe_allow_html=True)
        # Reference Section
        st.markdown("**📝 Reference:**")
        st.markdown(f'<div style="background:#f5f5f5; padding:10px; border-radius:5px;">{data["reference"]}</div>', unsafe_allow_html=True)
        st.markdown("**💬 Sentence:**")
        st.markdown(f'<div style="background:#f5f5f5; padding:10px; border-radius:5px;">{data["sentence"]}</div>', unsafe_allow_html=True)
        
        
        st.markdown("### Task")
        st.write("Rank the three given model scores (0-1) based on how accurately they reflect sentence alignment:")
        
        # Get user rankings
        col1, col2, col3 = st.columns(3)
        with col1:
            # st.markdown(f"**Score:** {data['s1']}")
            # st.markdown(f'<span class="pulse-score">Score: {data.s1}</span>', unsafe_allow_html=True)
            # st.write(f"Score: {data['s1']}")
            st.markdown(score_card("SCORE", data['s1']), unsafe_allow_html=True)
            s1_rank = st.selectbox(
                "Rank", ['', 1, 2, 3], 
                key="s1_rank",
                index=['', 1, 2, 3].index(st.session_state.ranks['s1'])
            )
            st.session_state.ranks['s1'] = s1_rank
            
        with col2:
            # st.markdown(f"**Score:** {data['s2']}")
            st.markdown(score_card("SCORE", data['s2']), unsafe_allow_html=True)
            s2_rank = st.selectbox(
                "Rank", ['', 1, 2, 3], 
                key="s2_rank",
                index=['', 1, 2, 3].index(st.session_state.ranks['s2'])
            )
            st.session_state.ranks['s2'] = s2_rank
            
        with col3:
            # st.markdown(f"**Score:** {data['s3']}")
            # st.markdown(f'<span class="pulse-score">Score: {data.s3}</span>', unsafe_allow_html=True)
            st.markdown(score_card("SCORE", data['s3']), unsafe_allow_html=True)
            s3_rank = st.selectbox(
                "Rank", ['', 1, 2, 3], 
                key="s3_rank",
                index=['', 1, 2, 3].index(st.session_state.ranks['s3'])
            )
            st.session_state.ranks['s3'] = s3_rank

        # Validate that ranks are unique
        if all([st.session_state.ranks['s1'], st.session_state.ranks['s2'], st.session_state.ranks['s3']]):
            if len({st.session_state.ranks['s1'], st.session_state.ranks['s2'], st.session_state.ranks['s3']}) < 3:
                st.error("Ranks must be unique.")

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
            value=st.session_state.human_score,
            key="human_score_slider"
        )
        st.session_state.human_score = human_score

        submitted_eval = st.form_submit_button("Submit Evaluation")
        
        if submitted_eval:
            # Final validation before submission
            if not all([st.session_state.ranks['s1'], st.session_state.ranks['s2'], st.session_state.ranks['s3']]):
                st.error("Please rank all scores")
            elif len({st.session_state.ranks['s1'], st.session_state.ranks['s2'], st.session_state.ranks['s3']}) < 3:
                st.error("Ranks must be unique")
            else:
                try:
                    # Write data using gspread
                    gc = get_gsheets_connection()
                    sheet = gc.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
                    worksheet = sheet.worksheet("Score")
                    
                    # Append new row
                    new_row = [
                        data['data_id'], 
                        st.session_state.user_name, 
                        data['reference'], 
                        data['sentence'], 
                        data['s1'], data['s2'], data['s3'], 
                        st.session_state.ranks['s1'], 
                        st.session_state.ranks['s2'], 
                        st.session_state.ranks['s3'], 
                        st.session_state.human_score
                    ]
                    worksheet.append_row(new_row)
                    
                    st.success("Response saved successfully!")
                    # Optionally clear selections after successful submission
                    st.session_state.ranks = {'s1': '', 's2': '', 's3': ''}
                    st.session_state.human_score = 0
                except Exception as e:
                    st.error(f"Error saving response: {str(e)}")