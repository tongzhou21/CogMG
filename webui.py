import streamlit as st
from webui_pages.utils import *
from streamlit_option_menu import option_menu
from webui_pages.dialogue.dialogue import dialogue_page, chat_box
from webui_pages.dialogue.home import home_page
from webui_pages.knowledge_base.knowledge_base import knowledge_base_page
# from webui_pages.knowledge_base.knowledge_base_raw import knowledge_base_page
import extra_streamlit_components as stx
from PIL import Image
import os
import sys
from server.utils import api_address
import base64

api = ApiRequest(base_url=api_address())

if __name__ == "__main__":
    is_lite = "lite" in sys.argv

    st.set_page_config(page_title="CogMG",
                       page_icon=os.path.join("img", "logo_head.png"),
                       layout="wide", initial_sidebar_state="expanded",)

    hide_streamlit_style = """
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    footer:after {
        content:'Made by CASIA'; 
        visibility: visible;
        display: block;
        position: relative;
    #background-color: red;
    padding: 0px;
    top: 0px;
    }
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    hide_streamlit_style = """
    <style>
        #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}
    </style>

    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    bottom_style = """
    <style>
    #root > div:nth-child(1) > div.withScreencast > div > div > header {
        bottom: 0px;
        height: 1rem;
        top: unset;
    }
    </style>
    """
    st.markdown(bottom_style, unsafe_allow_html=True)


    def add_logo(png_file):
        def get_base64_of_bin_file(png_file):
            with open(png_file, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()

        binary_string = get_base64_of_bin_file(png_file)
        st.markdown(
            """
            <style>
                [data-testid="stSidebar"] {
                    background-image: url("data:image/png;base64,%s");
                    background-repeat: no-repeat;
                    padding-top: 20px;
                    background-position: 40px 10px;
                    overflow: hidden;
                    background-size: 297px 110px;
                }
            </style>
            """ % (binary_string),
            unsafe_allow_html=True,
        )
    add_logo("img/cogmg.png")

    try:
        pages = {
            "Home": {
                "icon": "house",
                "func": home_page,
            },
            "Question Answer": {
                "icon": "chat",
                "func": dialogue_page,
            },
            "Knowledge Management": {
                "icon": "hdd-stack",
                "func": knowledge_base_page,
            },
        }
    except:
        st.rerun()

    with st.sidebar:
        st.caption(
            f"""<p align="right"> powered by CASIA </p>""",
            unsafe_allow_html=True,
        )
        options = list(pages)
        icons = [x["icon"] for x in pages.values()]

        default_index = 0
        selected_page = option_menu(
            "",
            options=options,
            icons=icons,
            default_index=default_index,
        )

    if selected_page in pages:
        pages[selected_page]["func"](api=api, is_lite=is_lite)

