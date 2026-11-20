import hashlib
import json
from datetime import datetime
from godoc import *

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

    with open("corpus/go/1.26/MANIFEST.json", "w") as f:
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