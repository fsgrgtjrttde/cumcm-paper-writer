#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate deterministic CUMCM 2026 electronic-paper constraints.

Exit codes: 0 PASS, 1 FAIL, 2 WARNING, 3 UNVERIFIED.
"""

from __future__ import print_function

import argparse
import io
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET


MAX_BYTES = 20 * 1024 * 1024
UNUSED_AI = u"本参赛队在竞赛过程中未使用任何AI工具。"
USED_AI_PREFIX = u"本参赛队在竞赛过程中使用了AI工具，主要用于"
USED_AI_SUFFIX = u"详细使用情况见支撑材料。"
AI_DETAIL_NAME = u"AI工具使用详情.pdf"
TEXT_EXTENSIONS = set([
    ".txt", ".md", ".csv", ".tsv", ".py", ".m", ".r", ".jl",
    ".json", ".yaml", ".yml", ".tex", ".ini", ".cfg", ".log"
])
OOXML_EXTENSIONS = set([".docx", ".xlsx", ".xlsm", ".pptx"])
GENERIC_AUTHORS = set([
    u"", u"author", u"作者", u"user", u"administrator",
    u"microsoft office user", u"wps", u"kingsoft"
])


def decode_bytes(data):
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise ValueError("text encoding is not UTF-8 or GB18030")


def read_text_file(path):
    with open(path, "rb") as handle:
        return decode_bytes(handle.read())


def xml_visible_text(data):
    root = ET.fromstring(data)
    chunks = []
    for element in root.iter():
        if element.tag.endswith("}t") and element.text:
            chunks.append(element.text)
        elif element.tag.endswith("}p"):
            chunks.append("\n")
    return u"".join(chunks)


def parse_docx_paragraphs(data):
    root = ET.fromstring(data)
    paragraphs = []
    for paragraph in root.iter():
        if not paragraph.tag.endswith("}p"):
            continue
        text = u"".join(
            node.text for node in paragraph.iter()
            if node.tag.endswith("}t") and node.text
        ).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def collect_ooxml(archive, label):
    paragraphs = []
    scan_sources = []
    metadata = []
    names = archive.namelist()
    if "word/document.xml" in names:
        paragraphs = parse_docx_paragraphs(archive.read("word/document.xml"))
    for name in names:
        lower = name.lower()
        if not lower.endswith(".xml"):
            continue
        if not (lower.startswith("word/") or lower.startswith("docprops/") or
                lower.startswith("xl/") or lower.startswith("ppt/")):
            continue
        try:
            text = xml_visible_text(archive.read(name))
        except Exception:
            continue
        if text.strip():
            scan_sources.append((label + ":" + name, text))
        if lower == "docprops/core.xml":
            try:
                root = ET.fromstring(archive.read(name))
                for node in root.iter():
                    local = node.tag.rsplit("}", 1)[-1]
                    if local in ("creator", "lastModifiedBy") and node.text:
                        value = node.text.strip()
                        if value.lower() not in GENERIC_AUTHORS:
                            metadata.append((local, value))
            except Exception:
                pass
    return paragraphs, scan_sources, metadata


def collect_docx(path):
    with zipfile.ZipFile(path, "r") as archive:
        paragraphs, sources, metadata = collect_ooxml(archive, os.path.basename(path))
        for name in archive.namelist():
            lower = name.lower()
            if "/media/" in lower or "/embeddings/" in lower or lower.startswith("customxml/"):
                sources.append((os.path.basename(path) + ":archive-name", name))
        return paragraphs, sources, metadata


def text_paragraphs(text):
    return [line.strip() for line in text.splitlines() if line.strip()]


def compact_text(value):
    return re.sub(r"\s+", "", value)


def canonical_heading(value):
    text = value.strip()
    text = re.sub(r"^#+\s*", "", text)
    text = re.sub(r"^[第]?[一二三四五六七八九十百]+[章节、.．\s]+", "", text)
    text = re.sub(r"^\d+(?:\.\d+)*[、.．\s]+", "", text)
    return compact_text(text).rstrip(u"：:")


def section_kind(value):
    heading = canonical_heading(value)
    exact = {
        u"摘要": "abstract",
        u"目录": "toc",
        u"AI工具使用声明": "ai",
        u"参考文献": "references",
        u"附录": "appendix",
        u"支撑材料文件列表": "support_list"
    }
    return exact.get(heading)


def official_ai_declarations(paragraphs):
    declarations = []
    for index, paragraph in enumerate(paragraphs):
        compact = compact_text(paragraph)
        if UNUSED_AI in compact:
            declarations.append((index, "unused", UNUSED_AI))
        start = compact.find(USED_AI_PREFIX)
        end = compact.find(USED_AI_SUFFIX, start + len(USED_AI_PREFIX))
        if start >= 0 and end >= 0:
            statement = compact[start:end + len(USED_AI_SUFFIX)]
            declarations.append((index, "used", statement))
    return declarations


def check_identity(label, text, forbidden, errors):
    compact = text or u""
    for value in forbidden:
        if value and value in compact:
            errors.append("forbidden identity string found in {0}: {1}".format(label, value))
    patterns = [
        ("team number", r"(?:参赛队号|队号)\s*[:：]\s*[A-Za-z0-9-]{3,}"),
        ("school", r"(?:学校名称|参赛学校|所在学校|院校)\s*[:：]\s*[^\s，。；;]{2,}"),
        ("region", r"赛区\s*[:：]\s*[^\s，。；;]{2,}"),
        ("name", r"(?:姓名|队员|指导教师|指导老师)\s*[:：]\s*[\u4e00-\u9fff]{2,}"),
        ("email", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
        ("mobile", r"(?<!\d)1[3-9]\d{9}(?!\d)")
    ]
    for name, pattern in patterns:
        if re.search(pattern, compact, flags=re.I):
            errors.append("possible {0} identity leakage in {1}".format(name, label))


def validate_structure(paragraphs, electronic, errors, warnings):
    sections = []
    for index, paragraph in enumerate(paragraphs):
        kind = section_kind(paragraph)
        if kind:
            sections.append((index, kind))
    positions = {}
    for index, kind in sections:
        positions.setdefault(kind, []).append(index)

    for kind, label in (
        ("abstract", "abstract heading"),
        ("ai", "AI tool use statement heading"),
        ("references", "references heading"),
        ("appendix", "appendix heading")
    ):
        if kind not in positions:
            errors.append("missing {0}".format(label))

    if "toc" in positions:
        errors.append("body must not contain a table-of-contents heading")
    if len(positions.get("ai", [])) != 1:
        errors.append("expected exactly one AI tool use statement heading")

    if all(kind in positions for kind in ("abstract", "ai", "references", "appendix")):
        order = [positions[kind][0] for kind in ("abstract", "ai", "references", "appendix")]
        if order != sorted(order):
            errors.append("required section order is abstract, AI statement, references, appendix")

    if not any(re.match(r"^\s*关键词\s*[:：]", p) for p in paragraphs):
        errors.append("missing keywords paragraph")

    if "appendix" in positions:
        appendix_text = u"\n".join(paragraphs[positions["appendix"][0]:])
        if not ((u"支撑材料" in appendix_text and u"文件列表" in appendix_text) or
                u"本论文没有支撑材料" in appendix_text):
            warnings.append("appendix should contain a support-material file list or official no-material statement")

    if electronic and "abstract" in positions:
        abstract_index = positions["abstract"][0]
        before_abstract = u"\n".join(paragraphs[:abstract_index])
        if u"承诺书" in before_abstract or u"编号专用页" in before_abstract:
            errors.append("electronic paper must not include commitment or numbering pages")
        recognized_before = [kind for index, kind in sections if index < abstract_index]
        if recognized_before:
            errors.append("electronic paper must start with the abstract section")
    return positions


def scan_pdf_bytes(label, data, forbidden, errors):
    try:
        text = data.decode("latin-1")
    except Exception:
        text = u""
    check_identity(label + " PDF bytes", text, forbidden, errors)
    for match in re.finditer(r"/(Author|Creator)\s*\(([^)]*)\)", text, flags=re.I):
        value = match.group(2).strip()
        if value and value.lower() not in GENERIC_AUTHORS:
            errors.append("PDF metadata {0} contains possible identity in {1}: {2}".format(match.group(1), label, value))


def inspect_support(path, ai_state, forbidden, errors, warnings, support_pdf_verified):
    names = []
    scan_sources = []
    ext = os.path.splitext(path)[1].lower()
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for filename in files:
                full = os.path.join(root, filename)
                relative = os.path.relpath(full, path)
                names.append(relative)
                file_ext = os.path.splitext(filename)[1].lower()
                try:
                    if file_ext in TEXT_EXTENSIONS and os.path.getsize(full) <= 5 * 1024 * 1024:
                        scan_sources.append(("support:" + relative, read_text_file(full)))
                    elif file_ext in OOXML_EXTENSIONS:
                        with zipfile.ZipFile(full, "r") as nested:
                            _, sources, metadata = collect_ooxml(nested, "support:" + relative)
                            scan_sources.extend(sources)
                            for nested_name in nested.namelist():
                                if "/media/" in nested_name.lower() or "/embeddings/" in nested_name.lower() or nested_name.lower().startswith("customxml/"):
                                    scan_sources.append(("support:" + relative + ":archive-name", nested_name))
                            for field, value in metadata:
                                errors.append("support OOXML metadata {0} contains possible identity: {1}".format(field, value))
                    elif file_ext == ".pdf":
                        data = open(full, "rb").read()
                        scan_pdf_bytes("support:" + relative, data, forbidden, errors)
                        if not support_pdf_verified:
                            warnings.append("support PDF text/layout/metadata is not verified: {0}".format(relative))
                except Exception as exc:
                    warnings.append("cannot inspect support file {0}: {1}".format(relative, exc))
    elif ext == ".zip":
        with zipfile.ZipFile(path, "r") as archive:
            names = archive.namelist()
            for name in names:
                if name.endswith("/"):
                    continue
                file_ext = os.path.splitext(name)[1].lower()
                try:
                    data = archive.read(name)
                    if file_ext in TEXT_EXTENSIONS and len(data) <= 5 * 1024 * 1024:
                        scan_sources.append(("support:" + name, decode_bytes(data)))
                    elif file_ext in OOXML_EXTENSIONS:
                        with zipfile.ZipFile(io.BytesIO(data), "r") as nested:
                            _, sources, metadata = collect_ooxml(nested, "support:" + name)
                            scan_sources.extend(sources)
                            for nested_name in nested.namelist():
                                if "/media/" in nested_name.lower() or "/embeddings/" in nested_name.lower() or nested_name.lower().startswith("customxml/"):
                                    scan_sources.append(("support:" + name + ":archive-name", nested_name))
                            for field, value in metadata:
                                errors.append("support OOXML metadata {0} contains possible identity: {1}".format(field, value))
                    elif file_ext == ".pdf":
                        scan_pdf_bytes("support:" + name, data, forbidden, errors)
                        if not support_pdf_verified:
                            warnings.append("support PDF text/layout/metadata is not verified: {0}".format(name))
                except Exception as exc:
                    warnings.append("cannot inspect support file {0}: {1}".format(name, exc))
    elif ext == ".rar":
        warnings.append("RAR content is allowed but unverified; inspect filenames, identity leakage, source completeness, and AI detail PDF manually")
    else:
        errors.append("support material must be a directory, ZIP, or RAR")

    for name in names:
        check_identity("support filename", name, forbidden, errors)
    for label, text in scan_sources:
        check_identity(label, text, forbidden, errors)

    basenames = [os.path.basename(name.rstrip("/\\")) for name in names]
    if ai_state == "used":
        if ext == ".rar":
            warnings.append("confirm that RAR contains exactly named AI detail PDF: {0}".format(AI_DETAIL_NAME))
        elif AI_DETAIL_NAME not in basenames:
            errors.append("AI detail PDF is missing from support material")


def main():
    parser = argparse.ArgumentParser(description="Validate key CUMCM 2026 electronic-paper constraints.")
    parser.add_argument("paper", help="DOCX/PDF paper or TXT/Markdown fixture")
    parser.add_argument("--electronic", action="store_true")
    parser.add_argument("--abstract-pages", type=int)
    parser.add_argument("--body-pages", type=int)
    parser.add_argument("--support", help="Support directory, ZIP, or RAR")
    parser.add_argument("--pdf-text", help="UTF-8/GB18030 text extracted separately from the PDF")
    parser.add_argument("--pdf-layout-verified", action="store_true", help="Confirm separate page-by-page PDF render inspection")
    parser.add_argument("--pdf-metadata-verified", action="store_true", help="Confirm PDF metadata and identity fields were inspected")
    parser.add_argument("--support-pdf-verified", action="store_true", help="Confirm every support PDF was text/layout/metadata inspected")
    parser.add_argument("--expect-ai", choices=("used", "unused", "unknown"), default="unknown")
    parser.add_argument("--forbidden", action="append", default=[], help="Identity string to reject everywhere")
    parser.add_argument("--allow-warning", action="store_true")
    parser.add_argument("--override-reason", help="Required evidence when overriding warnings")
    args = parser.parse_args()

    errors = []
    warnings = []
    unverified = []
    paragraphs = []
    paper_sources = []
    paper = os.path.abspath(args.paper)
    ext = os.path.splitext(paper)[1].lower()

    if not os.path.isfile(paper):
        errors.append("paper file does not exist")
    else:
        if os.path.getsize(paper) > MAX_BYTES:
            errors.append("electronic paper exceeds 20 MB")
        check_identity("paper filename", os.path.basename(paper), args.forbidden, errors)
        try:
            if ext == ".docx":
                paragraphs, paper_sources, metadata = collect_docx(paper)
                for field, value in metadata:
                    errors.append("DOCX metadata {0} contains possible identity: {1}".format(field, value))
            elif ext in (".txt", ".md"):
                paper_text = read_text_file(paper)
                paragraphs = text_paragraphs(paper_text)
                paper_sources = [(os.path.basename(paper), paper_text)]
            elif ext == ".pdf":
                with open(paper, "rb") as paper_handle:
                    scan_pdf_bytes("paper", paper_handle.read(), args.forbidden, errors)
                if not args.pdf_text:
                    unverified.append("PDF text was not supplied with --pdf-text")
                elif not os.path.isfile(args.pdf_text):
                    errors.append("PDF extracted text file does not exist")
                else:
                    paper_text = read_text_file(args.pdf_text)
                    paragraphs = text_paragraphs(paper_text)
                    paper_sources = [(os.path.basename(args.pdf_text), paper_text)]
                if not args.pdf_layout_verified:
                    unverified.append("PDF page-by-page layout was not separately verified")
                if not args.pdf_metadata_verified:
                    unverified.append("PDF metadata and identity fields were not separately verified")
            else:
                errors.append("supported paper types: .docx, .pdf, .txt, .md")
        except Exception as exc:
            errors.append("cannot read paper: {0}".format(exc))

    for label, text in paper_sources:
        check_identity(label, text, args.forbidden, errors)

    ai_state = None
    if paragraphs:
        positions = validate_structure(paragraphs, args.electronic, errors, warnings)
        declarations = official_ai_declarations(paragraphs)
        if len(declarations) != 1:
            errors.append("expected exactly one official 2026 AI-use declaration")
        else:
            declaration_index, ai_state, statement = declarations[0]
            if ai_state == "used":
                purpose = statement[len(USED_AI_PREFIX):-len(USED_AI_SUFFIX)].strip(u"，,")
                if (not purpose or u"【" in purpose or u"】" in purpose or
                        u"简要用途" in purpose or u"如语言润色" in purpose):
                    errors.append("AI-use declaration contains an unfilled purpose placeholder")
            if "ai" in positions and declaration_index <= positions["ai"][0]:
                errors.append("AI-use declaration must follow its heading")
            if "references" in positions and declaration_index >= positions["references"][0]:
                errors.append("AI-use declaration must appear before references")
        if args.expect_ai != "unknown" and ai_state != args.expect_ai:
            errors.append("AI-use declaration is {0}, expected {1}".format(ai_state or "missing", args.expect_ai))
    elif ext != ".pdf" or not unverified:
        errors.append("paper contains no readable paragraphs")

    if args.abstract_pages is None:
        warnings.append("abstract page count was not supplied")
    elif args.abstract_pages < 1:
        errors.append("abstract page count must be positive")
    elif args.abstract_pages > 1:
        warnings.append("abstract exceeds the official principle of one page; verify the exception manually")

    if args.body_pages is None:
        warnings.append("body page count was not supplied")
    elif args.body_pages < 1:
        errors.append("body page count must be positive")
    elif args.body_pages > 30:
        errors.append("body exceeds the official 30-page limit")

    if args.support:
        support = os.path.abspath(args.support)
        if not os.path.exists(support):
            errors.append("support material does not exist")
        else:
            check_identity("support archive filename", os.path.basename(support), args.forbidden, errors)
            if os.path.isfile(support) and os.path.getsize(support) > MAX_BYTES:
                errors.append("support archive exceeds 20 MB")
            try:
                inspect_support(support, ai_state, args.forbidden, errors, warnings, args.support_pdf_verified)
            except Exception as exc:
                errors.append("cannot inspect support material: {0}".format(exc))
    elif ai_state == "used":
        errors.append("AI use requires support material and AI detail PDF")

    if warnings and args.allow_warning and not (args.override_reason or "").strip():
        errors.append("--override-reason is required when --allow-warning overrides warnings")

    for item in errors:
        print("[ERROR] {0}".format(item))
    for item in warnings:
        print("[WARNING] {0}".format(item))
    for item in unverified:
        print("[UNVERIFIED] {0}".format(item))

    if errors:
        print("RESULT=FAIL")
        return 1
    if unverified:
        print("RESULT=UNVERIFIED")
        return 3
    if warnings and not args.allow_warning:
        print("RESULT=WARNING")
        return 2
    if warnings:
        print("[OVERRIDE] {0}".format(args.override_reason.strip()))
    print("RESULT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())


