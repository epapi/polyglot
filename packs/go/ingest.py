import hashlib
import json
import os
import pathlib
import subprocess
import tomllib

from datetime import datetime
from typing import Callable

import crc
import godoc

PACK_PATH = "packs/go/pack.toml"
CORPUS_BASE_PATH = "corpus/go"
BUILDERS = {
    "code_review_comments": crc.build,
    "go_doc": godoc.build
}

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

    path = os.path.join(CORPUS_BASE_PATH, go_version)
    with open(os.path.join(path, "MANIFEST.json"), "w") as f:
        json.dump(manifest, f, indent=2)


def save_file(file_out: str, content: str) -> str:
    """Funcction to save a file based on its metadata.
    Returns its sha256 string"""

    path_obj = pathlib.Path(file_out)
    path_obj.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(file_out, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def main():

    pack = tomllib.load(open(PACK_PATH, "rb"))
    version = pack["version"]["supported"][0]
    files_and_sources = []

    for source in pack["sources"]:
        build_func = BUILDERS.get(source["name"], None)
        if build_func is None:
            print(f"No builder for {source["name"]}, skipping")
        else:
            source_files = build_func(source, pack, version)
            print(f"{source["name"]}: {len(source_files)} files")
            files_and_sources.append({"source": source["name"], "files": source_files})

    # shas256 = []
    corpus_path = os.path.join(CORPUS_BASE_PATH, version)
    manifest_metadatas = []

    fs: dict
    for fs in files_and_sources:
        print(f"Saving files for {fs["source"]}")
        for f in fs["files"]:
            sha256 = save_file(os.path.join(corpus_path, f["path"]), f["content"])
            f["sha256"] = sha256
            manifest_metadatas.append(
                {
                    "path": f["path"],
                    "source": fs["source"],
                    "origin": f["origin"],
                    "sha256": sha256
                }
            )

    create_manifest(version, manifest_metadatas)
    print("Created MANIFEST.json")
    # print(files_and_sources)



    # packages_metadata = [
    #     {
    #         "source": "go_doc",
    #         "kind": "reference",
    #         "language": "go",
    #         "version": '"1.26"',
    #         "package": "errors",
    #         "url": "https://pkg.go.dev/errors",
    #         "license": "BSD-3-Clause",
    #     },
    #     {
    #         "source": "go_doc",
    #         "kind": "reference",
    #         "language": "go",
    #         "version": '"1.26"',
    #         "package": "fmt",
    #         "url": "https://pkg.go.dev/fmt",
    #         "license": "BSD-3-Clause",
    #     },
    #     {
    #         "source": "go_doc",
    #         "kind": "reference",
    #         "language": "go",
    #         "version": '"1.26"',
    #         "package": "os",
    #         "url": "https://pkg.go.dev/os",
    #         "license": "BSD-3-Clause",
    #     },
    # ]

    # go_version = get_go_version()
    # go_source = "go_doc"
    # files_metadata = []

    # for meta in packages_metadata:
    #     package = meta["package"]
    #     file = f"reference/{package}.md"
    #     command = f"go doc -all {package}"
    #     text = run_go_doc(package)
    #     parsed = parse_go_doc(text)
    #     md = render_markdown(parsed, meta)
    #     with open(f"corpus/go/1.26/{file}", "w") as f:
    #         f.write(md)
    #     files_metadata.append(
    #         {
    #             "path": file,
    #             "source": go_source,
    #             "command": command,
    #             "sha256": hashlib.sha256(md.encode("utf-8")).hexdigest()
    #         }
    #     )

    # create_manifest(go_version=go_version, files_metadata=files_metadata)


if __name__ == "__main__":
    main()