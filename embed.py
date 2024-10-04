import os
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

AZ_OAI_ENDPOINT = os.getenv('AZ_OAI_ENDPOINT')
AZ_OAI_VER = os.getenv('AZ_OAI_VER')
AZ_OAI_KEY = os.getenv('AZ_OAI_KEY')
VECTOR_STORE_ADDR= os.environ.get('VECTOR_STORE_ADDR')
VECTOR_STORE_KEY= os.environ.get('VECTOR_STORE_KEY')
AZ_OAI_DEPLOYMENT= os.environ.get('AZ_OAI_DEPLOYMENT')
INDEX_NAME_DEV = os.environ.get('INDEX_NAME_DEV')

embeddings = AzureOpenAIEmbeddings(
    azure_deployment=AZ_OAI_DEPLOYMENT,
    openai_api_version=AZ_OAI_VER,
    azure_endpoint=AZ_OAI_ENDPOINT,
    api_key=AZ_OAI_KEY,
)

datastore = AzureSearch(
    azure_search_endpoint=VECTOR_STORE_ADDR,
    azure_search_key=VECTOR_STORE_KEY,
    index_name=INDEX_NAME_DEV,
    embedding_function=embeddings.embed_query,
)

retriever = datastore.as_retriever()

if __name__ == "__main__":
    pass