#!/usr/bin/env python3
"""Export tracked source and a complete offline HTML review file."""
import argparse
import base64
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def standalone():
    html = (ROOT/"preview/index.html").read_text()
    css = (ROOT/"preview/style.css").read_text()
    html = html.replace('<link rel="stylesheet" href="style.css">', '<style>\n'+css+'\n</style>')
    for name in ("tokens.js", "icons.js", "app.js"):
        text = (ROOT/"preview"/name).read_text()
        if name == "app.js":
            data = base64.b64encode((ROOT/"preview/assets/wallpaper.svg").read_bytes()).decode()
            text = text.replace('url("assets/wallpaper.svg")', 'url("data:image/svg+xml;base64,'+data+'")')
        text = text.replace('</script', '<\\/script')
        html = html.replace('<script src="'+name+'"></script>', '<script>\n'+text+'\n</script>')
    return html


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=ROOT/"dist")
    args=parser.parse_args()
    target=args.output.resolve();target.mkdir(parents=True,exist_ok=True)
    html=standalone()
    preview=target/"PrismOS-Preview-v0.4.html";preview.write_text(html)
    files=subprocess.check_output(["git","ls-files","-z"],cwd=ROOT).decode().split("\0")
    archive=target/"BlueberryPie-17-Source-v0.4.zip"
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as package:
        for name in filter(None,files):
            file=ROOT/name
            if file.is_file() and name != preview.name:package.write(file,"PrismOS/"+name)
        package.writestr("PrismOS/PrismOS-Preview-v0.4.html",html)
    print(preview)
    print(archive)


if __name__ == "__main__":main()
