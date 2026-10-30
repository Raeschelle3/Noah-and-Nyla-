"""Build the site from source.html.

preview.html: images inlined, draft banner (for review as an artifact)
index.html:   full HTML document that loads images from assets/ (for hosting)
"""
import base64, json, pathlib, re

here = pathlib.Path(__file__).parent
src = (here / "source.html").read_text()
links = {k: v for k, v in json.loads((here / "links.json").read_text()).items() if not k.startswith("_")}
for k, v in links.items():
    src = src.replace("{{%s}}" % k, v)

images = set(re.findall(r"\{\{([\w-]+\.jpg)\}\}", src))

preview = src.replace("<!--DRAFT-->", '<div class="draft"><div class="wrap">DRAFT for Rae\'s review. Buttons go to the Stan store until each product\'s own link is added.</div></div>')
for name in images:
    data = base64.b64encode((here / "assets" / name).read_bytes()).decode()
    preview = preview.replace("{{%s}}" % name, "data:image/jpeg;base64," + data)
(here / "preview.html").write_text(preview)

page = src.replace("<!--DRAFT-->", "")
for name in images:
    page = page.replace("{{%s}}" % name, "assets/" + name)
head, body = page.split("</style>", 1)
(here / "index.html").write_text(
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    + head + "</style>\n</head>\n<body>\n" + body + "\n</body>\n</html>\n")
print("built preview.html and index.html")
