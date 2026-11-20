import os
import re
import subprocess

HEADER_RE = re.compile(r"^[A-Z]+$")
NAME_RE = re.compile(r"^(?:func|var|type|const)\s+(\w+)")
METHOD_RE = re.compile(r"^func\s+\(\s*(?:\w+\s+)?\*?(\w+)\)\s+(\w+)")
IDENT_RE = re.compile(r"^(\w+)")
SINGATURES_MATCHES = ("var ", "func ", "type ", "const ")


def build(source: dict, pack: dict, version: str) -> list[dict]:
    """Common interface that returns sources' parsed documentation"""
    data = []
    for s in source["packages"]:
        cmd_all = pack["doc"]["cmd_all"].format(package=s)
        result = subprocess.run(
            cmd_all.split(),
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        if result.stderr != "":
            raise ValueError(f"An error occurred: {result.stderr}") 
        text = result.stdout
        parsed_package = parse_go_doc(text)
        md_package = render_markdown(
            parsed_package,
            {
                "source": source["name"],
                "kind": source["kind"],
                "language": "go",
                "version": version,
                "package": s,
                "url": source["url"].format(package=s),
                "license": source["license"]
            }
        )
        data.append(
            {
                "path": os.path.join(os.getcwd(), f"go/{version}/{source["out"]}/{s}.md"),
                "content": md_package,
                "origin": cmd_all
            }
        )
    return data



def run_go_doc(package: str) -> str:
    """Runs 'go doc -all <package>' to get documentation for the package"""

    if package == "":
        return f"Error: package cannot be empty"

    result = subprocess.run(
        ["go", "doc", "-all", package],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )

    if result.stderr != "":
        raise ValueError(f"An error occurred: {result.stderr}") 
    return result.stdout

def demote_heading(text: str, extra: int) -> str:
    """Adds extra '#' in front of line from go docs"""
    if not text.startswith("#"):
        return text
    return "#" * extra + text

def symbol_title(signature: str) -> str:
    """Determines paragraph title (even for consts' and vars' lists)"""
    lines = signature.splitlines()
    first_line = lines[0]

    m = METHOD_RE.match(first_line)
    if m:
        return f"{m.group(1)}.{m.group(2)}"

    m = NAME_RE.match(first_line)
    if m:
        return m.group(1)

    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "" or stripped.startswith("//"):
            continue
        m = IDENT_RE.match(stripped)
        if m:
            return f"{m.group(1)} (group)"

    return first_line

def parse_go_doc(text: str) -> dict:
    """Parse go documentations into a dictionary"""

    if text == "":
        return {}

    parsed_doc = dict()
    lines = text.splitlines()
    parsed_doc = {
        "package": lines[0].split()[1],
        "overview": "",
        "sections": {}
    }

    overview_lines = []
    current_section, symbol, closing_char = None, None, None

    for line in lines[1:]:
        ## for cases such as type A interface{...}, whose signatures are on multiple lines
        if closing_char is not None:
            symbol["signature"] += "\n" + demote_heading(line, 3)
            if line.strip() == closing_char:
                closing_char = None
            continue

        ## encountering new section (VARIABLES, FUNCTIONS, etc...)
        if HEADER_RE.match(line):
            if symbol is not None:
                parsed_doc["sections"][current_section].append(symbol)
                symbol = None
            current_section = line    
            parsed_doc["sections"][current_section] = []
            continue

        ## filling overview key
        if current_section is None:
            overview_lines.append(demote_heading(line, 2))
            continue

        ## checking for new signature and closing character
        if line.startswith(SINGATURES_MATCHES):
            if symbol is not None:
                parsed_doc["sections"][current_section].append(symbol)
            symbol = {"signature": line, "description": ""}
            if not line.startswith("func "):
                if line.endswith("{"):
                    closing_char = "}"
                if line.endswith("("):
                    closing_char = ")"
            continue

        if symbol is not None:
            symbol["description"] += line + "\n"

    if symbol is not None:
        parsed_doc["sections"][current_section].append(symbol)

    parsed_doc["overview"] = "\n".join(overview_lines)
    return parsed_doc
     

def dedent_descritpion(descr: str) -> str:
    """Removes 4 spaces indentation from go docs' descriptions"""
    lines = []
    for line in descr.splitlines():
        lines.append(line[4:] if line.startswith("    ") else line)
    return "\n".join(lines).strip()
    
def render_markdown(parsed_doc: dict, metadata: dict) -> str:

    md_text = "---\n"
    for key, value in metadata.items():
        md_text += f"{key}: {value}\n"
    md_text += "---\n\n"
    md_text += f"""# {parsed_doc["package"]}

## Overview

{parsed_doc["overview"].strip()}\n\n"""

    for name, items in parsed_doc["sections"].items():
        if not items:
            continue
        md_text += f"## {name.title()}\n\n"
        for d in items:
            paragraph_title = symbol_title(d["signature"])
            code = f"```go\n{d['signature']}\n```"
            description = dedent_descritpion(d["description"])
            md_text += f"### {paragraph_title}\n\n{code}\n\n{description}\n\n"

    return md_text.rstrip() + "\n"

if __name__ == "__main__":
    import tomllib
    pack = tomllib.load(open("packs/go/pack.toml", "rb"))
    sources = [s for s in pack["sources"] if s["name"] == "go_doc"]
    for s in sources:
        data = build(s, pack, pack["version"]["supported"][0])
        print(data)
