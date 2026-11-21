
def render_front_matter(
    source: dict,
    pack: dict,
    version: str,
    identity: dict,
    url: str
) -> str:
    """Function that renders the front matter. 
    The identity dict may have different values and keys based on the go source.
    The order used to list the componennts of the front matter is always the same:
    source, kind, language, version, <identity>, url, license"""

    content = f"""source: {source["name"]}
kind: {source["kind"]}
language: {pack["name"]}
version: \"{version}\"\n"""
    for k, v in identity.items():
        content += f"{k}: {v}\n"
    content += f"url: {url}\nlicense: {source["license"]}"

    return f"---\n{content}\n---"