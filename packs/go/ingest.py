import hashlib
import json
import os
import pathlib
import subprocess
import tomllib

from datetime import datetime
from typing import Callable

import crc
import effective_go
import godoc

PACK_PATH = "packs/go/pack.toml"
CORPUS_BASE_PATH = "corpus/go"
BUILDERS = {
    "code_review_comments": crc.build,
    "go_doc": godoc.build,
    "effective_go": effective_go.build
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


if __name__ == "__main__":
    main()