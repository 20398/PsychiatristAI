from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import search_docs

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

def ask_agent(query: str):
    context = search_docs(query)

    prompt = f"""
                You are a helpful assistant.
                Answer using ONLY the context below.

                Context:
                {context}

                Question:
                {query}
                """

    response = llm.invoke(prompt)
    return response.content