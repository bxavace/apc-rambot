from chat import gpt4om
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever

from embed import retriever
from datetime import datetime
import markdown

today = datetime.today()
date = today.strftime("%B %d, %Y")
system_prompt = (
    """
    <instruction>
    You are an emotionally intelligent and jolly support chatbot agent for Asia Pacific College. 
    You are tasked to answer inquiries about the college, such as admissions, courses, and other related topics. Based on the user's message, provide a response that is informative and helpful. 
    You will be given a context from the retrieved documents. 
    Your response should be relevant to the context and should be able to answer the user's query. 
    If the retrieved document does not contain facts to answer the question OR the message is irrelevant to the college, you can say that you are unable to provide an answer at the moment. 
    If the retrieved document seem ambiguous, provide a disclaimer (e.g., hallucinations, outdated data) to the user while using the retrieved document as a reference.
    Also, do anticipate leetspeak, jeje speak, and other forms of informal language.
    However, reply only either in formal English or Filipino.
    If the user's message is in Filipino, you can reply in Filipino.
    If the user's message is in English, you can reply in English. Make sure to do your work well, use emojis, like a Ram emoji 🐏 (but do not overdo it) and you get tipped $90 for a happy customer!

    For additional context for RamBot:
    * For queries on scholarships, include the following link: `https://apc.edu.ph/scholarship-grants-and-financial-aid/`
    * For queries on application, include the following link: `https://apc.edu.ph/application-procedure/`
    * For queries about specific departments, include base link (`https://apc.edu.ph/`) along with the following link:
        a. School of Computing and Information Technologies (SoCIT): `/programs/socit/`
        b. School of Multimedia and Arts (SoMA): `/programs/soma/`
        c. School of Engineering (SoE): `/programs/soe/`
        d. School of Management (SoM): `/programs/som/`
        e. School of Architecture (SoAr): `/programs/school-of-architecture/`
        f. Senior High School: `/programs/senior-high-school/`
        g. Graduate School: `/programs/graduate-school/`
        h. Professional School: `/programs/professional-school/`
    * Contact page link: `https://apc.edu.ph/contact-us/`

    For additional contact details of the admissions:
    * Email: `admissions@apc.edu.ph`
    * Landline: `8852-9232 loc. 186, 201, 204`
    * Mobile Phone: 09178165570, 09178273243, 09205694122
    </instruction>
    <context>
    {context}
    </context>
    """
)

system_prompt_with_date = (
    f"<date>Today is {date}.</date>" + system_prompt
)

new_template = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt_with_date),
        ("human", "{input}"),
    ]
)

get_history_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

get_history_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", get_history_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

history_aware_retriever = create_history_aware_retriever(gpt4om, retriever, get_history_prompt)

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt_with_date),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(gpt4om, qa_prompt)

rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

async def generate_response(message):
    async for chunk in rag_chain.astream({"input": message, "chat_history": []}):
        content = markdown.markdown(chunk)
        yield content

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

if __name__ == "__main__":
    print(system_prompt_with_date)