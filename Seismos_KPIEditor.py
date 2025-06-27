import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
import json

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
# Save Job to Firestore
# --------------------------
def save_job(job_id, job_data):
    db.collection("jobs").document(job_id).set(job_data)

# --------------------------
# App UI - Editor
# --------------------------
st.title("Seismos KPI Editor")

with st.sidebar:
    st.header("Create or Load Job")
    job_id = st.text_input("Job ID")
    operator = st.text_input("Operator")
    pad = st.text_input("Pad")
    well_count = st.number_input("Number of Wells", min_value=1, step=1)

    wells = {}
    for i in range(well_count):
        col1, col2 = st.columns([2, 1])
        with col1:
            well_name = st.text_input(f"Well {i+1} Name", key=f"well_{i}")
        with col2:
            stage_count = st.number_input(f"Stages", min_value=1, step=1, key=f"stages_{i}")
        wells[well_name] = stage_count

    if st.button("Create Job"):
        new_job = {
            "operator": operator,
            "pad": pad,
            "wells": wells,
            "stage_log": {},
            "quality": {}
        }
        save_job(job_id, new_job)
        st.success(f"Job {job_id} created.")
        st.rerun()

if jobs_data:
    job_ids = list(jobs_data.keys())
    selected_job = st.selectbox("Select Job to Update", job_ids)

    if selected_job:
        job_data = jobs_data[selected_job]

        tab1, tab2 = st.tabs(["Update KPI", "Update Quality"])

        with tab1:
            st.subheader("Add Stage Timing")
            selected_well = st.selectbox("Well", list(job_data["wells"].keys()))
            stage = st.number_input("Stage Number", min_value=1, step=1)
            start_time = st.time_input("Start Time")
            end_time = st.time_input("End Time")
            date = st.date_input("Date")

            if st.button("Save KPI Entry"):
                start_dt = datetime.combine(date, start_time)
                end_dt = datetime.combine(date, end_time)
                duration_hr = (end_dt - start_dt).total_seconds() / 3600
                entry = {
                    "well": selected_well,
                    "stage": stage,
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                    "duration_hr": duration_hr
                }
                job_data.setdefault("stage_log", {})[f"{selected_well}_s{stage}"] = entry
                save_job(selected_job, job_data)
                st.success("KPI entry saved.")

        with tab2:
            st.subheader("Add Quality Info")
            selected_well = st.selectbox("Well (Q)", list(job_data["wells"].keys()), key="qwell")
            stage = st.number_input("Stage #", min_value=1, step=1, key="qstage")

            pre = st.text_input("Pre Sand")
            post = st.text_input("Post Sand")
            spp = st.text_input("SPP")
            comment = st.text_area("Comment")

            if st.button("Save Quality Entry"):
                entry = {
                    "pre_sand": pre,
                    "post_sand": post,
                    "spp": spp,
                    "comment": comment
                }
                job_data.setdefault("quality", {}).setdefault(selected_well, {})[str(stage)] = entry
                save_job(selected_job, job_data)
                st.success("Quality entry saved.")
