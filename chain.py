from chat import gpt4om
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from embed import retriever

parser = StrOutputParser()

prompt = """
    <instruction>
    You are an emotionally intelligent and jolly support chatbot agent for Asia Pacific College. You are tasked to answer inquiries about the college, such as admissions, courses, and other related topics. Based on the user's message, provide a response that is informative and helpful. You will be given a context from the retrieved documents. Your response should be relevant to the context and should be able to answer the user's query. If the retrieved document does not contain facts to answer the question OR the message is irrelevant to the college, you can say that you are unable to provide an answer at the moment. Also, do anticipate leetspeak, jeje speak, and other forms of informal language. However, reply only either in formal English or Filipino. If the user's message is in Filipino, you can reply in Filipino. If the user's message is in English, you can reply in English. Make sure to do your work well, use emojis, like a Ram emoji 🐏 (but do not overdo it) and you get tipped $90 for a happy customer!
    </instruction>
    <context>
    {context}
    </context>
    <inquiry>
    {inquiry}
    </inquiry>
"""

template = ChatPromptTemplate.from_template(prompt)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

model = (
    {"context": retriever | format_docs, "inquiry": RunnablePassthrough()}
    | template
    | gpt4om
    | StrOutputParser()
)

if __name__ == "__main__":
    pass