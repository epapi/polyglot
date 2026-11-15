import hashlib
import json
import os
import re
import subprocess
import tomllib
7
from datetime import datetime

HEADER_RE = re.compile(r"^[A-Z]+$")
NAME_RE = re.compile(r"^(?:func|var|type|const)\s+(\w+)")
METHOD_RE = re.compile(r"^func\s+\(\s*(?:\w+\s+)?\*?(\w+)\)\s+(\w+)")
IDENT_RE = re.compile(r"^(\w+)")
SINGATURES_MATCHES = ("var ", "func ", "type ", "const ")

HEADERS_LIST = [
    {"field_name": "variables", "match": "var"},
    {"field_name": "functions", "match": "func"},
    {"field_name": "types", "match": "type"},
    {"field_name": "constants", "match": "const"},
]

def get_go_version() -> str:
    """Runs 'go version' to get Golang version"""

    result = subprocess.run(
        ["go", "version"],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )

    if result.stderr != "":
        raise ValueError(f"An error occurred: {result.stderr}") 
    return result.stdout.strip()

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

def parse_go_doc(text: str) -> str:
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
            m = NAME_RE.match(d["signature"])
            paragraph_title = symbol_title(d["signature"])
            code = f"```go\n{d['signature']}\n```"
            description = dedent_descritpion(d["description"])
            md_text += f"### {paragraph_title}\n\n{code}\n\n{description}\n\n"

    return md_text.rstrip() + "\n"


def create_manifest(
    go_version: str, 
    files_metadata: list[dict[str]]
) -> None:
    manifest = {
        "go_version": go_version,
        "built_at": datetime.now().isoformat(timespec="seconds"),
        "files": []
    }

    for meta in files_metadata:
        manifest["files"].append(
            {k: v for k, v in meta.items()}
        )

    with open("corpus/go/MANIFEST.json", "w") as f:
        json.dump(manifest, f, indent=2)


def main():

    packages_metadata = [
        {
            "source": "go_doc",
            "kind": "reference",
            "language": "go",
            "version": '"1.26"',
            "package": "errors",
            "url": "https://pkg.go.dev/errors",
            "license": "BSD-3-Clause",
        },
        {
            "source": "go_doc",
            "kind": "reference",
            "language": "go",
            "version": '"1.26"',
            "package": "fmt",
            "url": "https://pkg.go.dev/fmt",
            "license": "BSD-3-Clause",
        },
        {
            "source": "go_doc",
            "kind": "reference",
            "language": "go",
            "version": '"1.26"',
            "package": "os",
            "url": "https://pkg.go.dev/os",
            "license": "BSD-3-Clause",
        },
    ]

    go_version = get_go_version()
    go_source = "go_doc"
    files_metadata = []

    for meta in packages_metadata:
        package = meta["package"]
        file = f"reference/{package}.md"
        command = f"go doc -all {package}"
        text = run_go_doc(package)
        parsed = parse_go_doc(text)
        md = render_markdown(parsed, meta)
        with open(f"corpus/go/1.26/{file}", "w") as f:
            f.write(md)
        files_metadata.append(
            {
                "path": file,
                "source": go_source,
                "command": command,
                "sha256": hashlib.sha256(md.encode("utf-8")).hexdigest()
            }
        )

    create_manifest(go_version=go_version, files_metadata=files_metadata)

    # meta = {
    #     "source": "go_doc",
    #     "kind": "reference",
    #     "language": "go",
    #     "version": '"1.26"',
    #     "package": "errors",
    #     "url": "https://pkg.go.dev/errors",
    #     "license": "BSD-3-Clause",
    # }
    # package_text = run_go_doc("errors")
    # parsed = parse_go_doc_1(package_text)
    # md = render_markdown(parsed, meta)
    # with open(os.getcwd() + "/corpus/go/1.26/reference/errors.md", "w") as f:
    #     f.write(md)

if __name__ == "__main__":
    main()