#!/usr/bin/env python3
"""Cloud-import source-tree IPKs and artwork without modifying the source repository."""
from __future__ import annotations
import hashlib, json, os, re, shutil, subprocess, time
from datetime import datetime, timezone
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[2]
SOURCE="https://github.com/online4tech/online4Tech.git"
TARGET=os.getenv("TARGET_REPO","online4tech/Online4Tech-Repository")
TOKEN=os.environ["GITHUB_TOKEN"]
API="https://api.github.com"
SESSION=requests.Session()
SESSION.headers.update({"Authorization":f"Bearer {TOKEN}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"})
WORK=Path(os.getenv("RUNNER_TEMP","/tmp"))/"o4t-source-import"
SRC=WORK/"source"
IMAGE_EXT={".png",".jpg",".jpeg",".webp",".gif",".svg"}

def api(method,url,**kwargs):
    if not url.startswith("http"): url=API+url
    for attempt in range(5):
        r=SESSION.request(method,url,timeout=(30,300),**kwargs)
        if r.status_code in (200,201,202,204): return r
        if r.status_code in (429,500,502,503,504) and attempt<4:
            time.sleep(8*(attempt+1)); continue
        raise RuntimeError(f"GitHub API {method} {r.status_code}: {r.text[:600]}")
    raise RuntimeError("GitHub API retry limit")

def slug(value):
    value=value.lower().strip()
    value=re.sub(r"\.(ipk|deb)$","",value)
    value=re.sub(r"^enigma2-plugin-(extensions-|skins-)?","",value)
    value=re.sub(r"^skins?-","",value)
    value=re.sub(r"[_+].*$","",value)
    return re.sub(r"[^a-z0-9]+","-",value).strip("-") or "unnamed-addon"

def title(value):
    return re.sub(r"\s+"," ",value.replace("-"," ").replace("_"," ")).strip().title()

def clone_source():
    WORK.mkdir(parents=True,exist_ok=True)
    if SRC.exists(): shutil.rmtree(SRC)
    subprocess.run(["git","clone","--depth","1","--filter=blob:none","--sparse",SOURCE,str(SRC)],check=True)
    subprocess.run(["git","-C",str(SRC),"sparse-checkout","set",
      "downloads/online4tech/plugins","downloads/online4tech/skins","images/plugins","images/skins"],check=True)
    return subprocess.check_output(["git","-C",str(SRC),"rev-parse","HEAD"],text=True).strip()

def package_group(path):
    parts=path.relative_to(SRC/"downloads/online4tech").parts
    kind,parent=parts[0],(parts[-2] if len(parts)>2 else "")
    if kind=="plugins":
        return "plugin",slug(parent) if parent and parent not in {"community","ipk"} else slug(path.name)
    addon_id=slug(parent) if parent and parent not in {"community","ipk","skins-openatv"} else slug(path.name)
    if addon_id in {"enigma2-display-skins","display-skins"}: addon_id="display-skin"
    return "skin",addon_id

def get_release(tag,name,body):
    try: return api("GET",f"/repos/{TARGET}/releases/tags/{tag}").json()
    except RuntimeError as e:
        if " 404:" not in str(e): raise
    return api("POST",f"/repos/{TARGET}/releases",json={"tag_name":tag,"target_commitish":"main","name":name,"body":body,"draft":False,"prerelease":False}).json()

def list_assets(release):
    found={}; page=1
    while True:
        batch=api("GET",f"/repos/{TARGET}/releases/{release['id']}/assets?per_page=100&page={page}").json()
        for a in batch: found[a["name"]]=a
        if len(batch)<100: break
        page+=1
    return found

def upload_asset(release,src,name,existing):
    h=hashlib.sha256(); size=src.stat().st_size
    with src.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    sha=h.hexdigest()
    if name in existing:
        old=existing[name]
        if int(old.get("size",-1))!=size: raise RuntimeError(f"Existing asset size conflict: {name}")
        old_sha=(old.get("digest") or "").lower().removeprefix("sha256:")
        if old_sha and old_sha!=sha: raise RuntimeError(f"Existing asset SHA conflict: {name}")
        return old,sha,size
    url=release["upload_url"].split("{",1)[0]
    headers={"Authorization":f"Bearer {TOKEN}","Accept":"application/vnd.github+json","Content-Type":"application/octet-stream"}
    with src.open("rb") as f: r=requests.post(url,params={"name":name},headers=headers,data=f,timeout=(30,900))
    if r.status_code!=201: raise RuntimeError(f"Upload failed {name}: {r.status_code} {r.text[:400]}")
    asset=r.json()
    if int(asset.get("size",-1))!=size: raise RuntimeError(f"Uploaded size mismatch: {name}")
    got=(asset.get("digest") or "").lower().removeprefix("sha256:")
    if got and got!=sha: raise RuntimeError(f"Uploaded SHA mismatch: {name}")
    existing[name]=asset
    return asset,sha,size

def copy_artwork():
    copied=[]
    for kind in ("plugins","skins"):
        src_root=SRC/"images"/kind
        if not src_root.exists(): continue
        for p in sorted(src_root.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in IMAGE_EXT or p.stat().st_size<=200: continue
            dest=ROOT/"assets"/kind/p.relative_to(src_root)
            dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():
                if hashlib.sha256(dest.read_bytes()).digest()!=hashlib.sha256(p.read_bytes()).digest():
                    raise RuntimeError(f"Refusing to overwrite existing artwork: {dest.relative_to(ROOT)}")
                continue
            shutil.copy2(p,dest)
            copied.append({"kind":kind[:-1],"source_path":p.relative_to(SRC).as_posix(),"target_path":dest.relative_to(ROOT).as_posix(),"size_bytes":p.stat().st_size})
    return copied

def main():
    source_commit=clone_source()
    package_root=SRC/"downloads/online4tech"
    packages=sorted([p for p in package_root.rglob("*.ipk") if p.is_file()])
    if not packages: raise RuntimeError("No source-tree IPK packages found.")
    images=copy_artwork()
    releases={}; existing={}
    for kind in ("plugin","skin"):
        tag=f"o4t-source-tree-{kind}-ipk-library-20261124"
        releases[kind]=get_release(tag,f"Online4Tech Source-Tree {kind.title()} IPK Library",
          f"IPK packages imported from online4tech/online4Tech main at {source_commit}. Original package bytes and filenames are preserved. Source repository is unchanged.")
        existing[kind]=list_assets(releases[kind])
    groups={}; package_rows=[]
    for p in packages:
        kind,addon_id=package_group(p)
        relpath=p.relative_to(SRC).as_posix()
        asset_name=f"{addon_id}--{re.sub(r'[^A-Za-z0-9._-]+','-',relpath.replace('/','__'))}"
        asset,sha,size=upload_asset(releases[kind],p,asset_name,existing[kind])
        row={"kind":kind,"addon_id":addon_id,"source_path":relpath,"original_filename":p.name,"asset_name":asset_name,
             "size_bytes":size,"sha256":sha,"download_url":asset["browser_download_url"]}
        package_rows.append(row); groups.setdefault((kind,addon_id),[]).append(row)
        print(f"UPLOADED {kind}/{addon_id}: {p.name} ({size:,} bytes)",flush=True)
    for (kind,addon_id),variants in sorted(groups.items()):
        folder=ROOT/("plugins" if kind=="plugin" else "skins")/addon_id
        folder.mkdir(parents=True,exist_ok=True)
        image_root=ROOT/"assets"/("plugins" if kind=="plugin" else "skins")/addon_id
        imgs=sorted([p for p in image_root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXT]) if image_root.exists() else []
        icon=""
        for preferred in ("icon.png","logo.png","icon.webp","logo.webp","cover.png","cover.webp"):
            hit=next((p for p in imgs if p.name.lower()==preferred),None)
            if hit: icon=hit.relative_to(ROOT).as_posix(); break
        if not icon and imgs: icon=imgs[0].relative_to(ROOT).as_posix()
        shots=[p.relative_to(ROOT).as_posix() for p in imgs if p.relative_to(ROOT).as_posix()!=icon]
        chosen=sorted(variants,key=lambda x:(("openatv" in x["original_filename"].lower()),x["original_filename"].lower()))[-1]
        metadata={"id":addon_id,"name":title(addon_id),"description":f"ملفات {title(addon_id)} المستوردة من مكتبة Online4Tech.",
          "version":"source-import-2026-11-24","status":"published","package_url":chosen["download_url"],"package_format":"ipk",
          "icon":icon,"screenshots":shots,"supported_models":[],"compatibility_status":"unverified",
          "available_packages":[{"filename":x["original_filename"],"download_url":x["download_url"],"sha256":x["sha256"]} for x in variants],
          "source_repository":"online4tech/online4Tech","source_commit":source_commit}
        (folder/"addon.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        latest={"status":"published","version":metadata["version"],"package_format":"ipk","package_url":chosen["download_url"],
          "sha256":chosen["sha256"],"compatibility_status":"unverified","source_repository":"online4tech/online4Tech","source_commit":source_commit}
        (folder/"latest.json").write_text(json.dumps(latest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        (folder/"SOURCE.md").write_text(
          f"# Source and provenance\n\n- Source repository: https://github.com/online4tech/online4Tech\n- Source commit: {source_commit}\n- Original paths and SHA-256 values: catalog/source-tree-ipk-import.json\n- Package payloads are unchanged. Compatibility remains unverified until tested on a receiver.\n",
          encoding="utf-8")
    manifest={"schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),"source_repository":"online4tech/online4Tech",
      "source_commit":source_commit,"source_modifications":"none","ipk_count":len(package_rows),"image_count":len(images),
      "packages":package_rows,"images":images,"release_urls":{k:v["html_url"] for k,v in releases.items()}}
    (ROOT/"catalog/source-tree-ipk-import.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"IMPORT COMPLETE: {len(package_rows)} IPKs, {len(images)} artwork files, {len(groups)} catalog entries.",flush=True)

if __name__=="__main__": main()
