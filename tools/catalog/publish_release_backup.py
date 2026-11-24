#!/usr/bin/env python3
"""Publish/index receiver backups stored as GitHub Release assets."""
from __future__ import annotations
import argparse, json, os, re, tempfile
from datetime import date
from pathlib import Path
from urllib.parse import quote
import requests

ROOT = Path(__file__).resolve().parents[2]
API = "https://api.github.com"
REPO = os.environ.get("TARGET_REPO", "online4tech/Online4Tech-Repository")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"
ARCHIVES = (".zip", ".tar", ".tar.gz", ".tgz", ".gz", ".xz", ".7z", ".img", ".bin", ".backup")
IMAGES = (".png", ".jpg", ".jpeg", ".webp", ".gif")

def api(method, path, **kwargs):
    r = requests.request(method, f"{API}/repos/{REPO}/{path.lstrip('/')}", headers=HEADERS, timeout=90, **kwargs)
    r.raise_for_status()
    return r.json() if r.content else {}

def slug(value):
    return (re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-").lower() or "receiver-backup")[:100]

def release_by_tag(tag):
    return api("GET", f"releases/tags/{quote(tag, safe='')}")

def parse_body(body):
    aliases = {"brand":"brand","model":"device_model","device model":"device_model","version":"version","date":"date","description":"description","compatibility":"compatibility","cover":"cover","source":"source_url","source url":"source_url","id":"id","name":"name"}
    result = {}
    for line in (body or "").splitlines():
        m = re.match(r"^\s*([A-Za-z][A-Za-z _-]*)\s*:\s*(.*?)\s*$", line)
        if m and aliases.get(m.group(1).strip().lower()) and m.group(2):
            result[aliases[m.group(1).strip().lower()]] = m.group(2)
    return result

def metadata_from_release(release):
    body = parse_body(release.get("body", ""))
    title = release.get("name") or release.get("tag_name") or "Receiver Backup"
    parts = [p.strip() for p in title.split("|")]
    if len(parts) >= 3:
        body.setdefault("brand", parts[1]); body.setdefault("device_model", parts[2])
        if len(parts) >= 4: body.setdefault("version", parts[3])
    if not body.get("device_model"):
        raise RuntimeError("Missing receiver model. Add Model: ... to the Release description or use title: Backup | Brand | Model | Version.")
    assets = release.get("assets", [])
    archives = [a for a in assets if a.get("name", "").lower().endswith(ARCHIVES)]
    images = [a for a in assets if a.get("name", "").lower().endswith(IMAGES)]
    package = next((a for a in archives if not any(x in a.get("name", "").lower() for x in ("checksum","sha256","manifest"))), None)
    if not package:
        raise RuntimeError("No recognized backup archive asset found in this Release.")
    cover_asset = next((a for a in images if any(x in a["name"].lower() for x in ("cover","thumb","poster"))), None)
    return {
        "id": body.get("id") or slug(f"{body.get('brand', '')}-{body.get('device_model', '')}") or slug(release["tag_name"]),
        "name": body.get("name") or title,
        "brand": body.get("brand", ""),
        "device_model": body.get("device_model", ""),
        "version": body.get("version", ""),
        "date": body.get("date") or (release.get("published_at", "")[:10] or str(date.today())),
        "description": body.get("description", ""),
        "package_url": package["browser_download_url"],
        "cover": body.get("cover") or (cover_asset["browser_download_url"] if cover_asset else ""),
        "screenshots": [a["browser_download_url"] for a in images if a is not cover_asset],
        "compatibility": body.get("compatibility", ""),
        "source_url": body.get("source_url", ""),
        "status": "published", "release_url": release.get("html_url", ""),
        "release_tag": release["tag_name"], "published_at": release.get("published_at") or release.get("created_at", ""), "asset_name": package["name"], "size": package.get("size", 0)
    }

def save_manifest(meta):
    folder = ROOT / "catalog/uploads/release-backups" / slug(meta["release_tag"])
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "backup.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {folder.relative_to(ROOT)}/backup.json")

def index_release(tag):
    meta = metadata_from_release(release_by_tag(tag))
    save_manifest(meta)
    print(f"Indexed release {tag}: {meta['device_model'] or meta['name']}")

def upload_from_url(args):
    if not args.source_url or not args.tag_name:
        raise RuntimeError("source_url and tag_name are required.")
    tag = args.tag_name.strip()
    try:
        release = release_by_tag(tag)
    except requests.HTTPError as e:
        if e.response is None or e.response.status_code != 404: raise
        title = args.release_name or f"Backup | {args.brand or 'Unknown brand'} | {args.device_model or tag} | {args.version or 'Unspecified'}"
        body = "\n".join([f"Brand: {args.brand}",f"Model: {args.device_model}",f"Version: {args.version}",f"Date: {args.backup_date or date.today().isoformat()}",f"Description: {args.description}",f"Compatibility: {args.compatibility}"])
        release = api("POST", "releases", json={"tag_name":tag,"name":title,"body":body,"draft":True,"prerelease":False})
    name = args.file_name or args.source_url.split("?")[0].rstrip("/").split("/")[-1] or f"{slug(tag)}.zip"
    # Make workflow retries safe: do not upload a duplicate asset with the same name.
    if any(a.get("name") == name for a in release.get("assets", [])):
        print(f"Asset {name} already exists on release {tag}; indexing the existing asset.")
        index_release(tag)
        return
    if not any(name.lower().endswith(ext) for ext in ARCHIVES):
        raise RuntimeError("File name must end with a supported archive extension.")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / name
        print("Downloading source on the GitHub Actions runner.")
        with requests.get(args.source_url, stream=True, timeout=(30,180)) as response:
            response.raise_for_status()
            with path.open("wb") as out:
                for chunk in response.iter_content(1024*1024):
                    if chunk: out.write(chunk)
        if path.stat().st_size >= 2*1024*1024*1024:
            raise RuntimeError("GitHub Release asset must be smaller than 2 GiB.")
        upload_url = release["upload_url"].split("{",1)[0]
        with path.open("rb") as data:
            r = requests.post(upload_url, params={"name":name}, headers={**HEADERS,"Content-Type":"application/octet-stream"}, data=data, timeout=(60,1800))
        r.raise_for_status()
    if release.get("draft"):
        api("PATCH", f"releases/{release['id']}", json={"draft":False})
    index_release(tag)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--index-tag",default="")
    p.add_argument("--source-url",default=os.environ.get("SOURCE_URL",""))
    p.add_argument("--tag-name",default=os.environ.get("TAG_NAME",""))
    p.add_argument("--release-name",default=os.environ.get("RELEASE_NAME",""))
    p.add_argument("--file-name",default=os.environ.get("FILE_NAME",""))
    p.add_argument("--brand",default=os.environ.get("BRAND",""))
    p.add_argument("--device-model",default=os.environ.get("DEVICE_MODEL",""))
    p.add_argument("--version",default=os.environ.get("VERSION",""))
    p.add_argument("--backup-date",default=os.environ.get("BACKUP_DATE",""))
    p.add_argument("--description",default=os.environ.get("DESCRIPTION",""))
    p.add_argument("--compatibility",default=os.environ.get("COMPATIBILITY",""))
    args=p.parse_args()
    if not TOKEN: raise RuntimeError("GITHUB_TOKEN is required.")
    if args.source_url: upload_from_url(args)
    elif args.index_tag: index_release(args.index_tag)
    else:
        event=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
        tag=(event.get("release") or {}).get("tag_name")
        if not tag: raise RuntimeError("Release event did not include a tag.")
        index_release(tag)

if __name__=="__main__": main()
