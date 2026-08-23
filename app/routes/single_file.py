import io
import os
import uuid
import pandas as pd
import zipfile

from flask import Blueprint, current_app, render_template, request, send_file, session, flash, redirect, url_for

from ..services.file_loader import load_dataframe, basic_stats, get_extension
from ..services import operations as ops
from ..services import exporters

bp = Blueprint("single_file", __name__)


def _session_path(filename_key: str) -> str:
    """Resolve the on-disk path for the file tracked in this session."""
    stored_name = session.get(filename_key)
    if not stored_name:
        return None
    return os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)


def _load_current_df():
    path = _session_path("single_file")
    if not path or not os.path.exists(path):
        return None
    return pd.read_csv(path)


def _save_result_and_offer_download(df, base_name="result"):
    """Stores the result df to session-scoped state for the export step."""
    stored_name = f"{uuid.uuid4().hex}.csv"
    stored_path = os.path.join(current_app.config["OUTPUT_FOLDER"], stored_name)
    df.to_csv(stored_path, index=False)
    session["last_result"] = stored_name
    return stored_name


@bp.route("/", methods=["GET", "POST"])
def home():
    """
    Epic 1: upload a file, show row/column count + preview.
    The parsed file is re-saved as a normalized CSV so every downstream
    operation can reload it consistently regardless of original format.
    """
    stats = None
    preview_html = None

    if request.method == "POST":
        file = request.files.get("data_file")
        if not file or file.filename == "":
            flash("Veuillez choisir un fichier à téléverser.", "warning")
            return redirect(url_for("single_file.home"))

        try:
            df = load_dataframe(file)
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("single_file.home"))

        stored_name = f"{uuid.uuid4().hex}.csv"
        stored_path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)
        df.to_csv(stored_path, index=False)

        session["single_file"] = stored_name
        session["single_file_original_name"] = file.filename

        stats = basic_stats(df)
        preview_html = df.head(20).to_html(classes="table table-sm table-striped", index=False)

    return render_template("single_file/home.html", stats=stats, preview_html=preview_html)


@bp.route("/sort", methods=["GET", "POST"])
def sort():
    """Epic 2."""
    df = _load_current_df()
    if df is None:
        flash("Veuillez d'abord téléverser un fichier.", "warning")
        return redirect(url_for("single_file.home"))

    result_html = None
    if request.method == "POST":
        mode = request.form.get("mode")
        ascending = request.form.get("ascending") == "on"
        if mode == "column":
            column = request.form.get("column")
            sorted_df = ops.sort_by_column(df, column, ascending)
        else:
            sorted_df = ops.sort_by_full_row(df, ascending)

        _save_result_and_offer_download(sorted_df)
        result_html = sorted_df.head(50).to_html(classes="table table-sm table-striped", index=False)

    return render_template("single_file/sort.html", columns=df.columns.tolist(), result_html=result_html)


@bp.route("/duplicates", methods=["GET", "POST"])
def duplicates():
    """Epic 3."""
    df = _load_current_df()
    if df is None:
        flash("Veuillez d'abord téléverser un fichier.", "warning")
        return redirect(url_for("single_file.home"))

    summary_html = None
    if request.method == "POST":
        mode = request.form.get("mode")
        subset = [request.form.get("column")] if mode == "column" else None

        summary = ops.find_duplicates(df, subset=subset)
        summary_html = summary.to_html(classes="table table-sm table-striped", index=False)

        cleaned = ops.remove_duplicates(df, subset=subset)
        _save_result_and_offer_download(cleaned)

    return render_template("single_file/duplicates.html", columns=df.columns.tolist(), summary_html=summary_html)


@bp.route("/sequences", methods=["GET", "POST"])
def sequences():
    """Epic 4: detect sequential values in a column or across rows."""
    df = _load_current_df()
    if df is None:
        flash("Veuillez d'abord téléverser un fichier.", "warning")
        return redirect(url_for("single_file.home"))

    columns = df.columns.tolist()
    summary_html = None

    if request.method == "POST":
        mode = request.form.get("mode")
        min_length = int(request.form.get("min_length", 3))
        results = []

        if mode == "column":
            column = request.form.get("column")
            sequences = ops.detect_sequences(df[column].tolist(), min_length=min_length)
            for sequence in sequences:
                results.append({"column": column, **sequence})
        else:
            for row_index, row in df.iterrows():
                sequences = ops.detect_sequences(row.tolist(), min_length=min_length)
                for sequence in sequences:
                    results.append({"row": int(row_index), **sequence})

        summary = pd.DataFrame(results)
        if summary.empty:
            summary = pd.DataFrame(columns=["column" if mode == "column" else "row", "start", "end", "length"])

        _save_result_and_offer_download(summary, base_name="sequences")
        summary_html = summary.to_html(classes="table table-sm table-striped", index=False)

    return render_template("single_file/sequences.html", columns=columns, summary_html=summary_html)


@bp.route("/split", methods=["GET", "POST"])
def split():
    """Epic 5: split the input file into multiple smaller files."""
    df = _load_current_df()
    if df is None:
        flash("Veuillez d'abord téléverser un fichier.", "warning")
        return redirect(url_for("single_file.home"))

    if request.method == "POST":
        mode = request.form.get("split_mode")
        fmt = request.form.get("fmt", "csv")

        try:
            if mode == "files":
                n_files = int(request.form.get("n_files", 1))
                chunks = ops.split_by_num_files(df, n_files)
            else:
                rows_per_file = int(request.form.get("rows_per_file", 1))
                chunks = ops.split_by_rows_per_file(df, rows_per_file)
        except ValueError:
            flash("Veuillez fournir un paramètre de division valide.", "warning")
            return redirect(url_for("single_file.split"))

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for index, chunk in enumerate(chunks, start=1):
                filename = f"split_{index}.{fmt}"
                if fmt in {"csv", "txt"}:
                    sep = "," if fmt == "csv" else "\t"
                    archive.writestr(filename, chunk.to_csv(index=False, sep=sep))
                elif fmt == "xlsx":
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        chunk.to_excel(writer, index=False)
                    archive.writestr(filename, output.getvalue())
                else:
                    flash("Unsupported split export format. Use CSV, TXT, or XLSX.", "danger")
                    return redirect(url_for("single_file.split"))

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name="split_files.zip",
            mimetype="application/zip",
        )

    return render_template("single_file/split.html")


@bp.route("/template", methods=["GET", "POST"])
def template():
    """Epic 6: generate a new file format according to a template."""
    df = _load_current_df()
    if df is None:
        flash("Veuillez d'abord téléverser un fichier.", "warning")
        return redirect(url_for("single_file.home"))

    columns = df.columns.tolist()
    result_html = None

    if request.method == "POST":
        source_column = request.form.get("source_column")
        template_text = request.form.get("template_text", "")
        separator = request.form.get("separator", "|")

        if "__SOURCE__" not in template_text:
            flash("Le modèle doit inclure le placeholder __SOURCE__.", "warning")
            return redirect(url_for("single_file.template"))

        template_fields = [field.strip() for field in template_text.split(separator)]
        result = ops.apply_template(df, source_column, template_fields, separator=separator)
        _save_result_and_offer_download(result, base_name="template")
        result_html = result.head(50).to_html(classes="table table-sm table-striped", index=False)

    return render_template("single_file/template.html", columns=columns, result_html=result_html)


@bp.route("/transform", methods=["GET", "POST"])
def transform():
    """Epic 7-8: column-level transformations and structure edits."""
    df = _load_current_df()
    if df is None:
        flash("Veuillez d'abord téléverser un fichier.", "warning")
        return redirect(url_for("single_file.home"))

    columns = df.columns.tolist()
    result_html = None

    if request.method == "POST":
        operation = request.form.get("operation")
        transformed = df.copy()

        try:
            if operation == "inject":
                column = request.form.get("column")
                text = request.form.get("text", "")
                position = request.form.get("position", "append")
                transformed = ops.inject_string(transformed, column, text, position)
            elif operation == "remove_string":
                column = request.form.get("column")
                text = request.form.get("text", "")
                transformed = ops.remove_string(transformed, column, text)
            elif operation == "math":
                column = request.form.get("column")
                operator = request.form.get("operator")
                operand = float(request.form.get("operand", "0"))
                transformed = ops.apply_math(transformed, column, operator, operand)
            elif operation == "reorder":
                order_text = request.form.get("order_text", "")
                new_order = [col.strip() for col in order_text.split(",") if col.strip()]
                transformed = ops.reorder_columns(transformed, new_order)
            elif operation == "add_column":
                name = request.form.get("new_name", "")
                value = request.form.get("new_value", "")
                position = int(request.form.get("new_position", len(columns)))
                transformed = ops.add_column(transformed, name, value, position)
            elif operation == "remove_column":
                position = int(request.form.get("remove_position", -1))
                transformed = ops.remove_column(transformed, position)
            elif operation == "extract_columns":
                positions_text = request.form.get("positions_text", "")
                positions = [int(p.strip()) for p in positions_text.split(",") if p.strip().isdigit()]
                transformed = ops.extract_columns(transformed, positions)
            else:
                flash("Opération de transformation inconnue.", "warning")
                return redirect(url_for("single_file.transform"))

            _save_result_and_offer_download(transformed, base_name="transform")
            result_html = transformed.head(50).to_html(classes="table table-sm table-striped", index=False)
        except Exception as exc:
            flash(str(exc), "danger")
            return redirect(url_for("single_file.transform"))

    return render_template("single_file/transform.html", columns=columns, result_html=result_html)


@bp.route("/export/<fmt>")
def export_last_result(fmt):
    """Epic 9: download the last generated result in the chosen format."""
    stored_name = session.get("last_result")
    if not stored_name:
        flash("Rien à exporter pour le moment — effectuez d'abord une opération.", "warning")
        return redirect(url_for("single_file.home"))

    src_path = os.path.join(current_app.config["OUTPUT_FOLDER"], stored_name)
    df = pd.read_csv(src_path)
    sep = request.args.get("sep")

    out_name = f"{uuid.uuid4().hex}.{fmt}"
    out_path = os.path.join(current_app.config["OUTPUT_FOLDER"], out_name)
    exporters.export(df, out_path, fmt, sep=sep)

    return send_file(out_path, as_attachment=True, download_name=f"result.{fmt}")
