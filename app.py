import streamlit as st
import os
from google.cloud import modelarmor_v1
from google.api_core.client_options import ClientOptions
from huggingface_hub import InferenceClient
# Add this import to safely convert Google responses to JSON
from google.protobuf.json_format import MessageToDict

# --- CONFIGURATION (Same as before) ---
PROJECT_ID = "your gcp project id"  # Updated with your project ID
LOCATION = "us-central1"
TEMPLATE_ID = "put model armor template "        # Updated with your template ID
HF_TOKEN = "put the hf token"
HF_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

def call_model_armor(user_text):
    api_endpoint = f"modelarmor.{LOCATION}.rep.googleapis.com"
    client_options = ClientOptions(api_endpoint=api_endpoint)
    client = modelarmor_v1.ModelArmorClient(transport="rest", client_options=client_options)
    
    name = f"projects/{PROJECT_ID}/locations/{LOCATION}/templates/{TEMPLATE_ID}"
    request = modelarmor_v1.SanitizeUserPromptRequest(
        name=name,
        user_prompt_data=modelarmor_v1.DataItem(text=user_text)
    )
    return client.sanitize_user_prompt(request=request)

def call_third_party_llm(clean_text):
    client = InferenceClient(token=HF_TOKEN)
    messages = [{"role": "user", "content": clean_text}]
    response = client.chat_completion(model=HF_MODEL_ID, messages=messages, max_tokens=500)
    return response.choices[0].message.content

# --- STREAMLIT GUI ---
st.set_page_config(page_title="AI Security Guardrails", layout="wide")
st.title("🛡️ Model Armor + Open LLM Demo")

user_input = st.text_area("Enter your prompt:", height=150)
submit_btn = st.button("Submit Prompt")

if submit_btn and user_input:
    with st.status("Processing Request...", expanded=True) as status:
        st.write("🔍 Scanning prompt with Model Armor...")
        
        try:
            armor_response = call_model_armor(user_input)
            sanitization_result = armor_response.sanitization_result
            match_state = sanitization_result.filter_match_state
            
            # --- FIX: Convert the Protobuf response to a regular Python Dictionary ---
            # This handles the "filter_results" field correctly for display
            debug_info = MessageToDict(armor_response._pb)
            
            # Display readable verdict
            st.json({
                "verdict": str(match_state),
                # The corrected field is 'filter_results' which is now inside our dict
                "details": debug_info.get("sanitizationResult", {}).get("filterResults", {})
            })

            # --- BUSINESS LOGIC ---
            # Check for MATCH_FOUND (Value 2 in the Enum)
            if match_state == modelarmor_v1.FilterMatchState.MATCH_FOUND:
                status.update(label="Security Threat Detected!", state="error")
                st.error("🛑 **BLOCKED**: Prompt rejected by security policy.")
                
                # Optional: Show specifically WHY it was blocked
                st.warning("Violation details are listed in the JSON above.")
                
            else:
                status.update(label="Security Check Passed", state="complete")
                st.success("✅ Clean prompt. Forwarding to LLM...")
                
                try:
                    llm_response = call_third_party_llm(user_input)
                    st.subheader("LLM Output:")
                    st.write(llm_response)
                except Exception as e:
                    st.error(f"LLM Error: {e}")
                    
        except Exception as e:
            st.error(f"Error connecting to Model Armor: {e}")
