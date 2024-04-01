import streamlit as st
from webui_pages.utils import *
from st_aggrid import AgGrid, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import pandas as pd
from typing import Literal, Dict, Tuple
import os
import json
import copy
import re
import requests

cell_renderer = JsCode("""function(params) {if(params.value==true){return '✓'}else{return '×'}}""")


def re_tuple(str_tuple_list):
    regex = r"\(\s*('?[^']+'?|\S+)\s*,\s*('?[^']+'?|\S+)\s*,\s*('?[^']+'?|\S+)\s*\)"

    matches = re.findall(regex, str_tuple_list)
    triplets = [tuple(map(lambda x: x.strip("'"), match)) for match in matches]

    return triplets

def config_aggrid(
        df: pd.DataFrame,
        columns: Dict[Tuple[str, str], Dict] = {},
        selection_mode: Literal["single", "multiple", "disabled"] = "single",
        use_checkbox: bool = False,
) -> GridOptionsBuilder:
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_column("No", width=40)
    for (col, header), kw in columns.items():
        gb.configure_column(col, header, wrapHeaderText=True, **kw)
    gb.configure_selection(
        selection_mode=selection_mode,
        use_checkbox=use_checkbox,
    )
    gb.configure_pagination(
        enabled=True,
        paginationAutoPageSize=False,
        paginationPageSize=10
    )
    return gb



def knowledge_base_page(api: ApiRequest, is_lite: bool = None):
    if 'df_tuple' not in st.session_state:
        file_path_kb_unhit = 'res/kb_unhit.csv'
        if os.path.exists(file_path_kb_unhit) == False:
            st.info(f"暂无未处理三元组")
            st.stop()

        df_tuple = pd.read_csv(file_path_kb_unhit)
        df_tuple = df_tuple.iloc[::-1]
        df_tuple = df_tuple.reset_index()
        st.session_state.df_tuple = df_tuple

    if 'flag_rag' not in st.session_state:
        st.session_state.flag_rag = False

    for idx, d in enumerate(st.session_state.df_tuple):
        st.session_state.df_tuple.at[idx, 'No'] = idx
        st.session_state.df_tuple.at[idx, 'VerifiedTriples'] = ''
        st.session_state.df_tuple.at[idx, 'WikipediaPages'] = ''

    if 'df_info' not in st.session_state:
        st.session_state.df_info = copy.copy(st.session_state.df_tuple)
        st.session_state.df_info = st.session_state.df_tuple[[
            "Question", "KnowledgeTriple", "ModelCompletion", "VerifiedTriples", "tuple_count", 'WikipediaPages',"No",
        ]]
    selected_rows = []
    if not len(st.session_state.df_tuple) or \
            not len(st.session_state.df_info) or \
            len(st.session_state.df_info) == 0 or st.session_state.df_info.at[0, 'Question'] is None:
        st.info(f"暂无未处理三元组")
    else:
        with st.sidebar:
            st.write('Out Of Knowledge Graph')

            gb = config_aggrid(
                st.session_state.df_info,
                {
                    ("KnowledgeTriple", "KnowledgeTriple"): {},
                    ("Question", "Question"): {},
                    ("ModelCompletion", "ModelCompletion"): {},
                    ("VerifiedTriples", "VerifiedTriples"): {},
                    ("No", "No"): {},
                    ("tuple_count", "tuple_count"): {},
                },
                "single",
            )
            gb.configure_selection(selection_mode="single",
                                   pre_selected_rows=[0])

            doc_grid = AgGrid(
                st.session_state.df_info,
                gb.build(),
                columns_auto_size_mode="FIT_CONTENTS",
                theme="alpine",
                custom_css={
                    "#gridToolBar": {"display": "none"},
                },
                allow_unsafe_jscode=True,
                enable_enterprise_modules=False
            )


            selected_rows = doc_grid.get("selected_rows", [])

    if selected_rows:
        list_col_name = ['subject', 'relation / attribution', 'object']

        with st.container(border=True):
            st.write('###### Question:\n')
            st.write(selected_rows[0]["Question"])

            with st.form("ModelCompletion_form"):
                st.write('###### KnowledgeTriple:\n')
                list_kt = re_tuple(selected_rows[0]["KnowledgeTriple"])
                for idx_tuple in range(len(list_kt)):
                    cols_tuple = st.columns([1 / 3, 1 / 3, 1 / 3])
                    for idx_col, cols_cur in enumerate(cols_tuple):
                        with cols_cur:
                            st.text_input(
                                label=list_col_name[idx_col],
                                key=f'KnowledgeTriple_idx_tuple{idx_tuple}idx_col{idx_col}',
                                value=list_kt[idx_tuple][idx_col], disabled=False)

                st.write('###### ModelCompletion:\n')
                list_mc = re_tuple(selected_rows[0]["ModelCompletion"])
                for idx_tuple in range(len(list_kt)):
                    cols_tuple = st.columns([1 / 3, 1 / 3, 1 / 3])
                    for idx_col, cols_cur in enumerate(cols_tuple):
                        with cols_cur:
                            st.text_input(
                                label=list_col_name[idx_col],
                                key=f'ModelCompletion_idx_tuple{idx_tuple}idx_col{idx_col}',
                                value=list_mc[idx_tuple][idx_col], disabled=False) # TODO: update
                list_sub_but = st.columns([0.29, 0.28, 0.43])

                with list_sub_but[0]:
                    if st.form_submit_button("Model Completion add to KG", disabled=st.session_state.flag_rag):
                        list_tuple_add = [tuple(tuple_new) for tuple_new in list_mc
                                          if (tuple_new[0] != '' and tuple_new[1] != '' and tuple_new[2] != '')]

                        if os.path.exists('res/kg_tuples.json'):
                            with open('res/kg_tuples.json',
                                      'r') as f_read:
                                question2tuples = json.load(f_read)
                        else:
                            question2tuples = {}
                        question2tuples[selected_rows[0]["Question"]] = list_tuple_add

                        with open('res/kg_tuples.json', 'w') as f_write:
                            f_write.write(json.dumps(question2tuples, ensure_ascii=False) + '\n')
                        st.toast(f'{len(list_tuple_add)} tuples add to KG.')
                        st.session_state.flag_rag = False
                with list_sub_but[1]:
                    if st.form_submit_button("Wikipedia knowledge verify", disabled=st.session_state.flag_rag):
                        st.session_state.flag_rag = True

            if st.session_state.df_info.at[int(selected_rows[0]['No']), 'WikipediaPages'] != '':
                with st.status("Searching Wikipedia... " + selected_rows[0]["Question"], expanded=False,  state="complete") as status:
                    query = selected_rows[0]["KnowledgeTriple"].replace('\n', '').replace(')]', '),]')

                    st.write('###### Query')
                    st.write(query)
                    st.write('###### Wikipedia Doc')
                    print(st.session_state.df_info.at[int(selected_rows[0]['No']), 'WikipediaPages'])
                    st.write(st.session_state.df_info.at[int(selected_rows[0]['No']), 'WikipediaPages'])

            if st.session_state.flag_rag:
                with st.status("Searching Wikipedia... " + selected_rows[0]["Question"], expanded=False) as status:
                    query = selected_rows[0]["KnowledgeTriple"].replace('\n', '').replace(')]', '),]')

                    st.write('###### Query')
                    st.write(query)

                    st.write('###### Wikipedia Doc')
                    url = "http://localhost:18766/rag?query={:s}".format(query)

                    response = requests.get(url=url)
                    dict_data = json.loads(response.text)
                    dict_data['docs'] = dict_data['docs'].replace('$', '\\$')
                    st.write(dict_data['docs'])

                    st.session_state.df_info.at[int(selected_rows[0]['No']), 'WikipediaPages'] = dict_data['docs']

                    st.session_state.df_info.at[int(selected_rows[0]['No']), 'VerifiedTriples'] = str(dict_data['final_ans'])
                    selected_rows[0]["VerifiedTriples"] = str(dict_data['final_ans'])

                    st.session_state.flag_rag = False
                    st.rerun()

            if st.session_state.df_info.at[int(selected_rows[0]['No']), 'VerifiedTriples'] != '':
                with st.form("VerifiedTriples_form"):
                    st.write('###### VerifiedTriples:\n')
                    tuple_count = int(selected_rows[0]['tuple_count'])
                    str_list_tuple_model = selected_rows[0]["VerifiedTriples"]
                    # list_tuple_cur = re_tuple(str_list_tuple_model)
                    list_tuple_cur = re_tuple(str_list_tuple_model.replace('[', '(').replace(']', ')'))
                    list_tuple_new = [list(t) for t in list_tuple_cur] + [['', '', ''] for _ in range(tuple_count)]
                    list_tuple_new = list_tuple_new[:max(tuple_count, len(list_tuple_cur))]

                    list_col_name = ['subject', 'relation / attribution', 'object']

                    for idx_tuple in range(len(list_tuple_new)):
                        cols_tuple = st.columns([1 / 3, 1 / 3, 1 / 3])
                        for idx_col, cols_cur in enumerate(cols_tuple):
                            with cols_cur:
                                list_tuple_new[idx_tuple][idx_col] = st.text_input(
                                    label=list_col_name[idx_col],
                                    key=f'VerifiedTriples_idx_tuple{idx_tuple}idx_col{idx_col}',
                                    value=list_tuple_new[idx_tuple][idx_col])  # TODO: update

                    if st.form_submit_button("add to KG"):
                        list_tuple_add = [tuple(tuple_new) for tuple_new in list_tuple_new
                                          if (tuple_new[0] != '' and tuple_new[1] != '' and tuple_new[2] != '')]
                        st.toast(f'{len(list_tuple_add)} tuples add to KG.')

                        if os.path.exists('res/kg_tuples.json'):
                            with open('res/kg_tuples.json', 'r') as f_read:
                                question2tuples = json.load(f_read)
                        else:
                            question2tuples = {}
                        question2tuples[selected_rows[0]["Question"]] = list_tuple_add

                        with open('res/kg_tuples.json', 'w') as f_write:
                            f_write.write(json.dumps(question2tuples, ensure_ascii=False) + '\n')

