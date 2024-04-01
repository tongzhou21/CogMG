
from langchain.llms import TextGen

from pydantic import BaseModel, Field
import json
import os


def exe_program(str_program):
    url = "http://localhost:18764/kopl_server?program={:s}".format(str_program)
    import requests
    response = requests.get(url=url)
    dict_data = json.loads(response.text)
    return dict_data['list_entity_qid_and_name'], dict_data['final_ans']

def tool_StepsInKG_func(steps, llm_tool_stepsinkg):
    prompt = "在**Program**中生成输出。\n" + \
             "**Program**是函数调用步骤，用于执行在**Thoughts**中的思考步骤。\n" + \
             "请逐行生成这些函数调用链，用dict的形式表示每个函数调用，用list组织输出格式。\n" + \
             '每行的函数调用dict的简单介绍：\n' + \
             '{"function": <str: 函数名>, "dependencies": <list: 输入依赖，之前步骤的序号>, "inputs": <list: 函数输入>}\n' + \
             "\n请根据**Thoughts**，补全对应的**Program**：\n" + \
             "**Thoughts**:\n" + steps.strip() + '\n' + \
             "**Program**:\n"

    input = prompt

    str_program = llm_tool_stepsinkg(input)

    print(str_program)

    list_entity_qid_and_name, final_ans = exe_program(str_program.replace('\n', ''))
    return final_ans

class QueryKnowledgeGraphInput(BaseModel):
    query: str = Field()

def query_knowledge_graph(query: str):
    llm_tool_stepsinkg = TextGen(model_url="ws://localhost:12316", streaming=True)  # TODO: 修改
    ans = tool_StepsInKG_func(query, llm_tool_stepsinkg)
    return ans


if __name__ == "__main__":
    program = '''[
{'function': 'Find', 'dependencies': [], 'inputs': ['Seattle']},
{'function': 'Find', 'dependencies': [], 'inputs': ['Cebu City']},
{'function': 'QueryRelationQualifier', 'dependencies': [0, 1], 'inputs': ['twinned administrative body', 'start time']},
]
'''
    print(exe_program(program))

