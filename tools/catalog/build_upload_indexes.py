#!/usr/bin/env python3
"""Build public indexes from uploaded Online4Tech plugin, skin and backup folders."""
from __future__ import annotations
import json, os, re
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
REPO = "online4tech/Online4Tech-Repository"
RAW = f"https://raw.githubusercontent.com/{REPO}/main/"
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
PACKAGE_EXT = {".ipk", ".deb", ".zip", ".tar", ".gz", ".tgz", ".xz", ".sh"}

def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()

def public(p: str) -> str:
    return RAW + p

def read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}

def files(folder: Path):
    return [p for p in folder.rglob("*") if p.is_file() and not p.name.startswith(".")]

def choose_image(folder: Path, names):
    all_files = files(folder)
    for name in names:
        hit = next((p for p in all_files if p.name.lower() == name.lower()), None)
        if hit and hit.suffix.lower() in IMAGE_EXT:
            return rel(hit)
    return ""

def build_addons(kind: str):
    root = ROOT / ("plugins" if kind == "plugin" else "skins")
    items = []
    if not root.exists():
        return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "items": []}
    for folder in sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p:p.name.lower()):
        fs = files(folder)
        meta = read_json(folder / "addon.json") or read_json(folder / "latest.json")
        package = next((p for p in fs if p.suffix.lower() in PACKAGE_EXT and p.name.lower() not in {"install.sh"}), None)
        package_path = str(meta.get("package_path") or "")
        if package_path:
            candidate = ROOT / package_path
            if candidate.is_file(): package = candidate
        package_url = str(meta.get("package_url") or (public(rel(package)) if package else ""))
        if not package_url and not package:
            continue
        addon_id = str(meta.get("id") or folder.name)
        icon = str(meta.get("icon") or choose_image(folder, ["icon.png","icon.webp","logo.png","logo.webp","cover.png","cover.webp"]))
        shots = meta.get("screenshots")
        if not isinstance(shots, list):
            shots = [rel(p) for p in fs if p.suffix.lower() in IMAGE_EXT and "screenshot" in p.name.lower()]
        else:
            shots = [x if str(x).startswith("http") else str(x).replace("\\","/") for x in shots]
        # Paths in metadata are repository-relative unless already absolute.
        icon = icon if icon.startswith("http") or not icon else (icon if icon.startswith(("plugins/","skins/","assets/")) else rel(folder / icon))
        shots = [x if x.startswith("http") or x.startswith(("plugins/","skins/","assets/")) else rel(folder / x) for x in shots]
        install_file = folder / "install.sh"
        install_value = str(meta.get("install_url") or "")
        install_url = install_value if install_value.startswith("http") else (public(install_value if install_value.startswith(("plugins/","skins/")) else rel(folder / install_value)) if install_value else (public(rel(install_file)) if install_file.is_file() else ""))
        latest_file = folder / "latest.json"
        items.append({
            "id": addon_id, "kind": kind, "name": str(meta.get("name") or folder.name.replace("-", " ").title()),
            "description": str(meta.get("description") or ""),
            "status": str(meta.get("status") or "published"),
            "latest_version": str(meta.get("version") or meta.get("latest_version") or ""),
            "package_url": package_url, "package_format": str(meta.get("package_format") or (package.suffix.lstrip(".") if package else "")),
            "available_packages": meta.get("available_packages") if isinstance(meta.get("available_packages"), list) else [],
            "icon": icon if icon.startswith("http") or not icon else public(icon),
            "screenshots": [x if x.startswith("http") else public(x) for x in shots],
            "supported_models": meta.get("supported_models") if isinstance(meta.get("supported_models"), list) else [],
            "compatibility_status": str(meta.get("compatibility_status") or "unverified"),
            "latest_manifest": public(rel(latest_file)) if latest_file.is_file() else "",
            "install_url": install_url if install_url.startswith("http") else (public(install_url) if install_url else "")
        })
    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "items": items}

def build_backups():
    root = ROOT / "backups"
    items = []
    if root.exists():
        for manifest in sorted(root.rglob("backup.json")):
            folder = manifest.parent
            meta = read_json(manifest)
            if not meta:
                continue
            package_url = str(meta.get("package_url") or "")
            package_path = str(meta.get("package_path") or "")
            if package_path:
                candidate = ROOT / package_path
                if candidate.is_file(): package_url = public(rel(candidate))
            if not package_url:
                package = next((p for p in files(folder) if p.suffix.lower() in {".zip",".tar",".gz",".tgz",".xz",".7z"}), None)
                if package: package_url = public(rel(package))
            cover = str(meta.get("cover") or meta.get("image") or "")
            if cover and not cover.startswith("http"):
                cover = public(rel(folder / cover) if not cover.startswith("backups/") else cover)
            shots = meta.get("screenshots", [])
            if not isinstance(shots, list): shots = []
            shots = [x if str(x).startswith("http") else public(rel(folder / str(x)) if not str(x).startswith("backups/") else str(x)) for x in shots]
            if not cover:
                cover = next((public(rel(p)) for p in files(folder) if p.suffix.lower() in IMAGE_EXT), "")
            items.append({
                "id": str(meta.get("id") or folder.name), "name": str(meta.get("name") or folder.name.replace("-"," ").title()),
                "device_model": str(meta.get("device_model") or folder.parent.name.replace("-"," ").title()),
                "brand": str(meta.get("brand") or folder.parent.parent.name.replace("-"," ").title()),
                "version": str(meta.get("version") or ""), "date": str(meta.get("date") or ""),
                "description": str(meta.get("description") or ""), "package_url": package_url,
                "cover": cover, "screenshots": shots, "compatibility": str(meta.get("compatibility") or ""),
                "source_url": str(meta.get("source_url") or ""), "status": str(meta.get("status") or "published")
            })
    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "items": items}

def write(path: str, data: dict):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def main():
    write("catalog/addons/plugins.json", build_addons("plugin"))
    write("catalog/addons/skins.json", build_addons("skin"))
    write("catalog/uploads/backups.json", build_backups())
    print("Indexes rebuilt from plugins/, skins/ and backups/.")
if __name__ == "__main__":
    main()
