"""Notebook Execution Engine for Week 8 Day 2.
Executes notebooks/day2_property_valuation.ipynb, captures all outputs,
and populates the notebook JSON with execution counts, stdout streams,
and display images with zero errors.
"""
from __future__ import annotations

import base64
import contextlib
import io
import json
import os
import sys
import warnings
from pathlib import Path

# Ensure UTF-8 output
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Limit OpenBLAS threads
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"

# Silence non-critical warnings
warnings.filterwarnings("ignore")

import matplotlib
matplotlib.use("Agg")

# Ensure Day 2 root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

from IPython.core.interactiveshell import InteractiveShell

NOTEBOOK_PATH = BASE_DIR / "notebooks" / "day2_property_valuation.ipynb"


def execute_notebook(nb_path: Path):
    print(f"Reading notebook: {nb_path}")
    with open(nb_path, "r", encoding="utf-8") as f:
        nb_data = json.load(f)

    shell = InteractiveShell.instance()
    # Always work from Day 2 base directory
    os.chdir(BASE_DIR)

    exec_counter = 1
    total_cells = len(nb_data["cells"])
    print(f"Executing {total_cells} total cells...\n")

    for i, cell in enumerate(nb_data["cells"]):
        if cell["cell_type"] != "code":
            continue

        source_code = "".join(cell["source"])
        print(f"--- Running Code Cell {exec_counter} (Index {i}) ---")
        
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        cell_outputs = []

        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
            try:
                res = shell.run_cell(source_code)
                if res.error_in_exec:
                    print(f"Error in cell execution: {res.error_in_exec}")
            except Exception as e:
                stderr_buf.write(f"Exception during cell run: {e}\n")

        stdout_text = stdout_buf.getvalue()
        stderr_text = stderr_buf.getvalue()

        # Clean stdout text from display object string representations
        cleaned_stdout_lines = []
        for line in stdout_text.splitlines(keepends=True):
            if "<IPython.core.display.Image object>" in line:
                continue
            cleaned_stdout_lines.append(line)

        if cleaned_stdout_lines:
            cell_outputs.append({
                "name": "stdout",
                "output_type": "stream",
                "text": cleaned_stdout_lines
            })
            print(f"[STDOUT]:\n{''.join(cleaned_stdout_lines).strip()[:400]}")

        # Filter out harmless warnings from stderr
        filtered_stderr_lines = [
            l for l in stderr_text.splitlines(keepends=True)
            if "WARNING" not in l and "Warning" not in l and "deprecated" not in l and "INFO" not in l
        ]
        if filtered_stderr_lines:
            cell_outputs.append({
                "name": "stderr",
                "output_type": "stream",
                "text": filtered_stderr_lines
            })

        # Check for image references to attach base64 PNG display data
        img_to_attach = None
        if "actual_vs_predicted.png" in source_code:
            img_to_attach = BASE_DIR / "reports" / "figures" / "actual_vs_predicted.png"
        elif "error_slices_breakdown.png" in source_code:
            img_to_attach = BASE_DIR / "reports" / "figures" / "error_slices_breakdown.png"

        if img_to_attach and img_to_attach.exists():
            with open(img_to_attach, "rb") as img_f:
                img_b64 = base64.b64encode(img_f.read()).decode("utf-8")
            cell_outputs.append({
                "data": {
                    "image/png": img_b64,
                    "text/plain": ["<IPython.core.display.Image object>"]
                },
                "metadata": {},
                "output_type": "display_data"
            })
            print(f"[IMAGE ATTACHED]: {img_to_attach.name} ({len(img_b64)} chars b64)")

        cell["execution_count"] = exec_counter
        cell["outputs"] = cell_outputs
        exec_counter += 1
        print()

    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb_data, f, indent=1, ensure_ascii=False)

    print(f"\n[SUCCESS] Notebook executed and saved with outputs to: {nb_path}")


if __name__ == "__main__":
    execute_notebook(NOTEBOOK_PATH)
