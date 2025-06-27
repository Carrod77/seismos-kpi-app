
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# --------------------------
# Firebase Setup
# --------------------------
@st.cache_resource
def init_firestore():
    cred = credentials.Certificate("seismoskpi-firebase-adminsdk-fbsvc-16d14ae4a5.json")
    firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firestore()

# --------------------------
# Load Jobs from Firestore
# --------------------------
@st.cache_data(ttl=10)
def load_jobs():
    jobs_ref = db.collection("jobs")
    docs = jobs_ref.stream()
    jobs = {}
    for doc in docs:
        jobs[doc.id] = doc.to_dict()
    return jobs

jobs_data = load_jobs()

# --------------------------
# App UI - Viewer
# --------------------------
st.title("Seismos KPI Viewer")

if not jobs_data:
    st.warning("No job data found.")
else:
    job_ids = list(jobs_data.keys())
    selected_job = st.selectbox("Select Job to View", job_ids)

    if selected_job:
        job_data = jobs_data[selected_job]
        st.header(f"Job: {selected_job} - {job_data['operator']} - {job_data['pad']}")

        # Display stage progress
        st.subheader("Stage Progress")
        well_progress = []
        for well, total_stages in job_data["wells"].items():
            completed = len([k for k in job_data.get("stage_log", {}) if k.startswith(f"{well}_s")])
            percent = round(completed / total_stages * 100, 2)
            well_progress.append({
                "Well": well,
                "Completed Stages": completed,
                "Total Stages": total_stages,
                "Progress (%)": percent
            })
        df = pd.DataFrame(well_progress)
        st.dataframe(df)

        fig = px.bar(df, x="Well", y="Progress (%)", color="Well", title="Progress by Well")
        st.plotly_chart(fig)

        # Display quality issues
        st.subheader("Quality Entries")
        if "quality" in job_data:
            for well, stages in job_data["quality"].items():
                with st.expander(f"Well: {well}"):
                    for stage, entry in stages.items():
                        st.markdown(f"**Stage {stage}**")
                        st.text(f"Pre Sand: {entry.get('pre_sand')}")
                        st.text(f"Post Sand: {entry.get('post_sand')}")
                        st.text(f"SPP: {entry.get('spp')}")
                        st.text(f"Comment: {entry.get('comment')}")
                        st.markdown("---")
        else:
            st.info("No quality entries found.")
