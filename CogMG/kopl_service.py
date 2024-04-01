import flask,json
from flask import request
from kopl.kopl import KoPLEngine

import os
#### 读取知识图谱
class KOPLKB():
    def __init__(self):
        #### 图谱执行程序
        with open('~/data/KG/kqa_pro/kb.IID.json', 'r') as f_read:  # 新版知识库
            self.dict_kb = json.load(f_read)
        self.engine = KoPLEngine(self.dict_kb)  # TODO: 检查键值，加入engine
        self.list_entity_qid_and_name = []

        self.question2program = {}
        self.question2tuples = {}

    def exe_program(self, str_program):
        list_entity_qid_and_name, final_ans = self._exe_program(str_program, engine=self.engine)
        if final_ans == '图谱查询失败':
            print('查询失败，寻找新加入的知识')

        return list_entity_qid_and_name, final_ans


    def _exe_program(self, str_program, engine=None):
        if engine is None:
            engine = self.engine

        print('str_program ⬇️')
        print(str_program)
        print('str_program ⬆️')

        list_entity_qid_and_name = []
        final_ans = '图谱查询失败'

        list_p = None
        try:
            list_p = eval(str_program)
        except:
            print('图谱执行语句解析错误')

        if list_p is not None:
            try:
                program = list_p
                list_func = [d['function'] for d in program]
                list_input = [d['inputs'] for d in program]
                list_entity_qid_and_name, final_ans = engine.forward_steps_entity(list_func, list_input, ignore_error=False, show_details=False)
            except:
                print('图谱执行语句执行错误')
        else:
            list_entity_qid_and_name = []
            final_ans = '图谱查询失败'
        if final_ans == '':
            final_ans = '图谱查询失败'
        elif final_ans == '0':
            final_ans = '图谱查询失败'
        elif final_ans != '图谱查询失败':
            final_ans = '执行结果 ' + final_ans
        return list_entity_qid_and_name, final_ans


server = flask.Flask(__name__)
@server.route('/kopl_server',methods=['get','post'])
def kopl_server():
    program = request.values.get('program')

    if program:
        list_entity_qid_and_name, final_ans = kb.exe_program(program)

        resu = {'code': 200, 'final_ans': final_ans, 'list_entity_qid_and_name': list_entity_qid_and_name}
        print(resu)
        return json.dumps(resu, ensure_ascii=False)


if __name__== '__main__':
    kb = KOPLKB()
    server.run(debug=True,port = 18764, host='0.0.0.0', use_reloader=False)

