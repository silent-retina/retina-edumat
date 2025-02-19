import streamlit as st
import os
import time
import pandas as pd
from datetime import datetime
import json

try:
    import google.generativeai as genai
except ImportError:
    st.error("Installing required package...")
    os.system("pip install google-generativeai")
    import google.generativeai as genai

# Initialize session state for storing results
if 'evaluation_results' not in st.session_state:
    st.session_state.evaluation_results = []
if 'system_metrics' not in st.session_state:
    st.session_state.system_metrics = []

class SystemEvaluator:
    def __init__(self):
        self.start_time = time.time()
        
    def evaluate_generation(self, content, patient_data):
        metrics = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'generation_time': time.time() - self.start_time,
            'content_length': len(content),
            'language': patient_data['language'],
            'has_english': 'English' in content,
            'error_occurred': False
        }
        return metrics

# Configure Google API
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("GOOGLE_API_KEY not found in secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash-exp')

def generate_content(patient_data, clinical_data):
    prompt = f"""
    Create a colorful, engaging patient education material with emojis and formatting. Use the following patient information:
    
    Patient Details:
    - Age: {patient_data['age']}
    - Preferred Language: {patient_data['language']}
    - Education Level: {patient_data['education']}
    
    Clinical Information:
    - Diagnosis: {clinical_data['diagnosis']}
    - Visual Acuity RE: {clinical_data['va_re']}
    - Visual Acuity LE: {clinical_data['va_le']}
    - OCT Findings: {clinical_data['oct_findings']}
    
    Include these sections: {', '.join(clinical_data['sections'])}
    
    Make the content patient-friendly, using simple language. Add emojis and color indicators using markdown.
    Use different colors for different sections (using markdown).
    Include a summary at the end.
    
    If the language selected is not English, provide content in both English and the selected language.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating content: {str(e)}"

def save_evaluation_results():
    # Convert results to DataFrame
    df_evaluations = pd.DataFrame(st.session_state.evaluation_results)
    df_metrics = pd.DataFrame(st.session_state.system_metrics)
    
    # Save to CSV files
    df_evaluations.to_csv('evaluation_results.csv', index=False)
    df_metrics.to_csv('system_metrics.csv', index=False)
    
    return df_evaluations, df_metrics

def main():
    st.set_page_config(page_title="Retina Patient Education Generator", page_icon="👁️", layout="wide")
    
    # Add tabs for Generator and Evaluator
    tab1, tab2 = st.tabs(["Generator", "Evaluator"])
    
    with tab1:
        st.title("👁️ Retina Patient Education Generator")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Patient Demographics")
            patient_data = {
                'age': st.number_input("Patient Age", 1, 100, 50),
                'language': st.selectbox(
                    "Preferred Language",
                    ["English", "Hindi", "Punjabi", "Odiya", "Marathi", "Bengali", "Korean", "Chinese", "Japanese"]
                ),
                'education': st.selectbox(
                    "Education Level",
                    ["Primary (upto grade 5)", "Secondary (upto High School)", "Tertiary (> High School)"]
                )
            }
        
        with col2:
            st.subheader("Clinical Information")
            clinical_data = {
                'diagnosis': st.selectbox(
                    "Diagnosis",
                    [
                        "Diabetic Retinopathy",
                        "Age-related Macular Degeneration",
                        "Retinal Detachment",
                        "Central Serous Chorio-retinopathy",
                        "Diabetic Macular Edema",
                        "Retinal Vein Occlusion"
                    ]
                ),
                'va_re': st.text_input("Visual Acuity (Right Eye)", "6/6"),
                'va_le': st.text_input("Visual Acuity (Left Eye)", "6/6"),
                'oct_findings': st.text_area("OCT Findings", "")
            }
        
        st.subheader("Content Sections")
        clinical_data['sections'] = st.multiselect(
            "Select sections to include:",
            [
                "Disease Overview",
                "Treatment Options",
                "Lifestyle Modifications",
                "Follow-up Care",
                "Emergency Signs",
                "Dietary Recommendations",
                "Visual Aids and Rehabilitation"
            ],
            default=["Disease Overview", "Treatment Options"]
        )
        
        if st.button("Generate Education Material", type="primary"):
            evaluator = SystemEvaluator()
            
            with st.spinner("Generating education material..."):
                content = generate_content(patient_data, clinical_data)
                metrics = evaluator.evaluate_generation(content, patient_data)
                
                # Store metrics
                st.session_state.system_metrics.append(metrics)
                
                st.markdown("### Generated Education Material")
                st.markdown(content)
                
                st.download_button(
                    label="Download Material",
                    data=content,
                    file_name=f"patient_education_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
    
    with tab2:
        st.title("Content Evaluator Feedback Form")
        
        evaluator_level = st.selectbox(
            "Select Reviewer ID [Consultant...]",
            ["001", "002", "003", "004", "005"]
        )
        
        st.subheader("Content Evaluation")
        scores = {}
        for metric in ["Medical Accuracy", "Language Clarity", "Completeness", 
                      "Cultural Appropriateness", "Formatting Quality"]:
            scores[metric] = st.slider(
                f"{metric} (1-5)",
                1, 5, 3,
                help=f"Rate the {metric.lower()} of the content"
            )
        
        st.subheader("Detailed Feedback")
        strengths = st.text_area("What are the main strengths of the generated content?")
        weaknesses = st.text_area("What areas need improvement?")
        suggestions = st.text_area("Any specific suggestions for improvement?")
        
        would_use = st.radio(
            "Would you use this output in your practice?",
            ["Definitely", "Probably", "Maybe", "Probably Not", "Definitely Not"]
        )
        
        if st.button("Submit Evaluation"):
            evaluation = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'evaluator_level': evaluator_level,
                'scores': scores,
                'feedback': {
                    'strengths': strengths,
                    'weaknesses': weaknesses,
                    'suggestions': suggestions
                },
                'would_use': would_use
            }
            
            st.session_state.evaluation_results.append(evaluation)
            st.success("Evaluation submitted successfully!")
            
        # Add download buttons for results
        if st.button("Download All Results"):
            df_evaluations, df_metrics = save_evaluation_results()
            
            st.download_button(
                label="Download Evaluation Results",
                data=df_evaluations.to_csv().encode('utf-8'),
                file_name="evaluation_results.csv",
                mime="text/csv"
            )
            
            st.download_button(
                label="Download System Metrics",
                data=df_metrics.to_csv().encode('utf-8'),
                file_name="system_metrics.csv",
                mime="text/csv"
            )
            
        # Display current results
        if st.session_state.evaluation_results:
            st.subheader("Current Evaluation Results")
            st.write(pd.DataFrame(st.session_state.evaluation_results))

if __name__ == "__main__":
    main()
