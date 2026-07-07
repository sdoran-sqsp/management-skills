#!/usr/bin/env python3
"""Combines agenda_{level}.md + discussion_template_{level}.md into one
simple HTML document per level, for uploading to Drive as a Google Doc.
Handles just what these generated docs actually use: #/##/### headers,
**bold**, _italic_, and GFM tables (cells may already contain literal <br>).
Not a general markdown converter - scoped to this script's own output.
"""
import re
import sys
import os

LEVELS = ["IC2", "IC3", "IC4", "IC5", "M5"]


def inline(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<i>\1</i>", text)
    return text


def cell_html(text):
    """Table-cell content that already contains literal '<br>' joins (from
    the roster/attendees cells) - Drive's HTML importer collapses inline
    <br> inside <td>, so re-wrap each line as its own <div> instead, which
    survives the import as separate lines within the cell."""
    parts = inline(text).split("<br>")
    if len(parts) == 1:
        return parts[0]
    return "".join(f"<div>{p}</div>" for p in parts)


def md_to_html_body(md_text):
    lines = md_text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("### "):
            out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.strip().startswith("|"):
            # table: header row, separator row (skip), then data rows
            header_cells = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 1  # skip separator row (|:-:|:-:|...)
            rows = []
            i += 1
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells)
                i += 1
            i -= 1  # compensate for outer while's i += 1
            out.append('<table border="1" cellpadding="6" cellspacing="0">')
            # Plain <td><b> for the header row, not <th> - Drive's HTML
            # importer was leaving <th> rows blank and pushing the header
            # text into what looks like the first data row instead.
            out.append("<tr>" + "".join(f"<td><b>{inline(c)}</b></td>" for c in header_cells) + "</tr>")
            for r in rows:
                out.append("<tr>" + "".join(f"<td>{cell_html(c)}</td>" for c in r) + "</tr>")
            out.append("</table>")
        elif line.strip() == "":
            pass
        else:
            out.append(f"<p>{inline(line)}</p>")
        i += 1
    return "\n".join(out)


def main():
    indir = sys.argv[1] if len(sys.argv) > 1 else "output"
    outdir = sys.argv[2] if len(sys.argv) > 2 else "output_html"
    os.makedirs(outdir, exist_ok=True)

    for level in LEVELS:
        agenda_path = os.path.join(indir, f"agenda_{level}.md")
        disc_path = os.path.join(indir, f"discussion_template_{level}.md")
        if not os.path.exists(agenda_path):
            continue
        with open(agenda_path) as f:
            agenda_md = f.read()
        with open(disc_path) as f:
            disc_md = f.read()

        html = (
            "<html><body>"
            + md_to_html_body(agenda_md)
            + "<hr>"
            + md_to_html_body(disc_md)
            + "</body></html>"
        )
        out_path = os.path.join(outdir, f"{level}.html")
        with open(out_path, "w") as f:
            f.write(html)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
