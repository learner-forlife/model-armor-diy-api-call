The purpose of this repo is to explain DIY mode of model armor
under this mode , the application developer calls the Model Armor API before handing the call to LLM . Similarly , in reponse , the application will call the Model Armor API before the response is handed over to the end client

Model Armor configuration is defined in a 'template ' , which is a GCP regional resources . It defines what AI security parameters you wish to be inspected and at what confidence level.



# model-armor-diy-api-call
This repo explains how a customer owned application enforces runtime security by integrating with model armor service 

# the function named "call_model_armor"
This function does not make decisions. It simply takes the text, runs to Google service , asks "Is this safe?", and brings back the report.

Key Concept: APIs are picky. We had to set api_endpoint manually because Model Armor lives in specific regions (like us-central1), not a global address.
Input: The raw text .
Output: A complex object containing the "Sanitization Result" (Pass/Fail).

# the function call_third_party_llm


# The scan phase 

armor_response = call_model_armor(user_input)
    sanitization_result = armor_response.sanitization_result
    match_state = sanitization_result.filter_match_state

match_state: This is the most important variable in the whole code. It holds the verdict. It is usually an "Enum" (a number representing a state):

MATCH_FOUND (Bad)
NO_MATCH_FOUND (Good)

# Sample Code #
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
