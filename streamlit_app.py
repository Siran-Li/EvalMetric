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

    # Title and Instructions
    st.markdown("## 📊 Evaluation Tasks")
    st.markdown("""
    <div style="background:#f0f8ff; padding:15px; border-radius:10px; margin-bottom:20px;">
        <p><strong>Instructions:</strong></p>
        <ol>
            <li><strong>Task 1:</strong> Score alignment (0-5) between the sentence and reference.</li>
            <li><strong>Task 2:</strong> Rank the 3 metric scores (1=best, 3=worst) by alignment accuracy.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    # Evaluation Form
    with st.form("evaluation_form"):
        # Reference and Sentence (improved styling)
        st.markdown("#### 📝 Reference")
        st.markdown(
            f'<div style="background:#f9f9f9; padding:12px; border-left:4px solid #4e79a7; border-radius:5px; margin-bottom:15px;">'
            f'{data["reference"]}'
            f'</div>', 
            unsafe_allow_html=True
        )

        st.markdown("#### 💬 Generated Sentence")
        st.markdown(
            f'<div style="background:#f9f9f9; padding:12px; border-left:4px solid #e15759; border-radius:5px; margin-bottom:20px;">'
            f'{data["sentence"]}'
            f'</div>', 
            unsafe_allow_html=True
        )

        # --- Task 1: Alignment Score ---
        st.markdown("### Task 1: Alignment Score (0-5)")
        st.markdown("**How well does the sentence match the reference?**")

        # Slider with scoring guide
        st.markdown("**Score Guide:**")
        st.markdown("""
        - **0-1:** No/weak alignment  
        - **2-3:** Partial alignment  
        - **4-5:** Strong alignment  
        """)

        human_score = st.slider(
            "**Your Score (0-5):**",
            0, 5,
            value=st.session_state.human_score,
            key="human_score_slider"
        )
        st.session_state.human_score = human_score

        # Divider
        st.markdown("---")

        # --- Task 2: Metric Ranking ---
        st.markdown("### Task 2: Rank Metric Scores (1=Best, 3=Worst)")
        st.markdown("**Which metric best reflects alignment between the reference and sentence?**")

        # Score cards in columns (improved layout)
        col1, col2, col3 = st.columns(3)
        scores = {
            's1': data['s1'],
            's2': data['s2'],
            's3': data['s3']
        }

        for i, (key, score) in enumerate(scores.items(), 1):
            with eval(f"col{i}"):
                # Score card with color coding
                st.markdown(
                    f'<div style="background:#f0f0f0; padding:10px; border-radius:5px; text-align:center; margin-bottom:10px;">'
                    f'<p style="margin:0; font-weight:bold;">Metric {i}</p>'
                    f'<p style="margin:0; font-size:24px; color:{"#e15759" if score >= 0.7 else "#4e79a7" if score < 0.4 else "#f28e2b"};">{score:.2f}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                # Rank dropdown
                rank = st.selectbox(
                    f"Rank Metric {i}",
                    ['', 1, 2, 3],
                    key=f"{key}_rank",
                    index=['', 1, 2, 3].index(st.session_state.ranks[key]))
                st.session_state.ranks[key] = rank

        # Validate that ranks are unique
        # if all([st.session_state.ranks['s1'], st.session_state.ranks['s2'], st.session_state.ranks['s3']]):
            # if len({st.session_state.ranks['s1'], st.session_state.ranks['s2'], st.session_state.ranks['s3']}) < 3:
                # st.error("Ranks must be unique.")
        
        submitted_eval = st.form_submit_button("Submit Evaluation")
        
        if submitted_eval:
            # Final validation before submission
            if not all([st.session_state.ranks['s1'], st.session_state.ranks['s2'], st.session_state.ranks['s3']]):
                st.error("Please rank all scores")
            # elif len({st.session_state.ranks['s1'], st.session_state.ranks['s2'], st.session_state.ranks['s3']}) < 3:
            #     st.error("Ranks must be unique")
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