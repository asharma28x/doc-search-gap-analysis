# doc-search-gap-analysis

To create a new branch in github, use the command:

```bash
git checkout -b <Branch-Name>
```

where ```<Branch-Name>``` should be the name of the feature you're coding up and adding to the repo. Commit and publish the branch using the VSCode sidebar after. 

A document comparison Agentic AI that takes a regulatory doc and compares it to the internal docs to check for any discrepencies, you will need to download Ollama by using the following commands:

```bash
curl -fsSL https://ollama.com/install.sh | sh

ollama serve &

ollama pull gemma3:1b
```
Every time you run the app, make sure to run only 
```bash
ollama serve &

ollama pull gemma3:1b
```
commands to start the Ollama server. You will only need to do ```ollama pull gemma3:1b``` command once

After you have Ollama installed, you can run the following command to install the required Python packages:
```bash
pip install -r requirements.txt
```

Finally, you can run the system using the following command:

```bash
python main.py
```
