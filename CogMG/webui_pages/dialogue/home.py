import streamlit as st
from webui_pages.utils import *
from streamlit_chatbox import *
import streamlit as st
from PIL import Image


def home_page(api: ApiRequest, is_lite: bool = False):

    st.write('#### Overall')


    st.image(Image.open('img/overall.png'), width=780)
