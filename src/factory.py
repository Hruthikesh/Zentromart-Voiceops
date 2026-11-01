import os
from .config import dataset_path, load_env
from .llm import LLM
from .retrieval import Retriever
from .tools import ToolStore
from .agent import Agent


def components():
    load_env()
    root = dataset_path()
    llm = LLM()
    retriever = Retriever(root, os.getenv('EMBEDDING_MODEL',
                          'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'))
    return llm, retriever, ToolStore(root)


def make_agent():
    return Agent(*components())
