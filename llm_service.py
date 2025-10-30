# Use custom LLM API from LLM.py
from LLM import MyCustomLLM
from auth import authenticate
from ntt_secrets import NTT_ID

def llm_chat(prompt, max_tokens=4000):
    token = authenticate()
    llm = MyCustomLLM(
        api_url='https://api.ntth.ai/v1/chat',
        token=token,
        # model_id="cc5bab32-9ccf-472b-9d76-91fc2ec5b047", # GPT-4o-mini
        model_id="a4022a51-2f02-4ba7-8a31-d33c7456b58e", # Gemini 2.5 Flash
        # model_id="6c26a584-a988-4fed-92ea-f6501429fab9", # GPT-4o

        ID=NTT_ID,
        max_tokens=max_tokens
    )
    return llm._call(prompt)