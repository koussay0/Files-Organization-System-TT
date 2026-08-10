import os
import uuid

import pandas as pd
from flask import Blueprint, current_app, render_template, request, send_file, session, flash, redirect, url_for

from ..services.file_loader import load_dataframe
from ..services import operations as ops
from ..services import exporters

bp = Blueprint("multi_file", __name__)


@bp.route("/", methods=["GET", "POST"])
def home():
    """Epic 10: upload two files and compare them."""
    results = None
    columns = None

    if request.method == "POST":
        file1 = request.files.get("file1")
        file2 = request.files.get("file2")
        mode = request.form.get("mode")

        if not file1 or not file2:
            flash("Please upload both files.", "warning")
            return redirect(url_for("multi_file.home"))

        df1 = load_dataframe(file1)
        df2 = load_dataframe(file2)

        subset = [request.form.get("column")] if mode == "column" else None
        comparison = ops.compare_files(df1, df2, subset=subset)

        for key, df in comparison.items():
            stored_name = f"{uuid.uuid4().hex}.csv"
            df.to_csv(os.path.join(current_app.config["OUTPUT_FOLDER"], stored_name), index=False)
            session[f"compare_{key}"] = stored_name

        results = {
            key: df.head(30).to_html(classes="table table-sm table-striped", index=False)
            for key, df in comparison.items()
        }
        columns = list(df1.columns)

    return render_template("multi_file/home.html", results=results, columns=columns)


@bp.route("/export/<result_key>/<fmt>")
def export_comparison(result_key, fmt):
    """Epic 9 applied to Epic 10 results: in_both / only_in_f1 / only_in_f2."""
    stored_name = session.get(f"compare_{result_key}")
    if not stored_name:
        flash("Run a comparison first.", "warning")
        return redirect(url_for("multi_file.home"))

    src_path = os.path.join(current_app.config["OUTPUT_FOLDER"], stored_name)
    df = pd.read_csv(src_path)
    sep = request.args.get("sep")

    out_name = f"{uuid.uuid4().hex}.{fmt}"
    out_path = os.path.join(current_app.config["OUTPUT_FOLDER"], out_name)
    exporters.export(df, out_path, fmt, sep=sep)

    return send_file(out_path, as_attachment=True, download_name=f"{result_key}.{fmt}")


@bp.route("/merge", methods=["GET", "POST"])
def merge():
    """Epic 11: merge two files side by side."""
    merged_html = None

    if request.method == "POST":
        file1 = request.files.get("file1")
        file2 = request.files.get("file2")

        if not file1 or not file2:
            flash("Please upload both files.", "warning")
            return redirect(url_for("multi_file.merge"))

        df1 = load_dataframe(file1)
        df2 = load_dataframe(file2)

        cols_f1 = [col.strip() for col in request.form.get("columns_f1", "").split(",") if col.strip()]
        cols_f2 = [col.strip() for col in request.form.get("columns_f2", "").split(",") if col.strip()]
        sep = request.form.get("separator", ",")

        if not cols_f1:
            cols_f1 = list(df1.columns)
        if not cols_f2:
            cols_f2 = list(df2.columns)

        merged = ops.merge_files(df1, df2, cols_f1, cols_f2)
        session["last_result"] = f"{uuid.uuid4().hex}.csv"
        merged.to_csv(os.path.join(current_app.config["OUTPUT_FOLDER"], session["last_result"]), index=False)

        merged_html = merged.head(30).to_html(classes="table table-sm table-striped", index=False)
        return render_template("multi_file/merge.html", merged_html=merged_html, separator=sep)

    return render_template("multi_file/merge.html", merged_html=merged_html, separator=",")
