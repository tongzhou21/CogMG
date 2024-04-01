import langchain
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import TextGen
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain.schema.retriever import BaseRetriever, Document
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from typing import Any, Iterable, List, Optional
from pyserini.search.lucene import LuceneSearcher
import flask,json
from flask import request


def my_bm25(query):
    folder_path_index = '~/data/KG/wikipedia/pyserini-index/index-en/wikipedia-en.dump20231001-chunk128/'
    searcher = LuceneSearcher(folder_path_index)
    hits = searcher.search(query, k=5)
    list_res = [json.loads(hits[i].raw)['contents'] for i in range(len(hits))] # TODO: 是否加入文档标题
    return list_res

class CustomRetriever(EnsembleRetriever):  #
    def _get_relevant_documents(
            self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        list_punc = ['[', ']', '(', ')', "'"]
        for punc in list_punc:
            query = query.replace(punc, '')
        list_text = my_bm25(query)
        str_res = '\n'.join(['{:d}. {:s}'.format(i, text.replace('\n', '\t'))
                             for i, text in enumerate(list_text)])
        return str_res

def configure_retriever():
    vectorstore = Chroma(
        persist_directory = "~/data/KG/wikipedia/db.chroma.wikipedia.en.token512.overlap64", # top20, token分块
        embedding_function = HuggingFaceBgeEmbeddings(
            model_name="~/huggingface_model/BAAI/bge-base-en-v1.5"
        )
    )
    vectorstore_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

    retriever = CustomRetriever(retrievers=[vectorstore_retriever], weights=[1])

    llm = TextGen(model_url="ws://localhost:12314", streaming=True)

    template = """You are a fact checker.
Complete the knowledge in the incomplete triples (Triples Incomplete) using the facts from the context (Context) given below.
'?' represents uncertain information in incomplete triples, that is, the part you need to complete with information in the context.
Only focus on incomplete triples with '?' and do not output other facts.
Directly generate a tuple list, the format refers to the given incomplete triplet.

If you don't know the answer, try your best to generate a reasonable result.
Please refer to Context relevance to these knowledge. Generate triples in Triples Truth.

Context:
{context}

Triples Incomplete:
{question}

Triples Truth:
"""

    rag_prompt_custom = PromptTemplate.from_template(template)

    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | rag_prompt_custom
        | llm
    )

    return rag_chain, retriever

def re_tuple(str_tuple_list):
    import re
    regex = r"\(\s*('?[^']+'?|\S+)\s*,\s*('?[^']+'?|\S+)\s*,\s*('?[^']+'?|\S+)\s*\)"

    matches = re.findall(regex, str_tuple_list)

    triplets = [tuple(map(lambda x: x.strip("'"), match)) for match in matches]

    return triplets

rag_chain, retriever = configure_retriever()
server = flask.Flask(__name__)


@server.route('/rag',methods=['get','post'])
def rag_server():
    query = request.values.get('query')

    if query:
        res = rag_chain.invoke(query)

        list_tuple = re_tuple(res)

        str_wiki = retriever.get_relevant_documents(query)

        resu = {'code': 200,
                'final_ans': list_tuple,
                'docs': str_wiki,}
        # print(resu)
        return json.dumps(resu, ensure_ascii=False)


if __name__== '__main__':
    server.run(debug=True,port = 18766, host='0.0.0.0', use_reloader=False)

    str_query = "[('The Wandering Earth', 'box office', '?'),('The Wandering Earth II', 'box office', '?'),]"
    url = "http://localhost:18766/rag?query={:s}".format(str_query)
    import requests
    response = requests.get(url=url)
    dict_data = json.loads(response.text)
    print('dict_data', dict_data)









