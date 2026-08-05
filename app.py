import streamlit as st


st.set_page_config(
    page_title="実質賃金分析",
    page_icon="📊",
    layout="wide",
)

st.title("実質賃金・消費者物価指数分析")

st.write("e-Stat APIから取得した公的統計を用いて、物価と賃金の推移を分析します。")