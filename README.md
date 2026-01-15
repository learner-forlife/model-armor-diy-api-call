The purpose of this repo is to explain DIY mode of model armor
under this mode , the application developer calls the Model Armor API before handing the call to LLM . Similarly , in reponse , the application will call the Model Armor API before the response is handed over to the end client

Model Armor configuration is defined in a 'template ' , which is a GCP regional resources . It defines what AI security parameters you wish to be inspected and at what confidence level.

In this repo , I have -
(a) A application runnign on a Debian VM . Its a simple applciation with a input and output option .
    User asks question in input text box -- it goes to LLM -- get reponse -- shows in output box 
(b) The code of application is shared in this repo .
(c) To include runtime AI security with Model Armor , flow of this application includes a call to Model Armor API (us-central in my case)

# Pre-requisites 
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install streamlit google-cloud-modelarmor huggingface_hub

The compute runnign application must have correct IAM permissions

$ gcloud projects add-iam-policy-binding <<project-id>> \
    --member="serviceAccount:<<project-number>>-compute@developer.gserviceaccount.com" \
    --role="roles/modelarmor.user"

# Now lets look at the Application logic #


## (1) The function named "call_model_armor"
This function does not make decisions. It simply takes the text, runs to Google service , asks "Is this safe?", and brings back the report.

Key Concept: APIs are picky. We had to set api_endpoint manually because Model Armor lives in specific regions (like us-central1), not a global address.
Input: The raw text .
Output: A complex object containing the "Sanitization Result" (Pass/Fail).

## (2) The function call_third_party_llm


## (3) The scan phase 

armor_response = call_model_armor(user_input)
    sanitization_result = armor_response.sanitization_result
    match_state = sanitization_result.filter_match_state

match_state: This is the most important variable in the whole code. It holds the verdict. It is usually an "Enum" (a number representing a state):

MATCH_FOUND (Bad)
NO_MATCH_FOUND (Good)

# Critical Sample Code section #
    if match_state == modelarmor_v1.FilterMatchState.MATCH_FOUND:
        st.error("🛑 BLOCKED...")
        # CODE STOPS HERE. The LLM is never called.
    else:
        st.success("✅ Clean prompt...")
        
        # Now we call the LLM
        llm_response = call_third_party_llm(user_input)
        st.write(llm_response)

Notice that call_third_party_llm is inside the else block. 
If the if condition (Block) is true, the code literally cannot reach the LLM. That is what makes this a secure design.
