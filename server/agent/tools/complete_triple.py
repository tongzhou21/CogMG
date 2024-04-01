
from langchain.llms import TextGen

from pydantic import BaseModel, Field
import json
import os
import time
import pandas as pd

def tool_CompleteTriple_func(tuple_blank):
    current_answer = ''
    for i in range(20):
        if os.path.exists('res/answer.txt'):
            with open('res/answer.txt', 'r') as f_read:
                current_answer = f_read.read()
            break
        time.sleep(0.1)

    prompt_icl = '''请根据提供的问题和答案，补全所涉及的提供的知识三元组的空缺部分，在**Triple Full**中生成输出。
**Triple Blank**是提供的不完整知识三元组，由元组形式包含(头实体, 关系, 尾实体)或(关系三元组, 修饰属性, 修饰值)或(头实体, 属性, 属性值)
请逐行生成完整的三元组，用tuple形式的list格式输出，输出格式参考**Triple Blank**。

我将为你提供几个示例，请学习补全三元组的方式和输出格式。

**Question**: 加拿大议会由多少个不同的组织组成？
**Answer**: 加拿大议会由两个不同的组织组成，包括众议院和参议院。
**Triple Blank**:
[
('Parliament of Canada', 'has part', '?'),
('?', 'is a', 'organization'),
]
**Triple Full**:
[
('Parliament of Canada', 'has part', 'Senate of Canada'),
('Parliament of Canada', 'has part', 'House of Commons'),
('Parliament of Canada', 'is a', 'organization'),
('House of Commons', 'is a', 'organization'),
('Senate of Canada', 'is a', 'organization'),
]

**Question**: 告诉我在由议员领导的第一级行政国家分区内海拔最高（超过海平面）的地区。
**Answer**: 由议员领导的国家包括加纳、肯尼亚、普利茅斯等，而第一级行政国家有南澳大利亚、维多利亚、北爱尔兰等。其中昆士兰州平均海拔744米，塔斯马尼亚海拔1009米，澳大利亚首都特区海拔892米。所以在由议员领导的第一级行政国家分区内海拔最高（超过海平面）的地区是塔斯马尼亚。
**Triple Blank**:
[
('?', 'office held by head of government', 'member of parliament'),
('?', 'is a', 'first-level administrative country subdivision'),
('?', 'elevation above sea level', '?'),
]
**Triple Full**:
[
('Ghana', 'office held by head of government', 'member of parliament'),
('Kenya', 'office held by head of government', 'member of parliament'),
('Plymouth', 'office held by head of government', 'member of parliament'),
('South Australia', 'is a', 'first-level administrative country subdivision'),
('Victoria', 'is a', 'first-level administrative country subdivision'),
('Northern Ireland', 'is a', 'first-level administrative country subdivision'),
('Queensland', 'elevation above sea level', '744 metre'),
('Tasmania', 'elevation above sea level', '1009 metre'),
('Australian Capital Territory', 'elevation above sea level', '892 metre'),
]

**Question**: 杰西·艾森伯格的民族使用什么语言？
**Answer**: 杰西·艾森伯格是犹太人，犹太民族通常说希伯来语。
**Triple Blank**:
[
('Jesse Eisenberg', 'ethnic group', '?'),
('?', 'is a', 'ethnic group'),
('?', 'languages spoken, written or signed', '?'),
]
**Triple Full**:
[
('Jesse Eisenberg', 'ethnic group', 'Jewish people'),
('Jewish people', 'is a', 'ethnic group'),
('Poles', 'languages spoken', 'written or signed', 'Hebrew'),
]

**Question**: 埃隆马斯克收购Twitter花费了多少美元？
**Triple Blank**:
[
('Elon Musk', 'acquisition', '?'),
('?', 'acquisition', 'Twitter'),
('?', 'cost', '?'),
]
**Triple Full**:
[
('Elon Musk', 'acquisition', 'Twitter'),
('(Elon Musk', 'acquisition', 'Twitter)', 'cost', '44 Billion United States dollar'),
]

**Question**: 以威尼斯为首都的威尼斯共和国成立于何时。
**Answer**: 威尼斯共和国成立于公元697年。威尼斯共和国的首都是威尼斯，它一度是强大的海洋共和国，影响了地中海地区的政治、经济和文化。这个共和国在中世纪和文艺复兴时期都具有重要地位，但后来在1797年被拿破仑·波拿巴的法国军队占领并解体。
**Triple Blank**:
[
('?', 'country', 'Republic of Venice'),
('Venice', 'country', '?'),
('Republic of Venice', 'capital', '?'),
('?', 'capital', 'Venice')
('?', 'start time', '?'),
]
**Triple Full**:
[
('Venice', 'country', 'Republic of Venice'),
('Republic of Venice', 'capital', 'Venice'),
(('Venice', 'country', 'Republic of Venice'), 'start time', '697'),
]

**Question**: 勒布朗詹姆斯什么时候加盟的湖人
**Answer**: 勒布朗·詹姆斯在2018年7月10日加盟洛杉矶湖人队。以下是详细的分析步骤：
**Triple Blank**:
[
('?', 'member of sports team', 'Lakers'),
('LeBron James', 'member of sports team', '?'),
('?', 'start time', '?'),
]
**Triple Full**:
[
('LeBron James', 'member of sports team', 'Lakers'), 
('Lakers', 'member of sports team', 'NBA'), 
(('LeBron James', 'member of sports team', 'Lakers'), 'start time', 'July 10th, 2018'),
]

请依据问题和答案中的事实，完成最后一个知识三元组补全任务。

'''

    user_question = 'None'

    prompt = prompt_icl + \
             "**Question**: " + user_question + '\n' + \
             "**Answer**: " + current_answer + '\n' + \
             "**Triple Blank**:\n" + tuple_blank+ '\n' + \
             "**Triple Full**:\n"

    llm_tool_completetriple = TextGen(model_url="ws://localhost:12317", streaming=True)

    str_res = llm_tool_completetriple(prompt)

    try:
        str_final = '[\n'
        if isinstance(eval(str_res), list):
            for tup in eval(str_res):
                str_final += tup + ',\n'
            str_final += ']'
            str_res = str_final
        else:
            pass
    except:
        pass

    return str_res.strip() # TODO: 验证效果

class CompleteTripleInput(BaseModel):
    query: str = Field()

def complete_triple(query: str):
    return tool_CompleteTriple_func(query)


if __name__ == "__main__":
    pass


