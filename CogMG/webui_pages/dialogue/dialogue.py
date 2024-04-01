import copy
import streamlit as st
from webui_pages.utils import *
import streamlit_chatbox
from streamlit_chatbox import *
import os
from configs import (TEMPERATURE, HISTORY_LEN, PROMPT_TEMPLATES,
                     DEFAULT_KNOWLEDGE_BASE, DEFAULT_SEARCH_ENGINE, SUPPORT_AGENT_MODEL)
import uuid
from typing import List, Dict
import streamlit as st
import json
import re
import base64
import pandas as pd


def re_tuple(str_tuple_list):
    regex = r"\(\s*('?[^']+'?|\S+)\s*,\s*('?[^']+'?|\S+)\s*,\s*('?[^']+'?|\S+)\s*\)"

    matches = re.findall(regex, str_tuple_list)

    triplets = [tuple(map(lambda x: x.strip("'"), match)) for match in matches]

    return triplets

def get_base64_of_bin_file(png_file):
    with open(png_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


chat_box = ChatBox(
    assistant_avatar='img/avatar_ai.png',
    user_avatar='img/avatar_user.png',
)

max_tool_count = 3

list_question = [
    '',
    '布伦特福德足球俱乐部的保罗·威廉姆斯何时出生？',
    '奥黛丽·赫本何时获得总统自由勋章？',
    '2022年世界杯冠军是哪只球队？',
    '《流浪地球1》和《流浪地球2》哪个票房更高？',
]

def get_messages_history(history_len: int, content_in_expander: bool = False) -> List[Dict]:
    def filter(msg):
        content = [x for x in msg["elements"] if x._output_method in ["markdown", "text"]]
        if not content_in_expander:
            content = [x for x in content if not x._in_expander]
        content = [x.content for x in content]

        return {
            "role": msg["role"],
            "content": "\n\n".join(content),
        }

    return chat_box.filter_history(history_len=history_len, filter=filter)


def upload_a_image():
    print('==> calling upload_a_image')
    st.session_state.show_image = True

def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = '''
    <style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)

def get_image_caption():
    pass

def dialogue_page(api: ApiRequest, is_lite: bool = False):
    if 'user_input' not in st.session_state:
        st.session_state.user_input = None

    if 'image' not in st.session_state:
        st.session_state.image = None

    if 'flag_agent_fail' not in st.session_state:
        st.session_state.flag_agent_fail = False

    if 'flag_running' not in st.session_state:
        st.session_state.flag_running = False

    if 'show_image' not in st.session_state:
        st.session_state.show_image = False
    if 'caption' not in st.session_state:
        st.session_state.caption = False
    if 'image_path' not in st.session_state:
        st.session_state.image_path = ''

    st.session_state.setdefault("conversation_ids", {})
    st.session_state["conversation_ids"].setdefault(chat_box.cur_chat_name, uuid.uuid4().hex)
    st.session_state.setdefault("file_chat_id", None)
    default_model = api.get_default_llm_model()[0]

    if not chat_box.chat_inited:
        st.toast(
            f"Welcome to CogMG !"
        )
        chat_box.init_session()

    with st.sidebar:
        conv_names = list(st.session_state["conversation_ids"].keys())
        index = 0
        if st.session_state.get("cur_conv_name") in conv_names:
            index = conv_names.index(st.session_state.get("cur_conv_name"))
        conversation_name = conv_names[index]
        chat_box.use_chat_name(conversation_name)
        conversation_id = st.session_state["conversation_ids"][conversation_name]

        def on_mode_change():
            mode = st.session_state.dialogue_mode
            text = f"change to {mode} mode"
            st.toast(text)

        with st.expander('⚙️ Setting', expanded=True):
            dialogue_mode = st.radio('Dialogue Mode',
                                     ["Daily Conversation", "Knowledge Augmentation"],
                                     index=1,
                                     on_change=on_mode_change,
                                     horizontal=True, captions=None,
                                     label_visibility="visible", key="dialogue_mode")

            TEMPERATURE = 0.2
            if dialogue_mode == 'Daily Conversation':
                TEMPERATURE = 0.5

            temperature = st.slider("Temperature：", 0.0, 1.2, TEMPERATURE, 0.05)
            history_len = st.number_input("history turns:", 0, 20, HISTORY_LEN)

        running_models = list(api.list_running_models())
        available_models = []
        config_models = api.list_config_models()
        if not is_lite:
            for k, v in config_models.get("local", {}).items():
                if (v.get("model_path_exists")
                    and k not in running_models):
                    available_models.append(k)
        for k, v in config_models.get("online", {}).items():
            if not v.get("provider") and k not in running_models:
                available_models.append(k)
        llm_models = running_models + available_models
        cur_llm_model = st.session_state.get("cur_llm_model", default_model)
        if cur_llm_model in llm_models:
            index = llm_models.index(cur_llm_model)
        else:
            index = 0
        st.write('llm_models', str(llm_models))
        llm_model = llm_models[0]

        index_prompt = {
            "Daily Conversation": "llm_chat",
            "Knowledge Augmentation": "agent_chat", # TODO：增加agent
        }
        prompt_templates_kb_list = list(PROMPT_TEMPLATES[index_prompt[dialogue_mode]].keys())
        if "prompt_template_select" not in st.session_state:
            st.session_state.prompt_template_select = prompt_templates_kb_list[0]

        prompt_template_name = st.session_state.prompt_template_select

    chat_box.output_messages()

    chat_input_placeholder = "Please type the question, press Shift+Enter to insert a newline."

    if prompt := st.chat_input(chat_input_placeholder, key="prompt") or st.session_state.user_input:
        st.session_state.flag_running = True
        if not prompt:
            prompt = st.session_state.user_input
            st.session_state.user_input = None
        history = get_messages_history(history_len)
        chat_box.user_say(prompt)

        if dialogue_mode == "Daily Conversation":
            chat_box.ai_say("Thinking...")

            text = ''
            message_id = ""
            r = api.chat_chat(prompt,
                            history=history,
                            conversation_id=conversation_id,
                            model=llm_model,
                            prompt_name=prompt_template_name,
                            temperature=temperature)

            for t in r:
                if error_msg := check_error_msg(t):  # check whether error occured
                    st.error(error_msg)
                    break
                text += t.get("text", "")
                chat_box.update_msg(text.replace('。。', ' 。').replace('？。', '？'))
                message_id = t.get("message_id", "")

            metadata = {
                "message_id": message_id,
                }
            chat_box.update_msg(text.replace('。。', ' 。').replace('？。', '？'), streaming=False, metadata=metadata)

        elif dialogue_mode == "Knowledge Augmentation":
            chat_box.ai_say([
                Markdown("...", in_expander=True, title="Thought", state="running", expanded=True),
                f"正在思考...",
            ])
            text = ""
            text_draft = ""
            ans = ""
            tool_count = 0
            for d in api.agent_chat(prompt,
                                    history=history,
                                    model=llm_model,
                                    prompt_name=prompt_template_name,
                                    temperature=temperature,
                                    ):
                try:
                    d = json.loads(d)
                except:
                    pass
                if error_msg := check_error_msg(d):  # check whether error occured
                    st.error(error_msg)
                if chunk := d.get("answer"):
                    text += chunk.replace('。。', ' 。')
                    text_draft = text
                    chat_box.update_msg(text.replace('。。', ' 。'), element_index=0)
                if chunk := d.get("final_answer"):
                    ans += chunk.replace('。。', ' 。')
                    chat_box.update_msg(ans.replace('。。', ' 。'), element_index=1)

                if chunk := d.get("draft"):
                    if text_draft == "":
                        text_draft = ans
                    if text_draft == ans:
                        text_draft += '\n草稿：\n'
                    text_draft += chunk.replace('。。', ' 。')
                    chat_box.update_msg(text_draft.replace('。。', ' 。').replace('\n。', '').
                                        replace('StepInKGInKG', 'StepInKG').
                                        replace('CompleteTriple CompleteTriple', 'CompleteTriple'), element_index=0)
                if chunk := d.get("tools"):
                    text += "\n\n".join(d.get("tools", []))
                    chat_box.update_msg(text.replace('。。', ' 。'), element_index=0)
                    tool_count += 1
                    if tool_count >= max_tool_count:
                        text += '达到最大工具调用限制'
                        chat_box.update_msg(text.replace('。。', ' 。'), element_index=0)
                        break
                    text_draft = text
            chat_box.update_msg(text.replace('。。', ' 。'), element_index=0,
                                streaming=False, title='Thought', expanded=True, state='complete')
            if ans == '':
                ans = '工具调用失败，我将尝试自己回答。'
                st.session_state.flag_agent_fail = True
            if "调用agent工具失败，以下为推理过程:\n\n" in text + ans:
                ans += '\n\n工具调用失败，我将尝试自己回答。'
                st.session_state.flag_agent_fail = True
            chat_box.update_msg(ans.replace('。。', ' 。'), element_index=1, streaming=False)

            if '工具名称: CompleteTriple' in text and '工具状态: 调用成功' in text:

                Question_db = prompt
                KnowledgeTriple_db = str(re_tuple(text.split('工具名称: CompleteTriple')[1].split('工具输入')[1].split('工具输出')[0]))
                ModelCompletion_db = str(re_tuple(text.split('工具名称: CompleteTriple')[1].split('工具输出')[1].split('```')[0].replace('\n', '')))
                tuple_count = max(len(re_tuple(text.split('工具名称: CompleteTriple')[1].split('工具输入')[1].split('工具输出')[0])), 3)

                file_path_kb_unhit = 'res/kb_unhit.csv'
                if os.path.exists(file_path_kb_unhit) == False:
                    df_tuple = pd.DataFrame(data=None, columns=['Question',
                                                                'KnowledgeTriple',
                                                                'ModelCompletion',
                                                                'tuple_count'])
                    df_tuple.to_csv(file_path_kb_unhit, index=False)
                df_tuple = pd.read_csv(file_path_kb_unhit)
                index = len(df_tuple)
                df_tuple.at[index, 'Question'] = Question_db
                df_tuple.at[index, 'KnowledgeTriple'] = KnowledgeTriple_db
                df_tuple.at[index, 'ModelCompletion'] = ModelCompletion_db
                df_tuple.at[index, 'tuple_count'] = tuple_count
                df_tuple.to_csv(file_path_kb_unhit, index=False)

        else:
            print('ERROR')
        if st.session_state.flag_agent_fail:
            st.session_state.flag_agent_fail = False
            chat_box.ai_say("正在思考...")
            text = ""
            message_id = ""
            r = api.chat_chat(prompt,
                              history=history,
                              conversation_id=conversation_id,
                              model=llm_model,
                              prompt_name=prompt_template_name,
                              temperature=temperature)
            for t in r:
                if error_msg := check_error_msg(t):  # check whether error occured
                    st.error(error_msg)
                    break
                text += t.get("text", "")
                chat_box.update_msg(text.replace('。。', ' 。'))
                message_id = t.get("message_id", "")

            metadata = {
                "message_id": message_id,
            }
            chat_box.update_msg(text.replace('。。', ' 。'), streaming=False, metadata=metadata)
        st.session_state.user_input = None


    with st.chat_message("user", avatar='img/avatar_q.png'):
        st.session_state.flag_running = False
        with st.form(key="form"):
            user_input = st.selectbox(
                "Quick question",
                list_question,
                index=0,
                on_change=None,
            )
            submit_clicked = st.form_submit_button("Confirm")

            if submit_clicked and user_input != '':
                print('submit_clicked', user_input)
                st.session_state.user_input = user_input
                st.rerun()

    if st.session_state.get("need_rerun"):
        st.session_state["need_rerun"] = False
        st.rerun()

    with st.sidebar:
        if st.session_state.show_image and st.session_state.image:
            st.rerun()

        cols = st.columns(2)
        if cols[1].button(
                "Empty dialogue",
                use_container_width=True,
        ):
            chat_box.reset_history()
            st.rerun()


