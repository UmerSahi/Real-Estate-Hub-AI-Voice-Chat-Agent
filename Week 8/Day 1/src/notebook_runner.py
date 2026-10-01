"""Notebook Execution Engine for Week 8.
Executes notebooks/day1_eda_and_pipeline.ipynb, captures all outputs,
and populates the notebook JSON with execution counts, stdout streams,
and display data.
"""
from __future__ import annotations

import base64
import contextlib
import io
import json
import os
import sys
from pathlib import Path

# Limit OpenBLAS threads
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

# Ensure Week 8 root and src are on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

from IPython.core.interactiveshell import InteractiveShell

NOTEBOOK_PATH = BASE_DIR / "notebooks" / "day1_eda_and_pipeline.ipynb"


def execute_notebook(nb_path: Path):
    print(f"Reading notebook: {nb_path}")
    with open(nb_path, "r", encoding="utf-8") as f:
        nb_data = json.load(f)

    # Initialize IPython interactive shell
    shell = InteractiveShell.instance()

    # Pre-configure shell display hook to capture displayed objects
    captured_displays = []

    def custom_display_hook(obj, **kwargs):
        captured_displays.append(obj)

    # Push working directory to notebooks/ or root
    os.chdir(nb_path.parent)

    exec_counter = 1
    total_cells = len(nb_data["cells"])
    print(f"Executing {total_cells} total cells...\n")

    for i, cell in enumerate(nb_data["cells"]):
        if cell["cell_type"] != "code":
            continue

        source_code = "".join(cell["source"])
        print(f"--- Running Code Cell {exec_counter} (Index {i}) ---")
        
        # Capture stdout & stderr
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

        # Format stdout output
        if stdout_text:
            cell_outputs.append({
                "name": "stdout",
                "output_type": "stream",
                "text": stdout_text.splitlines(keepends=True)
            })
            print(f"[STDOUT]:\n{stdout_text.strip()[:400]}")

        # Format stderr output
        if stderr_text:
            cell_outputs.append({
                "name": "stderr",
                "output_type": "stream",
                "text": stderr_text.splitlines(keepends=True)
            })

        # Check for image file references in source to attach PNG display data if relevant
        if "Image(filename=" in source_code:
            import re
            img_match = re.search(r'Image\(filename=["\'](.*?)["\']\)', source_code)
            if img_match:
                img_rel = img_match.group(1)
                img_abs = (nb_path.parent / img_rel).resolve()
                if img_abs.exists():
                    with open(img_abs, "rb") as img_f:
                        img_b64 = base64.b64encode(img_f.read()).decode("utf-8")
                    cell_outputs.append({
                        "data": {
                            "image/png": img_b64,
                            "text/plain": [f"<IPython.core.display.Image object>"]
                        },
                        "metadata": {},
                        "output_type": "display_data"
                    })
                    print(f"[IMAGE ATTACHED]: {img_abs.name} ({len(img_b64)} chars b64)")

        # Update cell metadata
        cell["execution_count"] = exec_counter
        cell["outputs"] = cell_outputs
        exec_counter += 1
        print()

    # Save executed notebook
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb_data, f, indent=1)

    print(f"\n[SUCCESS] All code cells executed and saved with outputs into {nb_path}!")


if __name__ == "__main__":
    execute_notebook(NOTEBOOK_PATH)
