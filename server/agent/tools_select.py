from langchain.tools import Tool
from server.agent.tools import *

from server.agent.tools import query_knowledge_graph, QueryKnowledgeGraphInput
from server.agent.tools import complete_triple, CompleteTripleInput

## 请注意，如果你是为了使用AgentLM，在这里，你应该使用英文版本。
#
# tools = [
#     Tool.from_function(
#         func=calculate,
#         name="calculate",
#         description="Useful for when you need to answer questions about simple calculations",
#         args_schema=CalculatorInput,
#     ),
#     Tool.from_function(
#         func=arxiv,
#         name="arxiv",
#         description="A wrapper around Arxiv.org for searching and retrieving scientific articles in various fields.",
#         args_schema=ArxivInput,
#     ),
#     Tool.from_function(
#         func=weathercheck,
#         name="weather_check",
#         description="",
#         args_schema=WhetherSchema,
#     ),
#     Tool.from_function(
#         func=shell,
#         name="shell",
#         description="Use Shell to execute Linux commands",
#         args_schema=ShellInput,
#     ),
#     Tool.from_function(
#         func=search_knowledgebase_complex,
#         name="search_knowledgebase_complex",
#         description="Use Use this tool to search local knowledgebase and get information",
#         args_schema=KnowledgeSearchInput,
#     ),
#     Tool.from_function(
#         func=search_internet,
#         name="search_internet",
#         description="Use this tool to use bing search engine to search the internet",
#         args_schema=SearchInternetInput,
#     ),
#     Tool.from_function(
#         func=wolfram,
#         name="Wolfram",
#         description="Useful for when you need to calculate difficult formulas",
#         args_schema=WolframInput,
#     ),
#     Tool.from_function(
#         func=search_youtube,
#         name="search_youtube",
#         description="use this tools to search youtube videos",
#         args_schema=YoutubeInput,
#     ),
# ]

tools = [

    # Tool.from_function(
    #     func=query_knowledge_graph,
    #     name="StepInKG",
    #     description="Use this tool to query knowledge and facts about the question. It parse steps and execute on KG, return accurate answer.",
    #     args_schema=QueryKnowledgeGraphInput,
    # ),
    # Tool.from_function(
    #     func=complete_triple,
    #     name="CompleteTriple",
    #     description="Use this tool complete knowledge triples.",
    #     args_schema=CompleteTripleInput,
    # ),
    Tool.from_function(
        func=query_knowledge_graph,
        name="StepInKG",
        description="根据一系列知识图谱查询的分解步骤，产生查询语句，并执行。返回每一步的结果。",
        args_schema=QueryKnowledgeGraphInput,
    ),
    Tool.from_function(
        func=complete_triple,
        name="CompleteTriple",
        description="用于补齐带有?的不完整知识三元组。（调用返回三元组后，你要说'我将参考这些事实三元组进行回答。Final Answer: 根据我的推理，最终答案为'）",
        args_schema=CompleteTripleInput,
    ),

]

tool_names = [tool.name for tool in tools]

