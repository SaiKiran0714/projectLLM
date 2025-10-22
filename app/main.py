import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Ensure project root is on sys.path so sibling package `core` can be imported
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.validate import validate_row
from core.extract import extract_requirement_text_to_json, explain_from_facts, parse_query_to_filters

st.set_page_config(page_title="LLM-based Requirement & Test Validation (MVP core)", layout="wide")
st.title("LLM-based Requirement & Test Validation (MVP core)")
st.caption("Upload your CSVs or use the sample ones in /data.")

# Default sample files
root = Path(__file__).resolve().parents[1]
default_req = root / "data" / "requirements.csv"
default_run = root / "data" / "test_reports.csv"

req_file = st.file_uploader("Upload requirements.csv", type=["csv"])
run_file = st.file_uploader("Upload test_reports.csv", type=["csv"])

if req_file is None and default_req.exists():
    st.info("Using sample requirements.csv")
    req_df = pd.read_csv(default_req, encoding='utf-8')
else:
    req_df = pd.read_csv(req_file, encoding='utf-8') if req_file else None

if run_file is None and default_run.exists():
    st.info("Using sample test_reports.csv")
    run_df = pd.read_csv(default_run, encoding='utf-8')
else:
    run_df = pd.read_csv(run_file, encoding='utf-8') if run_file else None

if req_df is not None and run_df is not None:
    st.subheader("Input preview")
    c1, c2 = st.columns(2)
    with c1: st.dataframe(req_df, use_container_width=True)
    with c2: st.dataframe(run_df, use_container_width=True)

    # --- 1) Extract from free_text (LLM or regex) ---
    st.markdown("### 1) Extract structured fields from free_text")
    if st.button("Extract requirements from free_text"):
        if "free_text" in req_df.columns:
            extr = []
            for _, r in req_df.iterrows():
                d = extract_requirement_text_to_json(str(r.get("free_text", "")))
                # Fill only if missing/NaN
                for k in ["metric","comparator","value","unit","component","condition"]:
                    if k in req_df.columns and (pd.isna(r[k]) if k in r else True):
                        req_df.loc[_, k] = d.get(k, r.get(k))
                extr.append(d)
            st.success("Extraction complete.")
        else:
            st.warning("No 'free_text' column found in requirements.csv")
        st.dataframe(req_df, use_container_width=True)

    # --- 2) Validate ---
    st.markdown("### 2) Run validation")
    if st.button("Run validation"):
        merged = run_df.merge(req_df, on="req_id", suffixes=("_test","_req"), how="left")
        results = []
        for _, r in merged.iterrows():
            res = validate_row(
                {"comparator": r.get("comparator"), "value": r.get("value"), "unit": r.get("unit_req")},
                {"measured_value": r.get("measured_value"), "unit": r.get("unit_test")}
            )
            row = {
                "test_id": r.get("test_id"),
                "req_id": r.get("req_id"),
                "component": r.get("component_test") or r.get("component_req") or r.get("component"),
                **res
            }
            # --- 3) Explanation from facts ---
            facts = {
                "run_id": row["test_id"],
                "component": row["component"],
                "metric": r.get("metric"),
                "status": row["status"],
                "measured_norm": row.get("measured_norm"),
                "target": row.get("target"),
                "unit": row.get("unit"),
            }
            row["explanation"] = explain_from_facts(facts)
            results.append(row)

        st.session_state.out = pd.DataFrame(results)
        st.success("Validation complete!")

    # Display results if available
    if 'out' in st.session_state:
        out = st.session_state.out
        # quick filters and metrics
        show = st.radio("Show", ["All","pass","fail","unknown"], horizontal=True)
        view = out if show=="All" else out[out["status"]==show]
        st.dataframe(view, use_container_width=True)
        c3, c4, c5 = st.columns(3)
        c3.metric("Pass", int((out["status"]=="pass").sum()))
        c4.metric("Fail", int((out["status"]=="fail").sum()))
        c5.metric("Unknown", int((out["status"]=="unknown").sum()))
        st.download_button("Download results CSV", out.to_csv(index=False), "validation_results.csv", "text/csv")

    # --- 4) Chat → filters ---
    st.markdown("### 3) Chat → filters")
    q = st.text_input("Ask something like: 'Show failed door_frame shear tests ≥5.5 kN'")
    if st.button("Apply chat filters"):
        if 'out' not in st.session_state:
            st.warning("Run validation first to generate results.")
        else:
            f = parse_query_to_filters(q)
            out = st.session_state.out
            vf = out.copy()
            if f.get("component"):
                vf = vf[vf["component"].str.contains(f["component"], case=False, na=False)]
            if f.get("status"):
                vf = vf[vf["status"]==f["status"]]
            
            # Unit filter (filter by unit alone)
            if f.get("unit") and not f.get("min_value"):
                # Filter to show only results with the specified unit
                if "unit" in vf.columns:
                    vf = vf[vf["unit"] == f["unit"]]
            
            # min_value filter logic (with or without unit)
            if f.get("min_value"):
                if f.get("unit"):
                    # Filter by specific unit and value
                    if "measured_norm" in vf.columns:
                        # Convert the threshold to the target unit if needed
                        min_val = float(f["min_value"])
                        target_unit = f["unit"]
                        
                        # Apply filter only to rows with matching units or convert if possible
                        mask = vf["unit"] == target_unit
                        if mask.any():
                            vf = vf[mask & (vf["measured_norm"] >= min_val)]
                        else:
                            # Try unit conversion for the filter
                            from core.validate import normalize
                            filtered_rows = []
                            for idx, row in vf.iterrows():
                                try:
                                    converted_measured = normalize(row["measured_norm"], row["unit"], target_unit)
                                    if converted_measured >= min_val:
                                        filtered_rows.append(idx)
                                except:
                                    # If conversion fails, skip this row
                                    pass
                            vf = vf.loc[filtered_rows] if filtered_rows else vf.iloc[0:0]
                else:
                    # No unit specified - apply filter to raw measured_norm values
                    if "measured_norm" in vf.columns:
                        vf = vf[vf["measured_norm"] >= float(f["min_value"])]
            st.write("Filters:", f)
            st.dataframe(vf, use_container_width=True)
else:
    st.warning("Load both CSVs to continue.")
