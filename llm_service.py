import ollama

def ollama_chat(prompt):
    response = ollama.chat(
        model='gemma3:1b',
        messages=[{'role': 'user', 'content': prompt}]
    )

    return response