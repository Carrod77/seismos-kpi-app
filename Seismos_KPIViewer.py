import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime

DATA_PATH = "jobs_data.json"

def load_data():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

data = load_data()

st.title("Seismos KPI Viewer")

selected_job = st.selectbox("Select Job", list(data["jobs"].keys()))
if selected_job:
    job = data["jobs"][selected_job]
    st.subheader(f"{selected_job} - {job['pad']} ({job['operator']})")

    stage_log = job["stage_log"]
    if stage_log:
        st.markdown("### KPI Timeline")
        all_stages = list(stage_log.values())
        df = pd.DataFrame([{
            "Well": s["well"],
            "Stage": s["stage"],
            "Start": pd.to_datetime(s["start"]),
            "End": pd.to_datetime(s["end"])
        } for s in all_stages])

        fig = px.timeline(df, x_start="Start", x_end="End", y="Well", color="Stage")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Quality Results")
    selected_well = st.selectbox("Select Well", list(job["wells"].keys()))
    if selected_well in job["quality"] and job["quality"][selected_well]:
        stage_list = list(job["quality"][selected_well].keys())
        selected_stage = st.selectbox("Select Stage", stage_list)
        entry = job["quality"][selected_well][selected_stage]
        st.markdown(f"**Pre Sand:** {entry['pre_sand']}")
        st.markdown(f"**Post Sand:** {entry['post_sand']}")
        st.markdown(f"**SPP:** {entry['spp']}")
        st.markdown(f"**Comments:** {entry['comment']}")
    else:
        st.info("No quality data entered yet for this well.")