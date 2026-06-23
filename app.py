import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.title("Feedback Analyzer - Stage 3")

YES_NO_MAYBE = ["Yes", "No", "Maybe"]

HELPFULNESS_5 = [
    "Not Attended",
    "Not at All Helpful",
    "Not Very Helpful",
    "Somewhat Helpful",
    "Very Helpful",
    "Extremely Helpful"
]

RATING_5 = [
    "Bad",
    "Poor",
    "Average",
    "Good",
    "Excellent"
]

STAR_RATING_5 = [
    "Very Poor",
    "Poor",
    "Average",
    "Good",
    "Excellent"
]

DEFAULT_EXCLUDE = [
    "16. Highlight the activities that have helped you to improve.\n(List specific activities and how they benefited you.)",
    " 18. What areas do you think need improvement?\n(Suggestions for betterment of activities, mentoring, or the program.)",
    "19.  Do you have any additional comments or suggestions?",
    "21. Any other feedback or suggestions ?",
    "Which news channel(s) do your parents generally watch or recommend in the community?",
    "Which newspaper(s) come to your house or community?",
    "Field Mentor Name",
    "Mentor Name",
    "Timestamp"
]


def clean_response(value):
    if pd.isna(value):
        return None
    return str(value).strip()


def normalize_response(value):
    
    if pd.isna(value):
        return None

    # Convert 1.0 -> 1, 2.0 -> 2, etc.
    if isinstance(value, float) and value.is_integer():
        value = int(value)

    response = str(value).strip()

    # Also catches text values like "1.0"
    if response.endswith(".0"):
        response = response[:-2]

    response_lower = response.lower().strip()

    mapping = {
        "yes": "Yes",
        "no": "No",
        "maybe": "Maybe",

        "not attended": "Not Attended",

        "1 - not at all helpful": "Not at All Helpful",
        "not at all helpful": "Not at All Helpful",

        "2 - not very helpful": "Not Very Helpful",
        "not very helpful": "Not Very Helpful",

        "3 - somewhat helpful": "Somewhat Helpful",
        "somewhat helpful": "Somewhat Helpful",

        "4 - very helpful": "Very Helpful",
        "very helpful": "Very Helpful",

        "5 - extremely helpful": "Extremely Helpful",
        "extremely helpful": "Extremely Helpful",

        "bad": "Bad",
        "poor": "Poor",
        "average": "Average",
        "good": "Good",
        "excellent": "Excellent",

        "1★ very poor": "Very Poor",
        "1* very poor": "Very Poor",
        "very poor": "Very Poor",

        "2★ poor": "Poor",
        "2* poor": "Poor",

        "3★ average": "Average",
        "3* average": "Average",

        "4★ good": "Good",
        "4* good": "Good",

        "5★ excellent": "Excellent",
        "5* excellent": "Excellent"
    }

    return mapping.get(response_lower, response)


def count_question(series, fixed_categories=None):
    responses = series.dropna().apply(normalize_response)

    if fixed_categories:
        counts = {cat: 0 for cat in fixed_categories}

        for response in responses:
            if response in counts:
                counts[response] += 1

        return pd.DataFrame({
            "Response": list(counts.keys()),
            "Count": list(counts.values())
        })

    counts = responses.value_counts()

    return pd.DataFrame({
        "Response": counts.index,
        "Count": counts.values
    })


def add_percentages(df):
    total = df["Count"].sum()

    if total == 0:
        df["Percentage"] = 0
    else:
        df["Percentage"] = (df["Count"] / total * 100).round(1)

    return df


def detect_question_type(series):
    values = set(series.dropna().apply(normalize_response).dropna().str.lower())

    yes_no_maybe_set = {x.lower() for x in YES_NO_MAYBE}
    helpfulness_set = {x.lower() for x in HELPFULNESS_5}
    rating_set = {x.lower() for x in RATING_5}
    star_rating_set = {x.lower() for x in STAR_RATING_5}

    if values and values.issubset(yes_no_maybe_set):
        return "yes_no_maybe"

    if values and values.issubset(helpfulness_set):
        return "helpfulness_5"

    if values and values.issubset(rating_set):
        return "rating_5"

    if values and values.issubset(star_rating_set):
        return "star_rating_5"

    return "general"


def analyze_question(df, question):
    question_type = detect_question_type(df[question])

    if question_type == "yes_no_maybe":
        result = count_question(df[question], YES_NO_MAYBE)

    elif question_type == "helpfulness_5":
        result = count_question(df[question], HELPFULNESS_5)

    elif question_type == "rating_5":
        result = count_question(df[question], RATING_5)

    elif question_type == "star_rating_5":
        result = count_question(df[question], STAR_RATING_5)

    else:
        result = count_question(df[question])

    result = add_percentages(result)
    return result, question_type


def plot_bar(df, question):
    fig, ax = plt.subplots(figsize=(10, 5))

    bars = ax.bar(df["Response"], df["Count"])

    ax.set_title(question)
    ax.set_ylabel("Count")
    ax.set_xlabel("Response")

    plt.xticks(rotation=45, ha="right")

    for bar, count, pct in zip(bars, df["Count"], df["Percentage"]):
        height = bar.get_height()

        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{int(count)}\n({pct}%)",
            ha="center",
            va="bottom",
            fontsize=9
        )

    plt.tight_layout()
    return fig


def plot_pie(df, question):
    fig, ax = plt.subplots(figsize=(7, 7))

    nonzero_df = df[df["Count"] > 0]

    ax.pie(
        nonzero_df["Count"],
        labels=[
            f"{row.Response}: {row.Count} ({row.Percentage}%)"
            for row in nonzero_df.itertuples()
        ],
        startangle=90
    )

    ax.set_title(question)
    plt.tight_layout()
    return fig


def compare_results(result1, result2, year1_label, year2_label):
    comparison = pd.merge(
        result1,
        result2,
        on="Response",
        how="outer",
        suffixes=(f"_{year1_label}", f"_{year2_label}")
    ).fillna(0)

    count_col_1 = f"Count_{year1_label}"
    count_col_2 = f"Count_{year2_label}"

    pct_col_1 = f"Percentage_{year1_label}"
    pct_col_2 = f"Percentage_{year2_label}"

    comparison[count_col_1] = comparison[count_col_1].astype(int)
    comparison[count_col_2] = comparison[count_col_2].astype(int)

    comparison["Count Change"] = comparison[count_col_2] - comparison[count_col_1]
    comparison["Percentage Point Change"] = (
        comparison[pct_col_2] - comparison[pct_col_1]
    ).round(1)

    return comparison


def plot_comparison_bar(comparison, question, year1_label, year2_label):
    count_col_1 = f"Count_{year1_label}"
    count_col_2 = f"Count_{year2_label}"

    x = range(len(comparison))
    width = 0.35

    fig, ax = plt.subplots(figsize=(11, 5))

    bars1 = ax.bar(
        [i - width / 2 for i in x],
        comparison[count_col_1],
        width,
        label=year1_label
    )

    bars2 = ax.bar(
        [i + width / 2 for i in x],
        comparison[count_col_2],
        width,
        label=year2_label
    )

    ax.set_title(question)
    ax.set_ylabel("Count")
    ax.set_xlabel("Response")
    ax.set_xticks(list(x))
    ax.set_xticklabels(comparison["Response"], rotation=45, ha="right")
    ax.legend()

    for bar in bars1:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            str(int(height)),
            ha="center",
            va="bottom",
            fontsize=8
        )

    for bar in bars2:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            str(int(height)),
            ha="center",
            va="bottom",
            fontsize=8
        )

    plt.tight_layout()
    return fig


def fig_to_png_download(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=300, bbox_inches="tight")
    buffer.seek(0)
    return buffer


mode = st.radio(
    "Select mode",
    ["Analyze One Excel", "Compare Two Excels"],
    horizontal=True
)

if mode == "Analyze One Excel":
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)

        st.subheader("Duplicate Removal")

        name_column = st.selectbox(
            "Select student name column for duplicate removal",
            ["None"] + list(df.columns)
        )

        if name_column != "None":
            before = len(df)
            df = df.drop_duplicates(subset=[name_column], keep="first")
            after = len(df)

            st.info(
                f"Duplicate removal applied: {before - after} duplicate rows removed. "
                f"Final responses counted: {after}"
            )

        st.subheader("Preview of Uploaded Data")
        st.dataframe(df.head())

        valid_default_exclude = [
            col for col in DEFAULT_EXCLUDE if col in df.columns
        ]

        columns_to_exclude = st.multiselect(
            "Select columns you DO NOT want to analyze",
            list(df.columns),
            default=valid_default_exclude
        )

        questions_to_analyze = [
            col for col in df.columns if col not in columns_to_exclude
        ]

        st.write(f"Questions selected for analysis: **{len(questions_to_analyze)}**")

        graph_type = st.radio(
            "Select graph type",
            ["Bar Chart", "Pie Chart"],
            horizontal=True
        )

        st.subheader("Single Question Analysis")

        selected_question = st.selectbox(
            "Select one question/column",
            questions_to_analyze
        )

        result, question_type = analyze_question(df, selected_question)

        st.write("Numerical Data")
        st.dataframe(result)

        if graph_type == "Pie Chart":
            fig = plot_pie(result, selected_question)
        else:
            fig = plot_bar(result, selected_question)

        st.pyplot(fig)

        png_file = fig_to_png_download(fig)

        st.download_button(
            "Download this graph as PNG",
            png_file,
            file_name="selected_question_graph.png",
            mime="image/png"
        )

        st.subheader("Analyze All Selected Questions")

        if st.button("Generate All Tables and Graphs"):
            all_results = []

            for question in questions_to_analyze:
                st.markdown("---")
                st.subheader(question)

                result, question_type = analyze_question(df, question)

                st.write("Numerical Data")
                st.dataframe(result)

                temp_result = result.copy()
                temp_result.insert(0, "Question", question)

                all_results.append(temp_result)

                if graph_type == "Pie Chart":
                    fig = plot_pie(result, question)
                else:
                    fig = plot_bar(result, question)

                st.pyplot(fig)

            if all_results:
                final_summary = pd.concat(all_results, ignore_index=True)

                st.subheader("Full Numerical Summary")
                st.dataframe(final_summary)

                csv = final_summary.to_csv(index=False).encode("utf-8")

                st.download_button(
                    "Download full numerical analysis as CSV",
                    csv,
                    "full_feedback_analysis.csv",
                    "text/csv"
                )


if mode == "Compare Two Excels":
    year1_label = st.text_input("Enter label for Excel 1", "2024")
    year2_label = st.text_input("Enter label for Excel 2", "2025")

    file1 = st.file_uploader("Upload Excel 1", type=["xlsx"], key="file1")
    file2 = st.file_uploader("Upload Excel 2", type=["xlsx"], key="file2")

    if file1 and file2:
        df1 = pd.read_excel(file1)
        df2 = pd.read_excel(file2)

        st.subheader("Duplicate Removal")

        name_column_1 = st.selectbox(
            "Select student name column for Excel 1 duplicate removal",
            ["None"] + list(df1.columns),
            key="name1"
        )

        if name_column_1 != "None":
            before = len(df1)
            df1 = df1.drop_duplicates(subset=[name_column_1], keep="first")
            after = len(df1)
            st.info(f"Excel 1: {before - after} duplicate rows removed. Final rows: {after}")

        name_column_2 = st.selectbox(
            "Select student name column for Excel 2 duplicate removal",
            ["None"] + list(df2.columns),
            key="name2"
        )

        if name_column_2 != "None":
            before = len(df2)
            df2 = df2.drop_duplicates(subset=[name_column_2], keep="first")
            after = len(df2)
            st.info(f"Excel 2: {before - after} duplicate rows removed. Final rows: {after}")

        common_columns = [col for col in df1.columns if col in df2.columns]

        valid_default_exclude = [
            col for col in DEFAULT_EXCLUDE if col in common_columns
        ]

        columns_to_exclude = st.multiselect(
            "Select columns you DO NOT want to compare",
            common_columns,
            default=valid_default_exclude
        )

        questions_to_compare = [
            col for col in common_columns if col not in columns_to_exclude
        ]

        st.write(f"Questions available for comparison: **{len(questions_to_compare)}**")

        selected_question = st.selectbox(
            "Select one question to compare",
            questions_to_compare
        )

        result1, question_type_1 = analyze_question(df1, selected_question)
        result2, question_type_2 = analyze_question(df2, selected_question)

        comparison = compare_results(result1, result2, year1_label, year2_label)

        st.subheader("Comparison Table")
        st.dataframe(comparison)

        fig = plot_comparison_bar(comparison, selected_question, year1_label, year2_label)

        st.subheader("Comparison Graph")
        st.pyplot(fig)

        png_file = fig_to_png_download(fig)

        st.download_button(
            "Download comparison graph as PNG",
            png_file,
            file_name="comparison_graph.png",
            mime="image/png"
        )

        csv = comparison.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download comparison table as CSV",
            csv,
            "comparison_table.csv",
            "text/csv"
        )

        st.subheader("Compare All Selected Questions")

        if st.button("Generate All Comparison Tables and Graphs"):
            all_comparisons = []

            for question in questions_to_compare:
                st.markdown("---")
                st.subheader(question)

                result1, question_type_1 = analyze_question(df1, question)
                result2, question_type_2 = analyze_question(df2, question)

                comparison = compare_results(result1, result2, year1_label, year2_label)
                comparison.insert(0, "Question", question)

                all_comparisons.append(comparison)

                st.dataframe(comparison)

                fig = plot_comparison_bar(
                    comparison,
                    question,
                    year1_label,
                    year2_label
                )

                st.pyplot(fig)

            if all_comparisons:
                final_comparison_summary = pd.concat(all_comparisons, ignore_index=True)

                st.subheader("Full Comparison Summary")
                st.dataframe(final_comparison_summary)

                csv = final_comparison_summary.to_csv(index=False).encode("utf-8")

                st.download_button(
                    "Download full comparison summary as CSV",
                    csv,
                    "full_comparison_summary.csv",
                    "text/csv"
                )