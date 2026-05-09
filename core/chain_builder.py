"""
Langchain RAG chain for the Meeting AI Assistant chat tab.

Architecture:
  VectorStoreRetriever — wraps vector_store query function
                         into a Langchain-compatible BaseRetriever
  build_rag_chain      — returns a ConversationalRetrievalChain backed by
                         VectorStoreRetriever + ConversationBufferMemory
"""

from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks.manager import CallbackManagerForRetrieverRun
from langchain_openai import ChatOpenAI
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from pydantic import ConfigDict

from .vector_store import query_relevant_documents

ROLE_PROMPTS = {
    "Manager": "Focus on decisions, risks, priorities, and high-level outcomes.",
    "Developer": "Focus on implementation details, blockers, dependencies, and tasks.",
    "QA": "Focus on test coverage, edge cases, validation, and quality risks.",
}


class VectorStoreRetriever(BaseRetriever):
    """Bridges vector_store module to the Langchain retriever interface."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    n_results: int = 3

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        results = query_relevant_documents(query, n_results=self.n_results)
        return [Document(page_content=r["page_content"], metadata=r["metadata"]) for r in results]


def build_rag_chain(
    base_url: str, api_key: str, role: str = "Manager"
) -> ConversationalRetrievalChain:
    """
    Build a ConversationalRetrievalChain with role-aware prompting.

    Components:
      - ChatOpenAI (Azure) as the LLM
      - VectorStoreRetriever pulling top-3 chunks from FAISS index
      - ConversationBufferMemory for multi-turn memory
      - PromptTemplate injecting the role instruction
    """
    llm = ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model="GPT-4o",
        temperature=0.4,
    )

    prompt = PromptTemplate(
        template=(
            "You are a helpful meeting assistant. "
            f"{ROLE_PROMPTS.get(role, '')}\n\n"
            "Use the retrieved meeting notes below to answer accurately.\n\n"
            "Context:\n{context}\n\n"
            "Question: {question}\n"
            "Answer:"
        ),
        input_variables=["context", "question"],
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
    )

    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=VectorStoreRetriever(),
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        return_source_documents=False,
        verbose=False,
    )
