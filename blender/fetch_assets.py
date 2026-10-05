"""Download the CC0 texture / HDRI / model kit listed in apartment/sourcing.json
into blender/assets/ (plain Python 3, no Blender needed).

    python blender/fetch_assets.py              # everything (~600 MB at 2k)
    python blender/fetch_assets.py textures hdri rembrandt

Files that already exist with the right size are skipped, so it is resumable.
"""

import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets")
API = "https://api.polyhaven.com/files/"
UA = {"User-Agent": "apartment-flythrough/1.0"}
TEX_MAPS = {"Diffuse": "diff", "Rough": "rough", "nor_gl": "nor_gl", "Displacement": "disp"}


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r:
        return json.load(r)


def download(url, path, size=None):
    if os.path.exists(path) and (size is None or os.path.getsize(path) == size):
        return "skip"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r, open(tmp, "wb") as fh:
        while chunk := r.read(1 << 20):
            fh.write(chunk)
    os.replace(tmp, path)
    return "ok"


def textures(S):
    res = S["resolution"]
    for mat, spec in S["textures"].items():
        pid = spec["id"]
        files = get_json(API + pid)
        for key, short in TEX_MAPS.items():
            f = files.get(key, {}).get(res, {}).get("jpg") or files.get(key, {}).get(res, {}).get("png")
            if f:
                ext = os.path.splitext(f["url"])[1]
                p = os.path.join(OUT, "textures", mat, f"{mat}_{short}{ext}")
                print(f"  {mat:14s} {short:7s} {download(f['url'], p, f['size'])}")


def hdri(S):
    for name, pid in S["hdri"].items():
        f = get_json(API + pid)["hdri"][S["resolution"]]["hdr"]
        print(f"  hdri {name:7s} {download(f['url'], os.path.join(OUT, 'hdri', f'{name}.hdr'), f['size'])}")


def models(S):
    res = S["resolution"]
    for pid in sorted({d["model"] for d in S["dressing"]}):
        if True:
            b = get_json(API + pid)["blend"][res]["blend"]
            base = os.path.join(OUT, "models", pid)
            download(b["url"], os.path.join(base, f"{pid}.blend"), b["size"])
            for rel, inc in b.get("include", {}).items():
                download(inc["url"], os.path.join(base, rel), inc["size"])
            print(f"  model {pid}")


def rembrandt(S):
    r = S["rembrandt"]
    print(f"  rembrandt {download(r['url'], os.path.join(OUT, r['file']))}")


def main():
    with open(os.path.join(HERE, "apartment", "sourcing.json"), encoding="utf-8") as fh:
        S = json.load(fh)
    steps = sys.argv[1:] or ["textures", "hdri", "models", "rembrandt"]
    for step in steps:
        print(step)
        globals()[step](S)


if __name__ == "__main__":
    main()
