import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Global Student Migration | EDA Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# DATA LOADING & CLEANING
# ============================================================
@st.cache_data
def load_data():
    df = pd.read_csv("global_student_migration.csv")

    # Logical NaN handling (NOT statistical fill - these NaNs are meaningful)
    df["placement_country"] = df["placement_country"].fillna("Not Placed")
    df["placement_company"] = df["placement_company"].fillna("Not Placed")
    df["language_proficiency_test"] = df["language_proficiency_test"].fillna("None")

    return df


df_raw = load_data()

# ============================================================
# SIDEBAR - FILTERS
# ============================================================
st.sidebar.title("🔍 Filters")

if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
    st.session_state.clear()
    st.rerun()

st.sidebar.markdown("---")

origin_sel = st.sidebar.multiselect(
    "Origin Country",
    options=sorted(df_raw["origin_country"].unique()),
    default=[],
    placeholder="All origin countries",
)

dest_sel = st.sidebar.multiselect(
    "Destination Country",
    options=sorted(df_raw["destination_country"].unique()),
    default=[],
    placeholder="All destination countries",
)

field_sel = st.sidebar.multiselect(
    "Field of Study",
    options=sorted(df_raw["field_of_study"].unique()),
    default=[],
    placeholder="All fields",
)

st.sidebar.markdown("**Enrollment Year Range**")
year_range = st.sidebar.slider(
    "Enrollment Year",
    int(df_raw["year_of_enrollment"].min()),
    int(df_raw["year_of_enrollment"].max()),
    (int(df_raw["year_of_enrollment"].min()), int(df_raw["year_of_enrollment"].max())),
    label_visibility="collapsed",
)

st.sidebar.markdown("**GPA / Score Range**")
gpa_range = st.sidebar.slider(
    "GPA",
    float(df_raw["gpa_or_score"].min()),
    float(df_raw["gpa_or_score"].max()),
    (float(df_raw["gpa_or_score"].min()), float(df_raw["gpa_or_score"].max())),
    label_visibility="collapsed",
)

st.sidebar.markdown("**Starting Salary Range (USD)**")
salary_range = st.sidebar.slider(
    "Salary",
    int(df_raw["starting_salary_usd"].min()),
    int(df_raw["starting_salary_usd"].max()),
    (int(df_raw["starting_salary_usd"].min()), int(df_raw["starting_salary_usd"].max())),
    step=1000,
    label_visibility="collapsed",
)

st.sidebar.markdown("**Placement Status**")
placement_sel = st.sidebar.pills(
    "Placement",
    options=["Placed", "Not Placed"],
    selection_mode="multi",
    default=["Placed", "Not Placed"],
    label_visibility="collapsed",
)

st.sidebar.markdown("**Scholarship Received**")
scholarship_sel = st.sidebar.pills(
    "Scholarship",
    options=["Yes", "No"],
    selection_mode="multi",
    default=["Yes", "No"],
    label_visibility="collapsed",
)

st.sidebar.markdown("**Visa Status**")
visa_sel = st.sidebar.multiselect(
    "Visa Status",
    options=sorted(df_raw["visa_status"].unique()),
    default=[],
    placeholder="All visa statuses",
)

# ============================================================
# APPLY FILTERS
# ============================================================
df = df_raw.copy()
if origin_sel:
    df = df[df["origin_country"].isin(origin_sel)]
if dest_sel:
    df = df[df["destination_country"].isin(dest_sel)]
if field_sel:
    df = df[df["field_of_study"].isin(field_sel)]
if visa_sel:
    df = df[df["visa_status"].isin(visa_sel)]

df = df[
    (df["year_of_enrollment"].between(year_range[0], year_range[1]))
    & (df["gpa_or_score"].between(gpa_range[0], gpa_range[1]))
    & (df["starting_salary_usd"].between(salary_range[0], salary_range[1]))
]

if placement_sel:
    df = df[df["placement_status"].isin(placement_sel)]
if scholarship_sel:
    df = df[df["scholarship_received"].isin(scholarship_sel)]

# ============================================================
# HEADER + KPI ROW
# ============================================================
st.title("🎓 Global Student Migration — EDA Dashboard")
st.caption(
    f"Showing **{len(df):,}** of {len(df_raw):,} student records "
    f"based on current filters."
)

if df.empty:
    st.warning("No records match the current filter combination. Please widen your filters.")
    st.stop()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Students", f"{len(df):,}")
placed_pct = (df["placement_status"] == "Placed").mean() * 100
k2.metric("Placement Rate", f"{placed_pct:.1f}%")
avg_salary = df.loc[df["placement_status"] == "Placed", "starting_salary_usd"].mean()
k3.metric("Avg Salary (Placed)", f"${avg_salary:,.0f}" if pd.notna(avg_salary) else "N/A")
avg_gpa = df["gpa_or_score"].mean()
k4.metric("Avg GPA/Score", f"{avg_gpa:.2f}")
scholarship_pct = (df["scholarship_received"] == "Yes").mean() * 100
k5.metric("Scholarship Rate", f"{scholarship_pct:.1f}%")

st.markdown("---")

# ============================================================
# TABS
# ============================================================
tab_overview, tab_uni, tab_bi, tab_multi, tab_geo, tab_trend, tab_insights = st.tabs(
    [
        "📋 Overview",
        "📊 Univariate",
        "🔗 Bivariate",
        "🧩 Multivariate",
        "🌍 Geographic Flow",
        "📈 Trends Over Time",
        "💡 Key Insights",
    ]
)

# ------------------------------------------------------------
# TAB 1: OVERVIEW
# ------------------------------------------------------------
with tab_overview:
    st.subheader("Dataset Snapshot")
    st.dataframe(df.head(20), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Column Data Types**")
        st.dataframe(
            pd.DataFrame(df.dtypes.astype(str), columns=["dtype"]),
            use_container_width=True,
        )
    with c2:
        st.markdown("**Summary Statistics (Numeric Columns)**")
        st.dataframe(df.describe().T, use_container_width=True)

# ------------------------------------------------------------
# TAB 2: UNIVARIATE
# ------------------------------------------------------------
with tab_uni:
    st.subheader("Single Variable Distributions")

    metric_choice = st.pills(
        "Choose a categorical variable to explore",
        options=[
            "Origin Country",
            "Destination Country",
            "Field of Study",
            "Enrollment Reason",
            "Visa Status",
            "Post-Graduation Visa",
            "Language Proficiency Test",
        ],
        default="Origin Country",
    )

    col_map = {
        "Origin Country": "origin_country",
        "Destination Country": "destination_country",
        "Field of Study": "field_of_study",
        "Enrollment Reason": "enrollment_reason",
        "Visa Status": "visa_status",
        "Post-Graduation Visa": "post_graduation_visa",
        "Language Proficiency Test": "language_proficiency_test",
    }

    top_n = st.slider("Show top N categories", 5, 20, 10)

    if metric_choice:
        col = col_map[metric_choice]
        counts = df[col].value_counts().head(top_n).reset_index()
        counts.columns = [metric_choice, "Count"]
        fig = px.bar(
            counts,
            x="Count",
            y=metric_choice,
            orientation="h",
            title=f"Top {top_n} — {metric_choice} (by number of students)",
            text="Count",
            color="Count",
            color_continuous_scale="Blues",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="Number of Students")
        st.plotly_chart(fig, use_container_width=True)
        top_cat = counts.iloc[0][metric_choice]
        top_val = counts.iloc[0]["Count"]
        st.info(f"📌 **Insight:** '{top_cat}' is the most common {metric_choice.lower()}, with {top_val} students ({top_val/len(df)*100:.1f}% of filtered data).")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Scholarship Received**")
        sc = df["scholarship_received"].value_counts().reset_index()
        sc.columns = ["Scholarship", "Count"]
        fig = px.pie(sc, names="Scholarship", values="Count", title="Scholarship Received", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("**Placement Status**")
        ps = df["placement_status"].value_counts().reset_index()
        ps.columns = ["Status", "Count"]
        fig = px.pie(ps, names="Status", values="Count", title="Placement Status", hole=0.4,
                     color="Status", color_discrete_map={"Placed": "#2E8B57", "Not Placed": "#CD5C5C"})
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(df, x="gpa_or_score", nbins=30, title="Distribution of GPA / Score",
                            labels={"gpa_or_score": "GPA / Score"}, color_discrete_sequence=["#4C78A8"])
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        placed_only = df[df["placement_status"] == "Placed"]
        fig = px.histogram(placed_only, x="starting_salary_usd", nbins=30,
                            title="Distribution of Starting Salary (Placed Students)",
                            labels={"starting_salary_usd": "Starting Salary (USD)"},
                            color_discrete_sequence=["#F58518"])
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"📌 Salary distribution skew: {'right-skewed (few high earners)' if placed_only['starting_salary_usd'].skew() > 0.5 else 'roughly symmetric'} "
                   f"(skewness = {placed_only['starting_salary_usd'].skew():.2f})")

    st.markdown("**Test Scores by Test Type**")
    test_df = df[df["language_proficiency_test"] != "None"]
    fig = px.box(test_df, x="language_proficiency_test", y="test_score",
                 title="Test Score Spread by Test Type", points="outliers",
                 labels={"language_proficiency_test": "Test Type", "test_score": "Score"})
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# TAB 3: BIVARIATE
# ------------------------------------------------------------
with tab_bi:
    st.subheader("Relationships Between Two Variables")

    analysis_choice = st.radio(
        "Choose a bivariate analysis",
        [
            "Field of Study vs Salary",
            "Scholarship vs Placement",
            "Field of Study vs Placement Rate",
            "GPA vs Salary",
            "Destination Country vs Avg Salary",
            "Enrollment Reason vs Placement",
        ],
        horizontal=True,
    )

    if analysis_choice == "Field of Study vs Salary":
        placed = df[df["placement_status"] == "Placed"]
        fig = px.box(placed, x="field_of_study", y="starting_salary_usd", color="field_of_study",
                     title="Starting Salary Distribution by Field of Study",
                     labels={"field_of_study": "Field of Study", "starting_salary_usd": "Starting Salary (USD)"})
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        best_field = placed.groupby("field_of_study")["starting_salary_usd"].mean().idxmax()
        best_val = placed.groupby("field_of_study")["starting_salary_usd"].mean().max()
        st.info(f"📌 **Insight:** '{best_field}' graduates earn the highest average starting salary (${best_val:,.0f}).")

    elif analysis_choice == "Scholarship vs Placement":
        cross = pd.crosstab(df["scholarship_received"], df["placement_status"], normalize="index") * 100
        cross = cross.reset_index().melt(id_vars="scholarship_received", var_name="Placement Status", value_name="Percent")
        fig = px.bar(cross, x="scholarship_received", y="Percent", color="Placement Status", barmode="group",
                     title="Placement Rate by Scholarship Status (%)",
                     labels={"scholarship_received": "Scholarship Received"})
        st.plotly_chart(fig, use_container_width=True)
        rate_yes = (df[df["scholarship_received"] == "Yes"]["placement_status"] == "Placed").mean() * 100
        rate_no = (df[df["scholarship_received"] == "No"]["placement_status"] == "Placed").mean() * 100
        st.info(f"📌 **Insight:** Students WITH scholarship have a {rate_yes:.1f}% placement rate vs {rate_no:.1f}% for those without.")

    elif analysis_choice == "Field of Study vs Placement Rate":
        rate = df.groupby("field_of_study")["placement_status"].apply(lambda x: (x == "Placed").mean() * 100).reset_index()
        rate.columns = ["Field of Study", "Placement Rate (%)"]
        rate = rate.sort_values("Placement Rate (%)", ascending=False)
        fig = px.bar(rate, x="Field of Study", y="Placement Rate (%)", color="Placement Rate (%)",
                     title="Placement Rate (%) by Field of Study", color_continuous_scale="Teal")
        st.plotly_chart(fig, use_container_width=True)
        st.info(f"📌 **Insight:** '{rate.iloc[0]['Field of Study']}' has the highest placement rate at {rate.iloc[0]['Placement Rate (%)']:.1f}%.")

    elif analysis_choice == "GPA vs Salary":
        placed = df[df["placement_status"] == "Placed"]
        fig = px.scatter(placed, x="gpa_or_score", y="starting_salary_usd", color="field_of_study",
                          title="GPA vs Starting Salary", trendline="ols",
                          labels={"gpa_or_score": "GPA / Score", "starting_salary_usd": "Starting Salary (USD)"})
        st.plotly_chart(fig, use_container_width=True)
        corr = placed["gpa_or_score"].corr(placed["starting_salary_usd"])
        st.info(f"📌 **Insight:** Correlation between GPA and salary is {corr:.3f} — "
                f"{'a weak/negligible relationship' if abs(corr) < 0.2 else 'a noticeable relationship'}.")

    elif analysis_choice == "Destination Country vs Avg Salary":
        placed = df[df["placement_status"] == "Placed"]
        avg = placed.groupby("destination_country")["starting_salary_usd"].mean().reset_index().sort_values("starting_salary_usd", ascending=False)
        fig = px.bar(avg, x="destination_country", y="starting_salary_usd", color="starting_salary_usd",
                     title="Average Starting Salary by Destination Country", color_continuous_scale="Sunset",
                     labels={"destination_country": "Destination Country", "starting_salary_usd": "Avg Starting Salary (USD)"})
        st.plotly_chart(fig, use_container_width=True)
        st.info(f"📌 **Insight:** {avg.iloc[0]['destination_country']} offers the highest average starting salary (${avg.iloc[0]['starting_salary_usd']:,.0f}).")

    elif analysis_choice == "Enrollment Reason vs Placement":
        cross = pd.crosstab(df["enrollment_reason"], df["placement_status"], normalize="index") * 100
        cross = cross.reset_index().melt(id_vars="enrollment_reason", var_name="Placement Status", value_name="Percent")
        fig = px.bar(cross, x="enrollment_reason", y="Percent", color="Placement Status", barmode="group",
                     title="Placement Rate by Enrollment Reason (%)", labels={"enrollment_reason": "Enrollment Reason"})
        st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# TAB 4: MULTIVARIATE
# ------------------------------------------------------------
with tab_multi:
    st.subheader("Multi-Variable Analysis")

    st.markdown("**Correlation Heatmap (Numeric Columns)**")
    numeric_cols = ["year_of_enrollment", "graduation_year", "starting_salary_usd", "gpa_or_score", "test_score"]
    corr_matrix = df[numeric_cols].corr()
    fig = px.imshow(corr_matrix, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                     title="Correlation Heatmap of Numeric Variables")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("**Field of Study × Destination Country → Avg Salary (Heatmap)**")
    placed = df[df["placement_status"] == "Placed"]
    pivot = placed.pivot_table(index="field_of_study", columns="destination_country",
                                values="starting_salary_usd", aggfunc="mean")
    fig = px.imshow(pivot, text_auto=".0f", color_continuous_scale="Viridis", aspect="auto",
                     title="Avg Starting Salary: Field of Study vs Destination Country",
                     labels=dict(color="Avg Salary (USD)"))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("**Scholarship × Field of Study × Placement Status**")
    grp = df.groupby(["field_of_study", "scholarship_received", "placement_status"]).size().reset_index(name="Count")
    fig = px.bar(grp, x="field_of_study", y="Count", color="placement_status",
                 facet_col="scholarship_received", barmode="stack",
                 title="Placement Outcomes by Field of Study, split by Scholarship",
                 labels={"field_of_study": "Field of Study"})
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# TAB 5: GEOGRAPHIC FLOW
# ------------------------------------------------------------
with tab_geo:
    st.subheader("Migration Flow Analysis")

    top_n_flow = st.slider("Number of top origin→destination pairs to show", 5, 25, 15, key="flow_slider")

    flow = df.groupby(["origin_country", "destination_country"]).size().reset_index(name="Count")
    flow = flow.sort_values("Count", ascending=False).head(top_n_flow)

    fig = px.bar(flow, x="Count", y=[f"{o} → {d}" for o, d in zip(flow["origin_country"], flow["destination_country"])],
                 orientation="h", title=f"Top {top_n_flow} Origin → Destination Country Pairs",
                 labels={"y": "Migration Route", "Count": "Number of Students"}, color="Count",
                 color_continuous_scale="Plasma")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)
    st.info(f"📌 **Insight:** The busiest migration route is **{flow.iloc[0]['origin_country']} → {flow.iloc[0]['destination_country']}** "
            f"with {flow.iloc[0]['Count']} students.")

    st.markdown("---")
    st.markdown("**Sankey Diagram: Origin → Destination Flow**")
    top_flow_sankey = df.groupby(["origin_country", "destination_country"]).size().reset_index(name="Count")
    top_flow_sankey = top_flow_sankey.sort_values("Count", ascending=False).head(20)

    origins = list(top_flow_sankey["origin_country"].unique())
    dests = list(top_flow_sankey["destination_country"].unique())
    all_nodes = origins + dests
    node_idx = {name: i for i, name in enumerate(all_nodes)}

    sankey_fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15, thickness=20,
            label=all_nodes,
            color=["#4C78A8"] * len(origins) + ["#F58518"] * len(dests),
        ),
        link=dict(
            source=[node_idx[o] for o in top_flow_sankey["origin_country"]],
            target=[node_idx[d] for d in top_flow_sankey["destination_country"]],
            value=top_flow_sankey["Count"],
        )
    )])
    sankey_fig.update_layout(title_text="Student Migration Flow (Origin → Destination)", font_size=11)
    st.plotly_chart(sankey_fig, use_container_width=True)

    st.markdown("---")
    st.markdown("**Net Brain Drain / Gain by Country**")
    origin_counts = df["origin_country"].value_counts()
    dest_counts = df["destination_country"].value_counts()
    net = (dest_counts.reindex(set(origin_counts.index) | set(dest_counts.index), fill_value=0)
           - origin_counts.reindex(set(origin_counts.index) | set(dest_counts.index), fill_value=0))
    net = net.reset_index()
    net.columns = ["Country", "Net Students (Incoming - Outgoing)"]
    net = net.sort_values("Net Students (Incoming - Outgoing)", ascending=False)
    fig = px.bar(net, x="Country", y="Net Students (Incoming - Outgoing)",
                 color="Net Students (Incoming - Outgoing)", color_continuous_scale="RdYlGn",
                 title="Net Student Flow by Country (Positive = Net Gain / Brain Gain)")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("**Do Students Stay in the Destination Country to Work?**")
    placed = df[df["placement_status"] == "Placed"].copy()
    placed["stayed_abroad"] = placed["destination_country"] == placed["placement_country"]
    stay_pct = placed["stayed_abroad"].mean() * 100
    st.metric("Stayed in Destination Country for Work", f"{stay_pct:.1f}%")
    fig = px.pie(placed, names="stayed_abroad", title="Stayed in Destination Country vs Moved Elsewhere",
                 color="stayed_abroad", color_discrete_map={True: "#2E8B57", False: "#CD5C5C"})
    fig.for_each_trace(lambda t: t.update(labels=["Stayed" if v else "Moved Elsewhere" for v in t.labels]))
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# TAB 6: TRENDS OVER TIME
# ------------------------------------------------------------
with tab_trend:
    st.subheader("Trends Over Time")

    trend_choice = st.pills(
        "Choose a trend to view",
        options=["Enrollment Count", "Scholarship Rate", "Avg Salary", "Placement Rate"],
        default="Enrollment Count",
    )

    if trend_choice == "Enrollment Count":
        trend = df.groupby("year_of_enrollment").size().reset_index(name="Students Enrolled")
        fig = px.line(trend, x="year_of_enrollment", y="Students Enrolled", markers=True,
                      title="Number of Students Enrolled per Year")
        st.plotly_chart(fig, use_container_width=True)

    elif trend_choice == "Scholarship Rate":
        trend = df.groupby("year_of_enrollment")["scholarship_received"].apply(lambda x: (x == "Yes").mean() * 100).reset_index()
        trend.columns = ["Year", "Scholarship Rate (%)"]
        fig = px.line(trend, x="Year", y="Scholarship Rate (%)", markers=True,
                      title="Scholarship Rate by Enrollment Year")
        st.plotly_chart(fig, use_container_width=True)

    elif trend_choice == "Avg Salary":
        placed = df[df["placement_status"] == "Placed"]
        trend = placed.groupby("graduation_year")["starting_salary_usd"].mean().reset_index()
        fig = px.line(trend, x="graduation_year", y="starting_salary_usd", markers=True,
                      title="Average Starting Salary by Graduation Year",
                      labels={"starting_salary_usd": "Avg Starting Salary (USD)", "graduation_year": "Graduation Year"})
        st.plotly_chart(fig, use_container_width=True)

    elif trend_choice == "Placement Rate":
        trend = df.groupby("graduation_year")["placement_status"].apply(lambda x: (x == "Placed").mean() * 100).reset_index()
        trend.columns = ["Graduation Year", "Placement Rate (%)"]
        fig = px.line(trend, x="Graduation Year", y="Placement Rate (%)", markers=True,
                      title="Placement Rate by Graduation Year")
        st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# TAB 7: KEY INSIGHTS
# ------------------------------------------------------------
with tab_insights:
    st.subheader("💡 Auto-Generated Key Insights")
    st.caption("These update automatically based on your current filter selection.")

    placed = df[df["placement_status"] == "Placed"]

    insights = []

    top_origin = df["origin_country"].value_counts().idxmax()
    insights.append(f"**Top origin country:** {top_origin} ({df['origin_country'].value_counts().max()} students)")

    top_dest = df["destination_country"].value_counts().idxmax()
    insights.append(f"**Top destination country:** {top_dest} ({df['destination_country'].value_counts().max()} students)")

    top_field = df["field_of_study"].value_counts().idxmax()
    insights.append(f"**Most popular field of study:** {top_field}")

    if not placed.empty:
        best_paying_field = placed.groupby("field_of_study")["starting_salary_usd"].mean().idxmax()
        insights.append(f"**Highest paying field:** {best_paying_field} "
                         f"(avg ${placed.groupby('field_of_study')['starting_salary_usd'].mean().max():,.0f})")

        best_dest_salary = placed.groupby("destination_country")["starting_salary_usd"].mean().idxmax()
        insights.append(f"**Best paying destination country:** {best_dest_salary} "
                         f"(avg ${placed.groupby('destination_country')['starting_salary_usd'].mean().max():,.0f})")

    overall_placement = (df["placement_status"] == "Placed").mean() * 100
    insights.append(f"**Overall placement rate:** {overall_placement:.1f}%")

    rate_yes = (df[df["scholarship_received"] == "Yes"]["placement_status"] == "Placed").mean() * 100 if (df["scholarship_received"] == "Yes").any() else float("nan")
    rate_no = (df[df["scholarship_received"] == "No"]["placement_status"] == "Placed").mean() * 100 if (df["scholarship_received"] == "No").any() else float("nan")
    insights.append(f"**Scholarship impact:** Placement rate is {rate_yes:.1f}% with scholarship vs {rate_no:.1f}% without")

    flow = df.groupby(["origin_country", "destination_country"]).size().reset_index(name="Count").sort_values("Count", ascending=False)
    if not flow.empty:
        insights.append(f"**Busiest migration route:** {flow.iloc[0]['origin_country']} → {flow.iloc[0]['destination_country']} "
                         f"({flow.iloc[0]['Count']} students)")

    if not placed.empty:
        placed_stay = placed.copy()
        placed_stay["stayed"] = placed_stay["destination_country"] == placed_stay["placement_country"]
        insights.append(f"**Stay-abroad rate:** {placed_stay['stayed'].mean()*100:.1f}% of placed students work in their study destination country")

    scholarship_pct_overall = (df["scholarship_received"] == "Yes").mean() * 100
    insights.append(f"**Scholarship rate:** {scholarship_pct_overall:.1f}% of students received a scholarship")

    for i, txt in enumerate(insights, 1):
        st.markdown(f"{i}. {txt}")

    st.markdown("---")
    st.markdown("### 📥 Export Filtered Data")
    st.download_button(
        "Download Filtered Data as CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_student_migration.csv",
        mime="text/csv",
    )
