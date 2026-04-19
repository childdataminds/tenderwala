#!/usr/bin/env python3
"""
Simple script to generate a 5-part tender summary from a local PDF using regex-based extraction.
Usage: python scripts/generate_summary_from_pdf.py [path/to/file.pdf]
If no path is provided, it defaults to `files/1204202610384287602701248648.pdf`.
"""

import re
import sys
import os

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


def extract_full_text(pdf_path):
    if PdfReader is None:
        raise ImportError("pypdf not installed. Run: python -m pip install pypdf")
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append(f"\n\n--- PAGE {i+1} ---\n\n{text}")
    return "\n".join(pages)


def extract_regex_insights(text):
    text_s = re.sub(r"\s+", " ", str(text)).strip()
    if text_s == "":
        return {"cdr_amount":"N/A", "estimate_amount":"N/A","documents_required":[], "evaluation_criteria":[]}

    amount_pat = r"(?:rs\.?|pkr)?\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?(?:\s*(?:million|billion|crore|lakh|thousand|k))?|[0-9]{1,2}(?:\.[0-9]{1,2})?\s*%"

    def _find_near_amount(keywords, window=140):
        keys = "|".join([re.escape(k) for k in keywords])
        if keys == "":
            return "N/A"
        m = re.search(rf"(?:{keys}).{{0,{window}}}?({amount_pat})", text_s, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
        m = re.search(rf"({amount_pat}).{{0,90}}?(?:{keys})", text_s, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return "N/A"

    cdr = _find_near_amount(["cdr","call deposit","bid security","earnest money","emd","security deposit"]) 
    estimate = _find_near_amount(["estimate","estimated amount","estimated cost","engineer estimate","estimated value"]) 

    doc_patterns = [
      r"documents? required[:\-]?\s*([^\.\n]{10,260})",
      r"mandatory documents?[:\-]?\s*([^\.\n]{10,260})",
      r"check[-\s]?list[:\-]?\s*([^\.\n]{10,260})",
      r"submit(?:ted|ting)?[:\-]?\s*([^\.\n]{10,260})",
    ]
    eval_patterns = [
      r"evaluation criteria[:\-]?\s*([^\.\n]{10,260})",
      r"technical evaluation[:\-]?\s*([^\.\n]{10,260})",
      r"qualification criteria[:\-]?\s*([^\.\n]{10,260})",
    ]

    def _collect(patterns, limit=8):
        out=[]
        seen=set()
        for pat in patterns:
            for m in re.finditer(pat, text_s, flags=re.IGNORECASE):
                val = re.sub(r"\s+"," ", str(m.group(1))).strip(" -:;,._\t")
                if len(val) < 10: 
                    continue
                key = val.lower()
                if key in seen:
                    continue
                seen.add(key)
                out.append(val)
                if len(out) >= limit:
                    return out
        return out

    docs = _collect(doc_patterns, limit=8)
    evals = _collect(eval_patterns, limit=8)

    return {"cdr_amount":cdr,"estimate_amount":estimate,"documents_required":docs,"evaluation_criteria":evals}


def extract_title_department_location(text):
    # Try common labelled fields then fallback to first long line
    title = None
    m = re.search(r"(?:Tender|Project|Name of Work|Title)[:\s\-]{0,10}(.{10,200})", text, flags=re.IGNORECASE)
    if m:
        title = m.group(1).strip()
    if not title:
        for line in text.splitlines():
            s = line.strip()
            if len(s) > 40:
                title = s
                break

    dept = None
    m2 = re.search(r"(?:Department|Agency|Organization|Owner)[:\s\-]{0,10}(.{5,200})", text, flags=re.IGNORECASE)
    if m2:
        dept = m2.group(1).strip()

    loc = None
    m3 = re.search(r"(?:Location|Place|City)[:\s\-]{0,10}(.{2,80})", text, flags=re.IGNORECASE)
    if m3:
        loc = m3.group(1).strip()

    return title, dept, loc


def ai_summary_snippet(text):
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) < 120:
        return clean[:500]
    snippet = clean[:600]
    sents = re.split(r"(?<=[\.\?\!])\s+", snippet)
    if len(sents) >= 2:
        return " ".join(sents[:2])
    return snippet


def generate_summary(pdf_path):
    text = extract_full_text(pdf_path)
    insights = extract_regex_insights(text)
    title, dept, loc = extract_title_department_location(text)
    ai_snip = ai_summary_snippet(text)

    lines = []
    lines.append("AI Quick Tender Summary")

    est = insights.get("estimate_amount")
    lines.append("1) Estimated Amount: " + (est if est and str(est).strip().lower() != "n/a" else "Not found"))

    cdr = insights.get("cdr_amount")
    lines.append("2) CDR (Bidding Fee): " + (cdr if cdr and str(cdr).strip().lower() != "n/a" else "Not found"))

    lines.append("3) Eligibility Criteria (Who can apply):")
    evals = insights.get("evaluation_criteria") or []
    if evals:
        for item in evals[:6]:
            lines.append("- " + item)
    else:
        lines.append("- Not found")

    lines.append("4) Required Documents:")
    docs = insights.get("documents_required") or []
    if docs:
        for item in docs[:8]:
            lines.append("- " + item)
    else:
        lines.append("- Not found")

    lines.append("5) AI Summary:")
    if title:
        lines.append(f"- Tender: {title}")
    if dept:
        lines.append(f"- Department: {dept}")
    if loc:
        lines.append(f"- Location: {loc}")

    if not any([title, dept, loc]):
        lines.append("- " + (ai_snip[:500] if ai_snip else "Not found"))
    else:
        if ai_snip:
            lines.append("- " + ai_snip[:500])

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", nargs="?", help="PDF path", default=os.path.join("..","files","1204202610384287602701248648.pdf"))
    args = parser.parse_args()
    pdf_path = args.pdf
    if not os.path.isabs(pdf_path):
        pdf_path = os.path.abspath(pdf_path)
    if not os.path.exists(pdf_path):
        print("PDF not found:", pdf_path)
        sys.exit(1)
    try:
        out = generate_summary(pdf_path)
        print("\n" + out + "\n")
    except Exception as e:
        print("Error:", str(e))
        sys.exit(1)
