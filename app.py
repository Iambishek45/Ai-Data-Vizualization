import streamlit as st
import pandas as pd

from modules.data_loader import load_data
from modules.data_profiler import detect_column_types
from modules.visualizer import bar_chart
from modules.insights import generate_insights
from modules.question_parser import parse_question
from modules.preprocess import bin_numeric_column


# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="AI Viz Project", layout="wide")
st.title("AI Viz – Automated Data Visualization System")


# -------------------------------------------------
# FILE UPLOAD
# -------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload CSV or Excel file",
    type=["csv", "xlsx"]
)

if uploaded_file is None:
    st.info("Please upload a dataset to continue.")
    st.stop()


# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
df = load_data(uploaded_file)

if df is None:
    st.error("Unsupported file format.")
    st.stop()


# -------------------------------------------------
# PREVIEW
# -------------------------------------------------
st.subheader("Dataset Preview")
st.dataframe(df.head())


# -------------------------------------------------
# INSIGHTS
# -------------------------------------------------
numeric_cols, categorical_cols = detect_column_types(df)

st.subheader("Dataset Insights")
for insight in generate_insights(df):
    st.write("•", insight)


# -------------------------------------------------
# QUESTION INPUT
# -------------------------------------------------
st.subheader("Ask a Question About Your Data")
st.caption(
    "Examples: compare salary by job ")

question = st.text_input("Enter your question")


# =================================================
# QUESTION HANDLING LOGIC
# =================================================
if question:

    result = parse_question(question, df)
    intent = result.get("intent")

    # ---------------------------------------------
    # BAR CHART: A by B
    # ---------------------------------------------
    if intent == "bar":

        value_col = result.get("value_col")
        group_col = result.get("group_col")

        # Case 1: numeric BY categorical (normal case)
        if value_col in numeric_cols and group_col in categorical_cols:

            grouped = (
                df.groupby(group_col)[value_col]
                .mean()
                .reset_index()
            )

            fig = bar_chart(df, group_col, value_col)
            st.pyplot(fig, use_container_width=False)

            top = grouped.loc[grouped[value_col].idxmax()]
            bottom = grouped.loc[grouped[value_col].idxmin()]

            st.success(
                f"📊 Analysis Result\n\n"
                f"- Highest average {value_col}: **{top[group_col]} ({round(top[value_col], 2)})**\n"
                f"- Lowest average {value_col}: **{bottom[group_col]} ({round(bottom[value_col], 2)})**"
            )

        # Case 2: numeric BY numeric → apply binning
        elif value_col in numeric_cols and group_col in numeric_cols:

            df_binned, new_group_col = bin_numeric_column(df, group_col)

            grouped = (
                df_binned.groupby(new_group_col)[value_col]
                .mean()
                .reset_index()
            )

            fig = bar_chart(df_binned, new_group_col, value_col)
            st.pyplot(fig, use_container_width=False)

            top = grouped.loc[grouped[value_col].idxmax()]

            st.success(
                f"📊 Analysis Result\n\n"
                f"- Highest average {value_col} occurs in the "
                f"**{top[new_group_col]} {group_col} range** "
                f"({round(top[value_col], 2)})"
            )

        else:
            st.warning(
                "Could not clearly identify what to compare and by what."
            )

    # ---------------------------------------------
    # MAX / HIGHEST QUESTIONS
    # ---------------------------------------------
    elif intent == "max":

        num_col = numeric_cols[0]
        cat_col = categorical_cols[0]

        grouped = (
            df.groupby(cat_col)[num_col]
            .mean()
            .reset_index()
        )

        top = grouped.loc[grouped[num_col].idxmax()]

        fig = bar_chart(df, cat_col, num_col)
        st.pyplot(fig, use_container_width=False)

        st.success(
            f"**{top[cat_col]}** has the highest average "
            f"**{num_col}** ({round(top[num_col], 2)})"
        )

    # ---------------------------------------------
    # FALLBACK
    # ---------------------------------------------
    else:
        st.warning(
            "I understood the question textually, but could not map it "
            "clearly to the dataset."
        )
