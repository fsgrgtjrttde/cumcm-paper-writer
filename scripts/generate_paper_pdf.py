#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build and validate a CUMCM LaTeX paper PDF through the shared LaTeX tool.

The script is deliberately a thin orchestrator. It does not replace the
official/template-aware latex_paper.py checks and refuses to build without a
PASS citation-verification report.
"""

from __future__ import print_function

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def find_latex_script(explicit):
    candidates = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        candidates.append(Path(codex_home) / "skills" / "math-modeling" / "tools" / "latex" / "scripts" / "latex_paper.py")
    skill_root = Path(__file__).resolve().parents[1]
    candidates.append(skill_root.parent / "math-modeling" / "tools" / "latex" / "scripts" / "latex_paper.py")
    candidates.append(Path.home() / ".codex" / "skills" / "math-modeling" / "tools" / "latex" / "scripts" / "latex_paper.py")
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    searched = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError("latex_paper.py not found; searched: {0}".format(searched))


def resolve_project(project_arg, main_arg):
    project = Path(project_arg).expanduser().resolve()
    if project.is_file():
        if project.suffix.lower() != ".tex":
            raise ValueError("project file must be a .tex main file")
        project_root = project.parent
        main = project
    else:
        project_root = project
        if not project_root.is_dir():
            raise FileNotFoundError("LaTeX project directory does not exist: {0}".format(project_root))
        if main_arg:
            main = (project_root / main_arg).resolve()
        else:
            top_level = sorted(project_root.glob("*.tex"))
            if len(top_level) != 1:
                raise ValueError("set --main because project has {0} top-level .tex files".format(len(top_level)))
            main = top_level[0].resolve()
    if not main.is_file():
        raise FileNotFoundError("LaTeX main file does not exist: {0}".format(main))
    try:
        main.relative_to(project_root)
    except ValueError:
        raise ValueError("main file must be inside the LaTeX project directory")
    return project_root, main


def read_citation_report(path):
    report_path = Path(path).expanduser().resolve()
    if not report_path.is_file():
        raise FileNotFoundError("citation verification report does not exist: {0}".format(report_path))
    with report_path.open("r", encoding="utf-8-sig") as handle:
        report = json.load(handle)
    if report.get("result") != "PASS":
        raise ValueError("citation verification report is not PASS: {0}".format(report.get("result", "missing")))
    if not isinstance(report.get("verified_count"), int) or report.get("verified_count") < 1:
        raise ValueError("citation verification report has no verified references")
    return report_path, report


def run_step(label, command, cwd):
    print("[RUN] {0}".format(label))
    print("      {0}".format(" ".join(str(part) for part in command)))
    completed = subprocess.run(command, cwd=str(cwd))
    if completed.returncode != 0:
        raise RuntimeError("{0} failed with exit code {1}".format(label, completed.returncode))
    print("[PASS] {0}".format(label))


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(
        description="Generate and validate a CUMCM LaTeX paper PDF."
    )
    parser.add_argument("project", help="LaTeX project directory or main .tex file")
    parser.add_argument("--main", help="Main .tex path relative to project directory")
    parser.add_argument("--output", help="Published PDF path (default: project-root paper.pdf)")
    parser.add_argument("--latex-script", help="Explicit path to math-modeling/tools/latex/scripts/latex_paper.py")
    parser.add_argument("--engine", choices=("xelatex", "lualatex", "pdflatex"), default="xelatex")
    parser.add_argument("--bibliography-backend", choices=("none", "bibtex", "biber"), default="biber")
    parser.add_argument("--citation-report", required=True, help="PASS JSON report from verify_references.py")
    parser.add_argument("--contest", default="cumcm", choices=("cumcm", "mcm-icm", "generic"))
    parser.add_argument("--questions", nargs="+", required=True, help="All question labels, e.g. q1 q2 q3")
    parser.add_argument("--min-image-dpi", type=int, default=300)
    parser.add_argument("--max-pages", type=int, default=30, help="Official body-page limit; CUMCM 2026 defaults to 30")
    parser.add_argument("--body-start-page", type=int, required=True)
    parser.add_argument("--appendix-start-page", type=int)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    try:
        project_root, main_tex = resolve_project(args.project, args.main)
        citation_path, citation_report = read_citation_report(args.citation_report)
        latex_script = find_latex_script(args.latex_script)
        output_pdf = Path(args.output).expanduser().resolve() if args.output else project_root / "完整论文.pdf"
        if output_pdf.exists() and not args.overwrite:
            raise FileExistsError("published PDF already exists; pass --overwrite only after confirming replacement")
        if args.max_pages <= 0 or args.min_image_dpi <= 0 or args.body_start_page <= 0:
            raise ValueError("page and DPI thresholds must be positive")
        if args.appendix_start_page is not None and args.appendix_start_page <= args.body_start_page:
            raise ValueError("appendix start page must follow body start page")

        python_executable = sys.executable
        run_step(
            "LaTeX environment doctor",
            [python_executable, str(latex_script), "doctor", "--engine", args.engine,
             "--bibliography-backend", args.bibliography_backend],
            project_root,
        )
        build_command = [
            python_executable, str(latex_script), "build", str(main_tex),
            "--engine", args.engine, "--timeout", str(args.timeout),
            "--publish", str(output_pdf)
        ]
        if args.overwrite:
            build_command.append("--overwrite")
        run_step("LaTeX PDF build", build_command, project_root)

        validate_command = [
            python_executable, str(latex_script), "validate", str(main_tex),
            "--pdf", str(output_pdf), "--contest", args.contest,
            "--quality-checks", "--questions"
        ] + list(args.questions) + [
            "--min-image-dpi", str(args.min_image_dpi),
            "--max-pages", str(args.max_pages),
            "--body-start-page", str(args.body_start_page)
        ]
        if args.appendix_start_page is not None:
            validate_command += ["--appendix-start-page", str(args.appendix_start_page)]
        run_step("LaTeX PDF quality validation", validate_command, project_root)

        if not output_pdf.is_file():
            raise FileNotFoundError("LaTeX tool returned success but PDF is missing: {0}".format(output_pdf))
        report_path = output_pdf.with_name(output_pdf.stem + ".pdf-generation.json")
        report = {
            "result": "PASS",
            "project": str(project_root),
            "main_tex": str(main_tex),
            "pdf": str(output_pdf),
            "pdf_sha256": sha256(output_pdf),
            "pdf_bytes": output_pdf.stat().st_size,
            "citation_report": str(citation_path),
            "citation_verified_count": citation_report.get("verified_count"),
            "engine": args.engine,
            "bibliography_backend": args.bibliography_backend,
            "contest": args.contest,
            "questions": list(args.questions),
            "max_pages": args.max_pages,
            "body_start_page": args.body_start_page,
            "appendix_start_page": args.appendix_start_page,
        }
        with report_path.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        print("RESULT=PASS")
        print("PDF={0}".format(output_pdf))
        print("REPORT={0}".format(report_path))
        return 0
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError, OSError) as exc:
        print("[ERROR] {0}".format(exc))
        print("RESULT=FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
