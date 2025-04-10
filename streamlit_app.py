import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account

# ===== CSS STYLING =====

# Using columns with tighter spacing
st.markdown("""
<style>
    .scale-container {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
    }
    .score-number {
        background: #4CAF50;
        color: white;
        border-radius: 50%;
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 12px;
        flex-shrink: 0;
    }
    .tip-box {
        background-color: #fcf7e9;
        padding: 10px 15px;
        border-radius: 8px;
        margin-top: 12px;
        border-left: 4px solid #f3dfa6;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    /* Score Visualization */
    .score-visualization {
        padding: 12px;
        background: #f8f9fa;
        border-radius: 8px;
        margin: 15px 0;
        border: 1px solid #e0e0e0;
    }
    .score-labels {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .score-bar-container {
        background: #e9ecef;
        height: 6px;
        border-radius: 3px;
        margin-bottom: 8px;
        overflow: hidden;
    }
    .score-bar {
        height: 100%;
        transition: width 0.3s ease;
    }
    .score-indicator {
        text-align: center;
        font-size: 0.9em;
    }
    .score-value {
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

score_colors = {
    0: "#cccccc",  # Gray (unchanged)
    1: "#FFA000",  # Darker orange (replaced red)
    2: "#FFC107",  # Amber (previously orange)
    3: "#FFD54F",  # Light amber (previously yellow)
    4: "#8BC34A",  # Light green (unchanged)
    5: "#4CAF50"   # Green (unchanged)
}

score_descriptions = {
    0: "Not Rated", 1: "Contradiction/Irrelevance", 2: "Significant Deviation",
    3: "Partial Match", 4: "Close Match", 5: "Semantic Equivalence"
}

# Score display function
def show_score(current_score):
    
    st.markdown(f"""
    <div class="score-visualization">
        <div class="score-labels">
            <span style="color:{score_colors[0]};">0</span>
            <span style="color:{score_colors[1]};">1</span>
            <span style="color:{score_colors[2]};">2</span>
            <span style="color:{score_colors[3]};">3</span>
            <span style="color:{score_colors[4]};">4</span>
            <span style="color:{score_colors[5]};">5</span>
        </div>
        <div class="score-bar-container">
            <div class="score-bar" style="width:{current_score * 20}%; background:{"#f44336"};"></div>
        </div>
        <div class="score-indicator">
            Selected: <span class="score-value" style="color:{score_colors[current_score]};">{current_score}</span> • {score_descriptions[current_score]}
        </div>
    </div>
    """, unsafe_allow_html=True)



# --- SETUP GOOGLE SHEETS CONNECTION ---
@st.cache_resource(ttl=1200)  # Cache the connection for 20 minutes
def get_gsheets_connection():
    """Authenticate and return a gspread client."""
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return gspread.authorize(credentials)

@st.cache_data(ttl=1200)  # Cache the data for 20 minutes
def load_data(sheetname):
    """Load data from Google Sheets with caching."""
    gc = get_gsheets_connection()
    sheet = gc.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
    worksheet = sheet.worksheet(sheetname)
    return pd.DataFrame(worksheet.get_all_records())


# Initialize session state variables
if 'current_sample' not in st.session_state:
    st.session_state.current_sample = 0
if 'evaluations' not in st.session_state:
    st.session_state.evaluations = {}
if 'loaded_data' not in st.session_state:
    st.session_state.loaded_data = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'data_group' not in st.session_state:
    st.session_state.data_group = None
if 'total_samples' not in st.session_state:
    st.session_state.total_samples = 0


df = load_data("Data")
df_finished = load_data("Finished")
df['datagroup'] = df['datagroup'].astype(int)

# filtered the datagroup that are already finished
if len(df_finished) > 0:
    df_finished['datagroup'] = df_finished['datagroup'].astype(int)
    df = df[~df['datagroup'].isin(df_finished['datagroup'])]


# At the top of your script or in the main display logic
if st.session_state.get('show_thank_you', False):
    st.empty()
    st.balloons()
    
    # Main thank you content
    st.markdown("""
    <div style="text-align: center;">
        <h1>Thank You!</h1>
        <h3>Your contributions are invaluable to our research!</h3>
        <p>All your evaluations have been successfully recorded.</p>
        <p style="margin-bottom: 40px;">We sincerely appreciate your time and effort.</p>
        <p style="font-style: italic; margin-bottom: 30px;">- The HealthNLP Research Team</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Centered button using CSS
    st.markdown("""
    <style>
        .stButton > button {
            margin: 0 auto;
            display: block;
        }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("Start New Evaluation", type="primary"):
        st.session_state.show_thank_you = False
        st.rerun()

# Main evaluation interface
else:
    # --- MAIN APP ---
    st.title("📝 Semantic Match Grading")
    # Data loading form - only shown if no datagroup is selected
    if st.session_state.data_group is None:

        with st.container():
            st.markdown("""
            **Evaluation Instructions**: You will see a **reference sentence** and a **target sentence**.  
            Rate how well their meanings match using this scale:
            """)
            
            # Score 5
            st.markdown("""
            <div class="scale-container">
                <div class="score-number" style="background:#4CAF50;">5</div>
                <div><strong>Semantic Equivalence</strong> - Same meaning, may paraphrase but no contradictions or core omissions</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Score 4
            st.markdown("""
            <div class="scale-container">
                <div class="score-number" style="background:#8BC34A;">4</div>
                <div><strong>Close Match</strong> - Minor differences in non-essential details</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Score 3
            st.markdown("""
            <div class="scale-container">
                <div class="score-number" style="background:#FFD54F;">3</div>
                <div><strong>Partial Match</strong> - <strong>(Please click this only if you really couldn’t decide)</strong></div>
            </div>
            """, unsafe_allow_html=True)
            
            # Score 2
            st.markdown("""
            <div class="scale-container">
                <div class="score-number" style="background:#FFC107;">2</div>
                <div><strong>Significant Deviation</strong> - Changes or omits core meaning</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Score 1
            st.markdown("""
            <div class="scale-container">
                <div class="score-number" style="background:#FFA000;">1</div>
                <div><strong>Contradiction/Irrelevance</strong> - Opposite meaning or completely unrelated</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="tip-box">
                <strong>Tip:</strong> Focus on whether the <strong>core meaning</strong> is preserved, not exact wording.
            </div>
            """, unsafe_allow_html=True)


        # Static Example Section
        st.markdown("#### Example before the Evaluation Task:")
        st.markdown("""
        Before you start, here’s an example to help you understand the evaluation process. 
        """)
        # st.markdown("Here's how the evaluation will look:")
        
        # Example data - static values
        example1 = {
            'reference': "The watermelon seeds pass through your digestive system.",
            'sentence': "You grow watermelons in your stomach.",
            "score": 1
        }

        example2 = {
            'reference': "The watermelon seeds pass through your digestive system.",
            'sentence': "The watermelon seeds will be excreted.",
            "score": 5
        }
        
        st.markdown("##### Example 1:")
        # Display container with improved spacing
        with st.container(border=True):
            # Reference and target Sentence
            st.markdown("**Reference**")
            st.markdown(
                f'<div style="background:#f9f9f9; padding:12px; border-left:4px solid #4e79a7; border-radius:5px; margin-bottom:15px;">'
                f'{example1["reference"]}'
                f'</div>', 
                unsafe_allow_html=True
            )

            st.markdown("**Target Sentence**")
            st.markdown(
                f'<div style="background:#f9f9f9; padding:12px; border-left:4px solid #e15759; border-radius:5px; margin-bottom:20px;">'
                f'{example1["sentence"]}'
                f'</div>', 
                unsafe_allow_html=True
            )

            # --- Task 1: Alignment Score ---
            st.markdown("#### Task: Semantic Match Score (1-5)")
            st.markdown("**How well does the target sentence match the reference?**")
            

            # Score display - replace 'current_score' with your variable
            show_score(example1["score"])
            st.markdown("**Explanation**: The sentences share similar elements (watermelon seeds and stomach) but convey different meanings, leading to a score of 1 (Contradiction/Irrelevance).")
        
        st.markdown("##### Example 2:")
        with st.container(border=True):
            # Reference and target Sentence
            st.markdown("**Reference**")
            st.markdown(
                f'<div style="background:#f9f9f9; padding:12px; border-left:4px solid #4e79a7; border-radius:5px; margin-bottom:15px;">'
                f'{example2["reference"]}'
                f'</div>', 
                unsafe_allow_html=True
            )

            st.markdown("**Target Sentence**")
            st.markdown(
                f'<div style="background:#f9f9f9; padding:12px; border-left:4px solid #e15759; border-radius:5px; margin-bottom:20px;">'
                f'{example2["sentence"]}'
                f'</div>', 
                unsafe_allow_html=True
            )

            # --- Task 1: Alignment Score ---
            st.markdown("#### Task: Semantic Match Score (1-5)")
            st.markdown("**How well does the target sentence match the reference?**")
            

            # Score display - replace 'current_score' with your variable
            show_score(example2["score"])
            st.markdown("**Explanation**: The sentences use different phrasing but preserve identical core meaning about seeds passing through the body, earning a score of 5 (Semantic Equivalence).")
        
        st.markdown("---")  # Separator before the actual form
        
        # Original data loading form
        with st.form("user_input"):
            col1, col2 = st.columns(2)
            with col1:
                data_group = st.selectbox(
                    "Data Group", 
                    [''] + sorted(df['datagroup'].unique().tolist()), 
                    key="datagroup_select"
                )
            with col2:
                name = st.text_input(
                    "Your Name", 
                    value=st.session_state.user_name, 
                    key="name_input"
                )
            submitted = st.form_submit_button("Load Data")

        if submitted and data_group and name:
            data_group = int(data_group)
            st.session_state.user_name = name
            st.session_state.data_group = data_group
            st.session_state.group_samples = df[df['datagroup'] == data_group].reset_index(drop=True)
            st.session_state.total_samples = len(st.session_state.group_samples)
            st.session_state.current_sample = 0 
            st.rerun()

    if st.session_state.data_group is not None and st.session_state.current_sample >= 0:
        # Progress bar
        progress = st.progress((st.session_state.current_sample) / st.session_state.total_samples)
        st.caption(f"Sample {st.session_state.current_sample + 1} of {st.session_state.total_samples}")
        
        st.markdown("#### Score descriptions:")
        # Score 5
        st.markdown("""
        <div class="scale-container">
            <div class="score-number" style="background:#4CAF50;">5</div>
            <div><strong>Semantic Equivalence</strong> - Same meaning, may paraphrase but no contradictions or core omissions</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Score 4
        st.markdown("""
        <div class="scale-container">
            <div class="score-number" style="background:#8BC34A;">4</div>
            <div><strong>Close Match</strong> - Minor differences in non-essential details</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Score 3
        st.markdown("""
        <div class="scale-container">
            <div class="score-number" style="background:#FFD54F;">3</div>
            <div><strong>Partial Match</strong> - Some alignment but unclear <strong>(Please click this only if you really couldn’t decide)</strong></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Score 2
        st.markdown("""
        <div class="scale-container">
            <div class="score-number" style="background:#FFC107;">2</div>
            <div><strong>Significant Deviation</strong> - Changes or omits core meaning</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Score 1
        st.markdown("""
        <div class="scale-container">
            <div class="score-number" style="background:#FFA000;">1</div>
            <div><strong>Contradiction/Irrelevance</strong> - Opposite meaning or completely unrelated</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="tip-box">
            <strong>Tip:</strong> Focus on whether the <strong>core meaning</strong> is preserved, not exact wording.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(" ")

        # Get current sample data
        current_data = st.session_state.group_samples.iloc[st.session_state.current_sample]
        
        # Display evaluation form
        with st.form(f"evaluation_form_{st.session_state.current_sample}"):
            # Reference and target Sentence
            st.markdown("**Reference**")
            st.markdown(
                f'<div style="background:#f9f9f9; padding:12px; border-left:4px solid #4e79a7; border-radius:5px; margin-bottom:15px;">'
                f'{current_data["reference"]}'
                f'</div>', 
                unsafe_allow_html=True
            )

            st.markdown("**Target Sentence**")
            st.markdown(
                f'<div style="background:#f9f9f9; padding:12px; border-left:4px solid #e15759; border-radius:5px; margin-bottom:20px;">'
                f'{current_data["sentence"]}'
                f'</div>', 
                unsafe_allow_html=True
            )

            # --- Task 1: Semantic Match Score ---
            st.markdown("#### Task 1: Semantic Match Score (1-5)")
            st.markdown("**How well does the target sentence match the reference?**")
            
            # Compact score guide in one row
            st.markdown(f"""
            <div class="score-labels">
                <span style="color:{score_colors[0]};">0 Not Rated</span>
                <span style="color:{score_colors[1]};"></span>
                <span style="color:{score_colors[2]};"></span>
                <span style="color:{score_colors[3]};"></span>
                <span style="color:{score_colors[4]};"></span>
                <span style="color:{score_colors[5]};">5 Equivalent</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Load previous evaluation if exists
            current_eval = st.session_state.evaluations.get(st.session_state.current_sample, {})
            
            human_score = st.slider(
                "Score (0-5)",
                0, 5,
                value=current_eval.get('human_score', 0),
                key=f"human_score_{st.session_state.current_sample}",
                label_visibility="collapsed"
            )

                        
            # Navigation buttons - right aligned
            cols = st.columns([3, 1, 1])
            with cols[1]:
                if st.session_state.current_sample > 0:
                    if st.form_submit_button("⏮ Previous"):
                        # Save current evaluation before moving
                        st.session_state.evaluations[st.session_state.current_sample] = {
                            'human_score': human_score
                        }
                        st.session_state.current_sample -= 1
                        st.rerun()
            
            with cols[2]:
                if st.session_state.current_sample < st.session_state.total_samples - 1:
                    if st.form_submit_button("Next ⏭"):
                        # Validate current evaluation
                        if human_score == 0 :
                            st.error("Please provide a score between 1 and 5")
                        else:
                            # Save current evaluation before moving
                            st.session_state.evaluations[st.session_state.current_sample] = {
                                'human_score': human_score
                            }
                            st.session_state.current_sample += 1
                            st.rerun()
    
                # if st.session_state.current_sample > 2:
                else:
                    if st.form_submit_button("Submit All"):
                        # Final validation
                        if human_score == 0:
                            st.error("Please provide a score between 1 and 5")
                        else:
                            # Save final evaluation
                            st.session_state.evaluations[st.session_state.current_sample] = {
                                'human_score': human_score
                            }
                            
                            try:
                                # Write all evaluations to Google Sheets
                                gc = get_gsheets_connection()
                                sheet = gc.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
                                worksheet = sheet.worksheet("Score")
                                
                                # Prepare all rows to append
                                rows_to_add = []
                                for sample_idx, evaluation in st.session_state.evaluations.items():
                                    sample_data = st.session_state.group_samples.iloc[sample_idx]
                                    new_row = [
                                        int(st.session_state.data_group),  # Convert to int
                                        st.session_state.user_name, 
                                        str(sample_data['dataId']),  # Convert to string
                                        sample_data['reference'], 
                                        sample_data['sentence'], 
                                        str(sample_data['label']),  # Convert to string
                                        sample_data['m1'], 
                                        float(sample_data['s1']),  # Convert to float
                                        sample_data['m2'], 
                                        float(sample_data['s2']),  # Convert to float
                                        sample_data['m3'], 
                                        float(sample_data['s3']),  # Convert to float
                                        int(evaluation['human_score'])  # Convert to int
                                    ]
                                    rows_to_add.append(new_row)
                                
                                # Append all rows at once
                                if rows_to_add:
                                    worksheet.append_rows(rows_to_add)

                                gc = get_gsheets_connection()
                                sheet = gc.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
                                worksheet = sheet.worksheet("Finished")
                                worksheet.append_row([int(st.session_state.data_group), st.session_state.user_name])
                                
                                # Set a flag to show thank you page
                                st.session_state.show_thank_you = True
                                
                                # Reset session state
                                st.session_state.current_sample = 0
                                st.session_state.evaluations = {}
                                st.session_state.data_group = None
                                st.session_state.group_samples = None
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Error saving evaluations: {str(e)}")

