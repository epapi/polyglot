import os
import re

PAGE_URL = "https://go.dev/wiki/CodeReviewComments"

ANCHOR = re.compile(r"(\[[^\]]*\])\(#([^)]*)\)")
PATH = re.compile(r"(\[[^\]]*\])\(/([^)]*)\)")
PAGE = re.compile(r"(\[[^\]]*\])\((\w+)\)")
A_TAG = re.compile(r'<a href="([^"]*)">(.*?)<\/a>')

def build(source: dict, pack: dict, version: str) -> list[dict]:
    """Common interface that returns sources' parsed documentation"""
    data = []
    with open(os.path.join(source["local"], source["path"]), "r") as f:
        content = f.read()
    ## thinking about what to do with the introduction
    


def split_sections(text: str) -> tuple:
    """Restituisce preambolo (dopo ultimo --- e il primo ##) e sezioni.
    scarta il front matter iniziale ---...---
    sezioni: lista di (titolo, corpo) in ordine di comparsa
    """
    lines = text.splitlines()

    ## removing front matter
    front_matter_count = 0
    while front_matter_count != 2:
        line = lines.pop(0)
        if line == "---":
            front_matter_count += 1

    sections = []
    in_code = False
    introduction = ""
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
        if not in_code and line.strip().startswith("## "):
            sections.append({
                "title": line[3:].strip(),
                "text": ""
            })
            continue
        if not sections:
            introduction += line.rstrip() + "\n"
        else:
            sections[-1]["text"] += line.rstrip() + "\n"

    for s in sections:
        s["text"] = s["text"].strip("\n")

    return introduction.strip(), sections

def apply_regex(text: str, page_url: str) -> str:
    text = A_TAG.sub(lambda m: f"[{m.group(2)}]({m.group(1)})", text)
    text = ANCHOR.sub(lambda m: f"{m.group(1)}({page_url}#{m.group(2)})", text)
    text = PATH.sub(lambda m: f"{m.group(1)}(https://go.dev/{m.group(2)})", text)
    text = PAGE.sub(lambda m: f"{m.group(1)}(https://go.dev/wiki/{m.group(2)})", text)
    return text
    

def fix_links(text: str, page_url: str) -> str:
    """Functions that returns a text with transforms .md urls, anchors, etc... 
    transformed into absolute URLs
    """
    lines = text.split("```")
    for i in range(0, len(lines), 2):
        lines[i] = apply_regex(lines[i], page_url)
    
    return "```".join(lines)

def write_introduction(text: str, path: str, filename: str = "00-introduction.md") -> None:
    """Writes down the introduction of CodeReviewComments"""
    if not os.path.exists(path):
        raise FileExistsError(f"{path} does not exist")

    with open(path + f"/{filename}", "w") as f:
        f.write(text)

def build_sections_metadata(sections: list) -> list[dict]:
    metadata = []
    for s in sections:
        metadata.append()

if __name__ == "__main__":
    GO_VERSION = "1.26"
    corpus_path = f"corpus/go/{GO_VERSION}/guides/code_review_comments"
    with open("sources/go/go.googlesource-wiki/CodeReviewComments.md", "r") as f:
        text = f.read()

    intro, sections = split_sections(text)
    intro = fix_links(intro, PAGE_URL)
    write_introduction(intro, os.path.join(os.getcwd(), corpus_path))

    