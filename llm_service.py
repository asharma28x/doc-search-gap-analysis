# Use custom LLM API from LLM.py
from LLM import MyCustomLLM
from auth import authenticate
from ntt_secrets import NTT_ID

def llm_chat(prompt):
    token = authenticate()
    llm = MyCustomLLM(
        api_url='https://api.ntth.ai/v1/chat',
        token=token,
        model_id="cc5bab32-9ccf-472b-9d76-91fc2ec5b047",
        ID=NTT_ID
    )
    return llm._call(prompt)