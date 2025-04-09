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
df_finished['datagroup'] = df_finished['datagroup'].astype(int)
# filtered the datagroup that are already finished
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
    st.title("📊 Sentence Comparison")
    # Data loading form - only shown if no datagroup is selected
    if st.session_state.data_group is None:

        st.markdown("""
        <div style="background:#f0f8ff; padding:15px; border-radius:10px; margin-bottom:20px;">
            <p><strong>Instructions:</strong> You will receive a <strong>reference</strong> and a <strong>target sentence</strong>. Your goal is to assess the similarity between the two sentences by completing the following tasks:</p>
            <ol>
                <li><strong>Task 1:</strong> Evaluate the alignment between the <strong>reference</strong> and <strong>target sentence</strong>. Assign a score from 0 to 5 based on how well the two sentences align:
                    <ul>
                        <li> 0-1 Weak alignment</li> 
                        <li> 2-3 Partial alignment</li> 
                        <li> 4-5 Strong alignment</li>
                    </ul>
                </li>
                <li><strong>Task 2:</strong> You will be presented with three metric scores that assess the alignment between the sentences. Your task is to rank these three scores based on how accurately they reflect the similarity between the <strong>reference</strong> and <strong>target sentence</strong>:
                    <ul>
                        <li>1 => Best (most accurate)</li>
                        <li>2 => Moderate accuracy</li>
                        <li>3 => Worst (least accurate)</li>
                    </ul>
                </li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

        # Static Example Section
        st.markdown("#### Example before the Evaluation Task:")
        st.markdown("""
        Before you start, here’s an example to help you understand the evaluation process. 
        """)
        # st.markdown("Here's how the evaluation will look:")
        
        # Example data - static values
        example_data = {
            'reference': "The watermelon seeds pass through your digestive system.",
            'sentence': "You grow watermelons in your stomach.",
            's1': 0.22,
            's2': 0.57,
            's3': 0.63
        }
        
        # Display container with improved spacing
        with st.container(border=True):
            # Reference and target Sentence
            st.markdown("**Reference**")
            st.markdown(
                f'<div style="background:#f9f9f9; padding:12px; border-left:4px solid #4e79a7; border-radius:5px; margin-bottom:15px;">'
                f'{example_data["reference"]}'
                f'</div>', 
                unsafe_allow_html=True
            )

            st.markdown("**Target Sentence**")
            st.markdown(
                f'<div style="background:#f9f9f9; padding:12px; border-left:4px solid #e15759; border-radius:5px; margin-bottom:20px;">'
                f'{example_data["sentence"]}'
                f'</div>', 
                unsafe_allow_html=True
            )

            # --- Task 1: Alignment Score ---
            st.markdown("#### Task 1: Alignment Score (0-5)")
            st.markdown("**How well does the target sentence match the reference?**")
            
            # Static slider with score 1
            st.markdown("""
            <div style="padding:10px; background:#f5f5f5; border-radius:5px; margin-bottom:20px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="font-size: 0.8em;">0-1: Weak</span>
                    <span style="font-size: 0.8em;">2-3: Partial</span>
                    <span style="font-size: 0.8em;">4-5: Strong</span>
                </div>
                <div style="background:#ddd; height:4px; border-radius:2px; margin-bottom:5px;">
                    <div style="background:#4e79a7; width:20%; height:4px;"></div>
                </div>
                <div style="text-align:center;">Selected: <strong>1</strong></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("**Explanation**: The sentences share similar elements (watermelon seeds and stomach) but convey different meanings, leading to a score of 1 (weak alignment).")
           
            # --- Task 2: Metric Ranking ---
            st.markdown("#### Task 2: Metric Ranking (1=Best, 3=Worst)")
            st.markdown("**Which metric best reflects alignment between the reference and target sentence?**")
            st.markdown("*Metrics are scored on a 0-1 scale where higher values indicate better alignment*")


            # Metrics with improved bottom spacing
            cols = st.columns(3)
            metrics = {
                'A': {'score': example_data['s1'], 'rank': 1},
                'B': {'score': example_data['s2'], 'rank': 2}, 
                'C': {'score': example_data['s3'], 'rank': 3}
            }
            
            for i, (metric, data) in enumerate(metrics.items()):
                with cols[i]:
                    # Metric score display
                    st.markdown(
                        f'<div style="background:#f0f0f0; padding:10px; border-radius:5px; text-align:center; margin-bottom:10px;">'
                        f'<p style="margin:0; font-weight:bold;">Metric {metric}</p>'
                        f'<p style="margin:0; font-size:24px; color:{"#e15759" if data["score"] >= 0.7 else "#4e79a7" if data["score"] < 0.4 else "#f28e2b"};">{data["score"]:.2f}</p>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    
                    # Rank display with extra bottom margin
                    st.markdown(
                        f'<div style="background:#f8f8f8; padding:8px; border-radius:5px; text-align:center; margin-bottom:15px;">'  # Increased margin-bottom
                        f'<p style="margin:0;">Rank: <strong>{data["rank"]}</strong></p>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
        
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

            # --- Task 1: Alignment Score ---
            st.markdown("#### Task 1: Alignment Score (0-5)")
            st.markdown("**How well does the target sentence match the reference?**")
            
            # Compact score guide in one row
            st.markdown("""
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-size: 0.8em;">0-1: Weak</span>
                <span style="font-size: 0.8em;">2-3: Partial</span>
                <span style="font-size: 0.8em;">4-5: Strong</span>
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

            # --- Task 2: Metric Ranking ---
            st.markdown("#### Task 2: Metric Ranking (1=Best, 3=Worst)")
            st.markdown("**Which metric best reflects alignment between the reference and target sentence?**")
            st.markdown("*Metrics are scored on a 0-1 scale where higher values indicate better alignment*")


            # Score cards in columns
            col1, col2, col3 = st.columns(3)
            scores = {
                'A': float(current_data['s1']),  # Convert to float to avoid int64
                'B': float(current_data['s2']),
                'C': float(current_data['s3'])
            }

            ranks = {}
            for metric, score in scores.items():
                with col1 if metric == 'A' else col2 if metric == 'B' else col3:
                    # Score card with color coding
                    st.markdown(
                        f'<div style="background:#f0f0f0; padding:10px; border-radius:5px; text-align:center; margin-bottom:10px;">'
                        f'<p style="margin:0; font-weight:bold;">Metric {metric}</p>'
                        f'<p style="margin:0; font-size:24px; color:{"#e15759" if score >= 0.7 else "#4e79a7" if score < 0.4 else "#f28e2b"};">{score:.2f}</p>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    # Rank dropdown
                    rank = st.selectbox(
                        f"Rank Metric {metric}",
                        ['', 1, 2, 3],
                        key=f"{metric}_rank_{st.session_state.current_sample}",
                        index=['', 1, 2, 3].index(current_eval.get(f"{metric}_rank", '')),
                        label_visibility="collapsed"
                    )
                    ranks[metric] = rank

            # Navigation buttons - right aligned
            cols = st.columns([3, 1, 1])
            with cols[1]:
                if st.session_state.current_sample > 0:
                    if st.form_submit_button("⏮ Previous"):
                        # Save current evaluation before moving
                        st.session_state.evaluations[st.session_state.current_sample] = {
                            'human_score': human_score,
                            'A_rank': ranks['A'],
                            'B_rank': ranks['B'],
                            'C_rank': ranks['C']
                        }
                        st.session_state.current_sample -= 1
                        st.rerun()
            
            with cols[2]:
                if st.session_state.current_sample < st.session_state.total_samples - 1:
                    if st.form_submit_button("Next ⏭"):
                        # Validate current evaluation
                        if not all([ranks['A'], ranks['B'], ranks['C']]):
                            st.error("Please rank all metrics")
                        else:
                            # Save current evaluation before moving
                            st.session_state.evaluations[st.session_state.current_sample] = {
                                'human_score': human_score,
                                'A_rank': ranks['A'],
                                'B_rank': ranks['B'],
                                'C_rank': ranks['C']
                            }
                            st.session_state.current_sample += 1
                            st.rerun()
    
                # if st.session_state.current_sample > 2:
                else:
                    if st.form_submit_button("Submit All"):
                        # Final validation
                        if not all([ranks['A'], ranks['B'], ranks['C']]):
                            st.error("Please rank all metrics")
                        else:
                            # Save final evaluation
                            st.session_state.evaluations[st.session_state.current_sample] = {
                                'human_score': human_score,
                                'A_rank': ranks['A'],
                                'B_rank': ranks['B'],
                                'C_rank': ranks['C']
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
                                        int(evaluation['A_rank']),  # Convert to int
                                        sample_data['m2'], 
                                        float(sample_data['s2']),  # Convert to float
                                        int(evaluation['B_rank']),  # Convert to int
                                        sample_data['m3'], 
                                        float(sample_data['s3']),  # Convert to float
                                        int(evaluation['C_rank']),  # Convert to int
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

