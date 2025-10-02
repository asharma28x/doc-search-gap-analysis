import json
import requests


from typing import Any, Dict, Iterator, List, Mapping, Optional
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import GenerationChunk
from langchain.llms.base import LLM

from auth import authenticate

class MyCustomLLM(LLM):
    """Custom LLM wrapper for a remote LLM API."""
    api_url : str 
    token :str
    model_id :str
    ID :str

    @property
    def _llm_type(self) -> str:
        return "my_custom_llm"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        # Prepare headers
        headers = {
            'Accept': 'text/event-stream' ,
            'Content-Type': 'application/json',
            'Authorization': self.token 
            }
        # Prepare messages, e.g., system + user
        messages = [
            {
                "role": "system",
                "content": "You are an AI assistant that helps answering questions",
            },
            {
                "role": "user",
                "content": prompt,
            }
        ]

        # Prepare data payload
        data =  {
        "id": self.ID,
        "modelId": self.model_id,
        "messages": messages,
        "maxTokens": 2000,
        "stream": False,
        "presencePenalty": 0,
        "stop": None,
        "frequencyPenalty": 0,
        "topP": 0.95,
        "temperature": 0.7,
        "safeGuardSettings": {
            "status": "monitor",
            "configurationStyle": "easy",
            "configuration": {
            "moderation": "one",
            "personalInformation": "one",
            "promptInjection": "one",
            "unknownLinks": "one"
            }
        },
        "locale": "en"
        }

        # Make the POST request
        response = requests.post(self.api_url, json=data, headers=headers)
        result = response.json()
        # print(json.dumps(result, indent=4))
        return result["content"]


# if __name__ == '__main__':
#     token = authenticate()
    
#     # Usage
#     my_llm = MyCustomLLM(
#         api_url='https://api.ntth.ai/v1/chat',
#         token= token,
#         model_id="cc5bab32-9ccf-472b-9d76-91fc2ec5b047",
#         ID = 'dbfa14f2-1566-46f8-acff-b5b9928f380f'
#     )

#     # response = 
#     response = my_llm.invoke("What is NTT Data?")
#     print(response)

    