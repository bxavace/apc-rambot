import os
import time
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

load_dotenv()

AZ_OAI_ENDPOINT = os.getenv("AZ_OAI_ENDPOINT")
AZ_OAI_VER = os.getenv("AZ_OAI_VER")
AZ_OAI_KEY = os.getenv("AZ_OAI_KEY")

gpt4om = AzureChatOpenAI(
    azure_deployment="gpt-4o-mini",
    api_version=AZ_OAI_VER,
    api_key=AZ_OAI_KEY,
    azure_endpoint=AZ_OAI_ENDPOINT,
    max_retries=2,
    streaming=True
)

if __name__ == "__main__":
    start = time.time()
    response = gpt4om.invoke("Tell me a trivia about Ayala in Makati City, Philippines.")
    end = time.time()
    print(f"Response: {response.content}\n Time elapsed: {end - start} seconds")