import html
import os
import re
import subprocess

from bs4 import BeautifulSoup as bs
from bs4 import Comment
from markdownify import markdownify as md

from utilities import render_front_matter  # adatta l'import a come lo fa crc.py

SITE = "https://go.dev"
PAGE = f"{SITE}/doc/effective_go"

DIRECTIVE = re.compile(r"\{\{code\s+(.*?)\}\}")
ARG = re.compile(r'"([^"]*)"|`([^`]*)`')
TEMPLATE_LITERAL = re.compile(r'\{\{"(.*?)"\}\}')
H2_SPLIT = re.compile(r"(?=<h2[\s>])")


# ---------- stadio 0: controllo del checkout ----------

def check_commit(local: str, expected: str) -> None:
    actual = subprocess.run(
        ["git", "-C", local, "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    if actual != expected:
        raise RuntimeError(f"{local} è a {actual}, il TOML chiede {expected}")


# ---------- stadio 1: stringa -> stringa ----------

def unwrap_literals(text: str) -> str:
    """{{"{{if .}}"}} -> {{if .}}"""
    return TEMPLATE_LITERAL.sub(lambda m: m.group(1), text)


def _pattern(arg: str) -> str:
    # "/regex/" -> "regex"; "$" resta "$"
    if len(arg) >= 2 and arg.startswith("/") and arg.endswith("/"):
        return arg[1:-1]
    return arg


def extract_fragment(path: str, start: str, end: str) -> str:
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    s = next((i for i, l in enumerate(lines) if re.search(start, l)), None)
    if s is None:
        raise ValueError(f"{path}: nessuna riga per l'inizio {start!r}")
    if end == "$":
        e = len(lines) - 1
    else:
        e = next((i for i in range(s, len(lines)) if re.search(end, lines[i])), None)
        if e is None:
            raise ValueError(f"{path}: nessuna riga per la fine {end!r}")
    # righe marcate OMIT: ipotesi che il sito le tolga, da verificare con grep -c OMIT
    chunk = [l for l in lines[s:e + 1] if not l.rstrip().endswith("// OMIT")]
    return "\n".join(chunk)


def resolve_code(text: str, local: str, root: str) -> str:
    def replace(m: re.Match) -> str:
        args = [a or b for a, b in ARG.findall(m.group(1))]
        if len(args) != 3:
            raise ValueError(f"direttiva non riconosciuta: {m.group(0)}")
        file, start, end = args
        path = os.path.join(local, root, file.lstrip("/"))
        code = extract_fragment(path, _pattern(start), _pattern(end))
        return "<pre>" + html.escape(code) + "</pre>"

    return DIRECTIVE.sub(replace, text)


# ---------- stadio 2: spezzare per <h2> (ancora sulla stringa) ----------

def split_sections(text: str) -> tuple[str, list[str]]:
    chunks = H2_SPLIT.split(text)
    head = re.sub(r"<!--.*?-->", "", chunks[0], flags=re.S).strip()
    if head and not head.startswith('<div class="Note">'):
        raise ValueError(f"testo inatteso prima del primo <h2>: {head[:80]!r}")
    return head, chunks[1:]


# ---------- stadio 3: modifiche all'albero ----------

def fix_links(body, ids: set[str]) -> None:
    for a in body.find_all("a", href=True):
        href = a["href"]
        if href.startswith("#"):
            if href[1:] not in ids:
                raise ValueError(f"ancora senza id nel documento: {href}")
            a["href"] = PAGE + href
        elif href.startswith("/"):
            a["href"] = SITE + href


def clean_pre(body) -> None:
    for pre in body.find_all("pre"):
        pre.string = pre.get_text().strip("\n")


def dl_to_ul(soup, body) -> None:
    for dl in body.find_all("dl"):
        ul = soup.new_tag("ul")
        li = None
        for child in list(dl.children):
            name = getattr(child, "name", None)
            if name == "dt":
                li = soup.new_tag("li")
                strong = soup.new_tag("strong")
                strong.string = " ".join(child.get_text().split())
                li.append(strong)
                li.append(": ")
                ul.append(li)
            elif name == "dd":
                for c in list(child.contents):
                    li.append(c.extract())
        dl.replace_with(ul)


def to_markdown(chunk: str, ids: set[str]) -> tuple[str, str, str]:
    """Ritorna (titolo, id dell'h2, markdown)."""
    soup = bs(chunk, "html5lib")
    body = soup.body
    for c in body.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    h2 = body.find("h2")
    title = " ".join(h2.get_text().split())
    anchor = h2["id"]
    fix_links(body, ids)
    clean_pre(body)
    dl_to_ul(soup, body)
    markdown = md(body.decode_contents(), heading_style="ATX")
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()
    return title, anchor, markdown


# ---------- controlli ----------

FENCE = re.compile(r"```.*?```", re.S)
INLINE = re.compile(r"`[^`\n]*`")
HTML_TAG = re.compile(r"</?[a-zA-Z][^>\n]*>")


def check_output(name: str, content: str) -> None:
    if "{{code" in content:
        raise ValueError(f"{name}: direttiva {{{{code}}}} rimasta")
    if "](/" in content or "](#" in content:
        raise ValueError(f"{name}: link relativo rimasto")
    prose = INLINE.sub("", FENCE.sub("", content))
    if "TODO" in prose:
        raise ValueError(f"{name}: TODO rimasto fuori dal codice")
    m = HTML_TAG.search(prose)
    if m:
        raise ValueError(f"{name}: HTML rimasto fuori dal codice: {m.group(0)!r}")


# ---------- build ----------

def slugify(title: str) -> str:
    s = re.sub(r"[^\w\s-]", "", title.lower())
    return re.sub(r"\s+", "-", s.strip())


def build(source: dict, pack: dict, version: str) -> list[dict]:
    local = source["local"]
    check_commit(local, source["commit"])

    in_path = os.path.join(local, source["path"])
    if not os.path.exists(in_path):
        raise FileNotFoundError(f"{in_path} does not exist!")
    root = source["path"].split("/")[0]  # "_content"

    with open(in_path, encoding="utf-8") as f:
        text = f.read()

    text = unwrap_literals(text)
    text = resolve_code(text, local, root)
    ids = set(re.findall(r'\bid="([^"]+)"', text))

    head, chunks = split_sections(text)
    if head:
        # l'avviso va subito dopo il titolo di Introduction
        chunks[0] = chunks[0].replace("</h2>", "</h2>\n" + head, 1)

    results = []
    for i, chunk in enumerate(chunks):
        title, anchor, markdown = to_markdown(chunk, ids)
        front = render_front_matter(
            source,
            pack,
            version,
            {"title": title},
            f"{PAGE}#{anchor}"
        )
        content = front.rstrip("\n") + "\n\n" + markdown + "\n"
        name = f"{i:02d}-{slugify(title)}.md"
        check_output(name, content)
        results.append({
            "path": f"{source['out']}/{name}",
            "content": content,
            "origin": source["commit"],
        })

    n_h2 = len(re.findall(r"<h2[\s>]", text))
    if len(results) != n_h2:
        raise ValueError(f"{len(results)} file per {n_h2} <h2>")
    return results
