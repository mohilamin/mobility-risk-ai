from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import DATA_PROCESSED, POWERBI_EXPORTS

st.set_page_config(page_title="Mobility Risk AI", layout="wide")
st.title("Mobility Risk AI")
st.caption("Commercial mobility insurance underwriting and portfolio analytics prototype")


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    risk = pd.read_csv(DATA_PROCESSED / "fleet_monthly_risk_scores.csv")
    portfolio = pd.read_csv(POWERBI_EXPORTS / "portfolio_dashboard.csv")
    underwriting = pd.read_csv(POWERBI_EXPORTS / "underwriting_account_summary.csv")
    claims = pd.read_csv(POWERBI_EXPORTS / "claims_dashboard.csv")
    importance = pd.read_csv(DATA_PROCESSED / "ml_feature_importance.csv")
    return risk, portfolio, underwriting, claims, importance


risk, portfolio, underwriting, claims, importance = load_data()

client_types = st.sidebar.multiselect("Client type", sorted(risk["client_type"].unique()), default=sorted(risk["client_type"].unique()))
states = st.sidebar.multiselect("State", sorted(risk["primary_state"].unique()), default=sorted(risk["primary_state"].unique()))
tiers = st.sidebar.multiselect("Risk tier", sorted(risk["risk_tier"].unique()), default=sorted(risk["risk_tier"].unique()))
levels = st.sidebar.multiselect("Autonomy level", sorted(risk["autonomy_level"].unique()), default=sorted(risk["autonomy_level"].unique()))

filtered = risk.loc[risk["client_type"].isin(client_types) & risk["primary_state"].isin(states) & risk["risk_tier"].isin(tiers) & risk["autonomy_level"].isin(levels)]

tabs = st.tabs(["Executive Portfolio", "Underwriting Intelligence", "Autonomous Risk", "Claims & Exposure", "ML Insights", "Data Quality"])

with tabs[0]:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Earned Premium", f"${filtered.groupby('fleet_id')['earned_premium'].first().sum():,.0f}")
    c2.metric("Incurred Loss", f"${filtered['incurred_loss'].sum():,.0f}")
    c3.metric("Loss Ratio", f"{filtered['incurred_loss'].sum() / filtered.groupby('fleet_id')['earned_premium'].first().sum():.1%}")
    c4.metric("High/Critical Fleet-Months", int(filtered["risk_tier"].isin(["High", "Critical"]).sum()))
    st.plotly_chart(px.line(filtered.groupby("month", as_index=False)["risk_score"].mean(), x="month", y="risk_score", title="Average Risk Score Trend"), use_container_width=True)
    st.plotly_chart(px.bar(portfolio, x="client_type", y="loss_ratio", color="primary_state", title="Loss Ratio by Client Type and State"), use_container_width=True)

with tabs[1]:
    st.subheader("Underwriting Recommendations")
    st.dataframe(underwriting.sort_values("risk_score", ascending=False), use_container_width=True)
    st.plotly_chart(px.bar(underwriting.head(25), x="client_name", y="risk_score", color="risk_tier", title="Top Account Risk Scores"), use_container_width=True)

with tabs[2]:
    st.plotly_chart(px.box(filtered, x="autonomy_level", y="risk_score", color="client_type", title="Risk Score by Autonomy Level"), use_container_width=True)
    st.plotly_chart(px.scatter(filtered, x="manual_override_rate", y="loss_ratio", color="risk_tier", size="near_miss_rate", title="Manual Overrides vs Loss Ratio"), use_container_width=True)
    st.dataframe(filtered[["fleet_id", "month", "autonomy_level", "manual_override_rate", "disengagement_rate", "sensor_failure_rate", "ai_confidence_avg"]].head(250), use_container_width=True)

with tabs[3]:
    claims_summary = claims.groupby(["claim_type", "accident_severity"], as_index=False).agg(claims=("claim_id", "count"), incurred_loss=("incurred_loss", "sum"))
    st.plotly_chart(px.bar(claims_summary, x="claim_type", y="incurred_loss", color="accident_severity", title="Claim Severity by Cause"), use_container_width=True)
    st.dataframe(claims.sort_values("incurred_loss", ascending=False).head(200), use_container_width=True)

with tabs[4]:
    st.plotly_chart(px.bar(importance.head(15), x="feature", y="classifier_importance", title="Risk Classifier Feature Importance"), use_container_width=True)
    anomaly_path = DATA_PROCESSED / "anomaly_results.csv"
    if anomaly_path.exists():
        anomalies = pd.read_csv(anomaly_path)
        st.subheader("Anomaly Alerts")
        st.dataframe(anomalies.loc[anomalies["anomaly_flag"] == True].head(200), use_container_width=True)

with tabs[5]:
    issues = pd.read_csv(DATA_PROCESSED / "data_quality_issues.csv")
    st.dataframe(issues, use_container_width=True)
    st.plotly_chart(px.bar(issues, x="check_name", y="issue_count", color="severity", title="Data Quality Findings"), use_container_width=True)
