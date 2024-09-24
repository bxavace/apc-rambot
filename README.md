# Rambot
Generative AI __Chatbot__ of the Rams with Naive RAG and Azure

Install dependencies:
```
pip install -r requirements.txt
```

Set environment variables:
```
VECTOR_STORE_ADDR=<ai_search_endpoint>
VECTOR_STORE_KEY=<ai_search_privatekey>
AZ_OAI_ENDPOINT=<azure_openai_endpoint>
AZ_OAI_KEY=<azure_openai_key>
AZ_OAI_VER=2024-02-01
AZ_OAI_DEPLOYMENT=<azure_openai_embeddings_deployment_name>
```

Run:
```
python app.py
```
