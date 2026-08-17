#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify that CUMCM bibliography entries have traceable, non-invented metadata.

This tool intentionally treats unavailable online evidence as UNVERIFIED. It is a
publication gate, not a citation formatter or a source of bibliographic facts.
"""

from __future__ import print_function

import argparse
import csv
import datetime
import difflib
import json
import os
import re
import sys
try:
    from urllib.error import HTTPError, URLError
    from urllib.parse import quote
    from urllib.request import Request, urlopen
except ImportError:  # pragma: no cover - retained for old Python environments
    from urllib2 import HTTPError, URLError, Request, urlopen
    from urllib import quote


LEDGER_COLUMNS = (
    "citation_key", "title", "authors", "year", "source_type", "doi",
    "canonical_url", "isbn", "verification_source", "verified_at", "status"
)
SOURCE_TYPES = set(("doi", "publisher", "official_web", "book", "dataset", "standard"))
DOI_PREFIX = re.compile(r"^https?://(?:dx\.)?doi\.org/", re.I)
ENTRY_START = re.compile(r"@([A-Za-z]+)\s*([\{\(])")


def fail(message, errors):
    errors.append(message)


def read_text(path):
    with open(path, "rb") as handle:
        data = handle.read()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("cannot decode as UTF-8 or GB18030")


def clean_value(value):
    value = (value or "").strip().strip(",")
    if len(value) >= 2 and ((value[0] == "{" and value[-1] == "}") or
                            (value[0] == '"' and value[-1] == '"')):
        value = value[1:-1]
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_doi(value):
    value = DOI_PREFIX.sub("", (value or "").strip())
    return value.rstrip("/ ").lower()


def normalize_title(value):
    return "".join(character for character in (value or "").lower()
                   if character.isalnum())


def title_matches(left, right):
    left = normalize_title(left)
    right = normalize_title(right)
    if not left or not right:
        return False
    if left in right or right in left:
        return True
    return difflib.SequenceMatcher(None, left, right).ratio() >= 0.90


def split_top_level(value, separator):
    pieces = []
    start = 0
    brace_depth = 0
    quoted = False
    escaped = False
    for index, character in enumerate(value):
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if character == '"':
            quoted = not quoted
            continue
        if not quoted:
            if character == "{":
                brace_depth += 1
            elif character == "}" and brace_depth:
                brace_depth -= 1
            elif character == separator and brace_depth == 0:
                pieces.append(value[start:index])
                start = index + 1
    pieces.append(value[start:])
    return pieces


def parse_bibtex(text):
    entries = {}
    position = 0
    while True:
        match = ENTRY_START.search(text, position)
        if not match:
            break
        opener = match.group(2)
        closer = "}" if opener == "{" else ")"
        depth = 1
        quoted = False
        escaped = False
        cursor = match.end()
        while cursor < len(text) and depth:
            character = text[cursor]
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = not quoted
            elif not quoted:
                if character == opener:
                    depth += 1
                elif character == closer:
                    depth -= 1
            cursor += 1
        if depth:
            raise ValueError("unterminated BibTeX entry near character {0}".format(match.start()))
        body = text[match.end():cursor - 1]
        pieces = split_top_level(body, ",")
        key = pieces[0].strip()
        entry_type = match.group(1).lower()
        if entry_type in ("comment", "preamble", "string"):
            position = cursor
            continue
        if not key:
            raise ValueError("BibTeX entry has no citation key")
        if key in entries:
            raise ValueError("duplicate BibTeX citation key: {0}".format(key))
        fields = {"entry_type": entry_type}
        for piece in pieces[1:]:
            field_pair = split_top_level(piece, "=")
            if len(field_pair) < 2:
                continue
            field_name = field_pair[0].strip().lower()
            field_value = "=".join(field_pair[1:])
            if field_name:
                fields[field_name] = clean_value(field_value)
        entries[key] = fields
        position = cursor
    if not entries:
        raise ValueError("no BibTeX entries found")
    return entries


def read_ledger(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = tuple(reader.fieldnames or ())
        missing = [column for column in LEDGER_COLUMNS if column not in fieldnames]
        if missing:
            raise ValueError("ledger is missing required columns: {0}".format(", ".join(missing)))
        records = {}
        for line_number, row in enumerate(reader, 2):
            record = dict((column, (row.get(column) or "").strip()) for column in fieldnames)
            key = record.get("citation_key", "")
            if not key:
                raise ValueError("ledger line {0} has an empty citation_key".format(line_number))
            if key in records:
                raise ValueError("ledger has duplicate citation_key: {0}".format(key))
            record["_line"] = line_number
            records[key] = record
    if not records:
        raise ValueError("ledger has no references")
    return records


def validate_ledger_record(key, record, errors):
    prefix = "{0} (ledger line {1})".format(key, record["_line"])
    for field_name in ("title", "authors", "year", "source_type", "verification_source", "verified_at", "status"):
        if not record.get(field_name):
            fail("{0}: missing {1}".format(prefix, field_name), errors)
    if record.get("source_type") not in SOURCE_TYPES:
        fail("{0}: unsupported source_type".format(prefix), errors)
    if record.get("status", "").lower() != "verified":
        fail("{0}: status must be verified".format(prefix), errors)
    if record.get("year") and not re.match(r"^\d{4}$", record["year"]):
        fail("{0}: year must be YYYY".format(prefix), errors)
    if record.get("verified_at"):
        try:
            datetime.datetime.strptime(record["verified_at"], "%Y-%m-%d")
        except ValueError:
            fail("{0}: verified_at must be YYYY-MM-DD".format(prefix), errors)
    source_type = record.get("source_type")
    doi = normalize_doi(record.get("doi"))
    url = record.get("canonical_url", "")
    if source_type == "doi" and not doi:
        fail("{0}: DOI source requires doi".format(prefix), errors)
    if source_type != "doi" and not url.startswith(("https://", "http://")):
        fail("{0}: non-DOI source requires canonical_url".format(prefix), errors)
    if record.get("verification_source") and not record["verification_source"].startswith(("https://", "http://")):
        fail("{0}: verification_source must be an HTTP(S) URL".format(prefix), errors)


def validate_bibtex(bib_entries, ledger_records, errors):
    for key in sorted(bib_entries):
        entry = bib_entries[key]
        if key not in ledger_records:
            fail("{0}: BibTeX entry is absent from ledger".format(key), errors)
            continue
        record = ledger_records[key]
        for field_name in ("title", "author", "year"):
            if not entry.get(field_name):
                fail("{0}: BibTeX entry is missing {1}".format(key, field_name), errors)
        if entry.get("title") and not title_matches(entry["title"], record.get("title")):
            fail("{0}: BibTeX title differs from verified ledger title".format(key), errors)
        if entry.get("year") and record.get("year") and entry["year"] != record["year"]:
            fail("{0}: BibTeX year differs from verified ledger year".format(key), errors)
        bib_doi = normalize_doi(entry.get("doi"))
        ledger_doi = normalize_doi(record.get("doi"))
        if ledger_doi and bib_doi != ledger_doi:
            fail("{0}: BibTeX DOI differs from verified ledger DOI".format(key), errors)
    for key in sorted(ledger_records):
        if key not in bib_entries:
            fail("{0}: verified ledger entry is absent from BibTeX".format(key), errors)


def get_json(url):
    request = Request(url, headers={"User-Agent": "CUMCM-Reference-Verifier/1.0"})
    response = urlopen(request, timeout=20)
    try:
        status = response.getcode()
        payload = response.read()
    finally:
        response.close()
    if status < 200 or status >= 300:
        raise HTTPError(url, status, "unexpected HTTP status", None, None)
    return json.loads(payload.decode("utf-8"))


def check_url(url):
    request = Request(url, headers={"User-Agent": "CUMCM-Reference-Verifier/1.0"})
    response = urlopen(request, timeout=20)
    try:
        status = response.getcode()
        response.read(1024)
    finally:
        response.close()
    if status < 200 or status >= 400:
        raise HTTPError(url, status, "unexpected HTTP status", None, None)


def crossref_years(message):
    years = set()
    for field_name in ("published-print", "published-online", "issued", "created"):
        parts = (message.get(field_name, {}) or {}).get("date-parts", [])
        if parts and parts[0] and parts[0][0]:
            years.add(str(parts[0][0]))
    return years


def author_families(value):
    """Extract comparable family-name tokens from ledger author text."""
    pieces = re.split(r"\s+and\s+|;|\n", value or "", flags=re.I)
    families = []
    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        if "," in piece:
            family = piece.split(",", 1)[0].strip()
        else:
            words = piece.split()
            family = words[-1] if words else piece
        family = "".join(character for character in family.lower() if character.isalnum())
        if family:
            families.append(family)
    return families


def online_check(key, record, errors, unverified):
    doi = normalize_doi(record.get("doi"))
    try:
        if doi:
            data = get_json("https://api.crossref.org/works/{0}".format(quote(doi, safe="")))
            message = data.get("message", {})
            titles = message.get("title", []) or []
            actual_title = titles[0] if titles else ""
            if not actual_title or not title_matches(actual_title, record.get("title")):
                fail("{0}: Crossref title conflicts with ledger".format(key), errors)
            years = crossref_years(message)
            if years and record.get("year") not in years:
                fail("{0}: Crossref year {1} conflicts with ledger year {2}".format(
                    key, ", ".join(sorted(years)), record.get("year")), errors)
            crossref_authors = message.get("author", []) or []
            if not crossref_authors:
                unverified.append("{0}: Crossref returned no author metadata".format(key))
            else:
                verified_families = set(
                    "".join(character for character in (author.get("family") or "").lower()
                            if character.isalnum())
                    for author in crossref_authors
                    if author.get("family")
                )
                ledger_families = author_families(record.get("authors"))
                missing_families = [family for family in ledger_families
                                    if family not in verified_families]
                if missing_families:
                    fail("{0}: author family differs from Crossref metadata: {1}".format(
                        key, ", ".join(missing_families)), errors)
            returned_doi = normalize_doi(message.get("DOI"))
            if returned_doi != doi:
                fail("{0}: Crossref returned a different DOI".format(key), errors)
        else:
            check_url(record.get("canonical_url"))
    except HTTPError as exc:
        if exc.code in (404, 410):
            fail("{0}: source returned HTTP {1}".format(key, exc.code), errors)
        else:
            unverified.append("{0}: source could not be confirmed (HTTP {1})".format(key, exc.code))
    except (URLError, ValueError, IOError) as exc:
        unverified.append("{0}: source could not be reached ({1})".format(key, exc))


def write_report(path, report):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(
        description="Verify BibTeX and a CUMCM citation ledger against real sources."
    )
    parser.add_argument("--ledger", required=True, help="UTF-8 TSV citation verification ledger")
    parser.add_argument("--bib", help="BibTeX file to match against the ledger")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--online", action="store_true", help="Query Crossref DOI records or canonical source URLs")
    mode.add_argument("--offline", action="store_true", help="Only check local consistency; never returns PASS")
    parser.add_argument("--report", help="Write a JSON verification report")
    args = parser.parse_args()

    errors = []
    unverified = []
    ledger_records = {}
    bib_entries = {}
    try:
        ledger_records = read_ledger(args.ledger)
        for key in sorted(ledger_records):
            validate_ledger_record(key, ledger_records[key], errors)
        if args.bib:
            bib_entries = parse_bibtex(read_text(args.bib))
            validate_bibtex(bib_entries, ledger_records, errors)
        if args.online and not errors:
            for key in sorted(ledger_records):
                online_check(key, ledger_records[key], errors, unverified)
        if args.offline:
            unverified.append("offline consistency check does not verify external sources")
    except (IOError, OSError, ValueError, csv.Error) as exc:
        errors.append(str(exc))

    result = "PASS"
    if errors:
        result = "FAIL"
    elif unverified:
        result = "UNVERIFIED"
    report = {
        "result": result,
        "ledger": os.path.abspath(args.ledger),
        "bib": os.path.abspath(args.bib) if args.bib else None,
        "verified_count": len(ledger_records),
        "errors": errors,
        "unverified": unverified,
        "checked_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    if args.report:
        write_report(args.report, report)
    for message in errors:
        print("[ERROR] {0}".format(message))
    for message in unverified:
        print("[UNVERIFIED] {0}".format(message))
    print("RESULT={0}".format(result))
    if result == "PASS":
        return 0
    if result == "UNVERIFIED":
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
