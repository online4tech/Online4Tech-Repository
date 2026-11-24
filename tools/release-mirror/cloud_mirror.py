#!/usr/bin/env python3
"""Resumable cloud-side mirror of public GitHub Release assets. Never executes packages."""
import argparse, base64, hashlib, json, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
import requests

API = "https://api.github.com"
TARGET = os.getenv("TARGET_REPO", "online4tech/Online4Tech-Repository")
TOKEN = os.environ["GITHUB_TOKEN"]
H = {"Accept":"application/vnd.github+json","Authorization":f"Bearer {TOKEN}",
     "X-GitHub-Api-Version":"2022-11-28"}
ROOT = Path(__file__).resolve().parents[2]
INV = ROOT/"catalog"/"release-assets-inventory.json"
PROGRESS = ROOT/"catalog"/"mirror-progress.json"
TMP = Path(os.getenv("RUNNER_TEMP","/tmp"))/"o4t-cloud-mirror"
TMP.mkdir(parents=True,exist_ok=True)
CATEGORIES = ["small-first","skins","plugins","picons","scripts","other","bridge_tools","receiver_backups"]
MAX_ASSET = 2*1024**3
MAX_BATCH = int(1.65*1024**3)
MAX_FILES = 20
S = requests.Session()
S.headers.update(H)

def api(method,path,**kw):
    url=path if path.startswith("https://") else API+path
    for n in range(5):
        r=S.request(method,url,timeout=(30,300),**kw)
        if r.status_code in (200,201,202,204): return r
        if r.status_code in (429,500,502,503,504) and n<4:
            time.sleep(8*(n+1)); continue
        raise RuntimeError(f"GitHub API {method} {r.status_code}: {r.text[:500]}")
    raise RuntimeError("GitHub API retry limit")

def key(x): return f"{x['repo']}|{x['tag']}|{x['name']}"

def sha_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def read_progress():
    done=set()
    if PROGRESS.exists():
        try: done.update(json.loads(PROGRESS.read_text(encoding="utf-8-sig")).get("completed_keys",[]))
        except Exception: pass
    # Reconstruct prior successful batches directly from target prerelease manifests.
    page=1
    while True:
        releases=api("GET",f"/repos/{TARGET}/releases?per_page=100&page={page}").json()
        if not releases: break
        for rel in releases:
            for asset in rel.get("assets",[]):
                if asset.get("name")!="mirror-manifest.json": continue
                try:
                    raw=requests.get(asset["browser_download_url"],timeout=(20,120))
                    raw.raise_for_status()
                    m=raw.json()
                    if m.get("verification")=="PASS":
                        done.update(m.get("completed_keys",[]))
                except Exception as e:
                    print(f"NOTICE: couldn't read old manifest {rel.get('tag_name')}: {e}",flush=True)
        if len(releases)<100: break
        page+=1
    return done

def save_progress(done):
    obj={"schema_version":1,"updated_at":datetime.now(timezone.utc).isoformat(),
         "completed_count":len(done),"completed_keys":sorted(done),
         "note":"Only assets in fully verified PASS mirror batches are listed."}
    content=json.dumps(obj,ensure_ascii=False,indent=2)+"\n"
    path="catalog/mirror-progress.json"
    try:
        old=api("GET",f"/repos/{TARGET}/contents/{path}").json()
        sha=old["sha"]
    except RuntimeError as e:
        if " 404:" not in str(e): raise
        sha=None
    payload={"message":f"Update cloud mirror checkpoint ({len(done)} verified assets)",
             "content":base64.b64encode(content.encode()).decode(),"branch":"main"}
    if sha: payload["sha"]=sha
    api("PUT",f"/repos/{TARGET}/contents/{path}",json=payload)
    PROGRESS.write_text(content,encoding="utf-8")

def inventory_items():
    data=json.loads(INV.read_text(encoding="utf-8-sig"))
    out=[]
    for rel in data.get("releases",[]):
        for a in rel.get("assets",[]):
            x={"repo":rel["repo"],"tag":rel["tag"],"release_url":rel.get("html_url",""),
               "name":a["name"],"size":int(a.get("size_bytes",0)),
               "type":a.get("content_type") or "application/octet-stream",
               "url":a["download_url"],"digest":(a.get("digest") or "").lower().removeprefix("sha256:"),
               "category":a.get("category") or "other"}
            if x["size"]>0 and x["size"]<MAX_ASSET: out.append(x)
    return out

def choose(items,done,cat):
    rows=[]
    for x in items:
        if key(x) in done: continue
        if cat=="small-first":
            if x["category"] not in ("skins","plugins","picons"): continue
            pr={"skins":0,"plugins":1,"picons":2}[x["category"]]
        elif x["category"]==cat: pr=0
        else: continue
        rows.append((pr,x["size"],x["repo"],x["tag"],x["name"],x))
    rows.sort(key=lambda z:z[:-1])
    batch=[]; total=0
    for row in rows:
        x=row[-1]
        if len(batch)>=MAX_FILES: break
        if total+x["size"]>MAX_BATCH: continue
        batch.append(x); total+=x["size"]
    return batch

def download(x,p):
    h=hashlib.sha256(); n=0
    with requests.get(x["url"],stream=True,timeout=(30,300)) as r:
        r.raise_for_status()
        with open(p,"wb") as f:
            for b in r.iter_content(1024*1024):
                if b: f.write(b); h.update(b); n+=len(b)
    digest=h.hexdigest()
    if n!=x["size"]: raise RuntimeError(f"Source size mismatch: {x['repo']} {x['tag']} {x['name']}")
    if x["digest"] and digest!=x["digest"]:
        raise RuntimeError(f"Source SHA-256 changed; manual inventory review required: {x['name']}")
    return n,digest

def create_release(cat):
    stamp=datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    tag=f"o4t-mirror-{cat}-{stamp}"
    body={"tag_name":tag,"name":f"Online4Tech Cloud Mirror — {cat} — {stamp}",
          "body":"Cloud-side mirror. Source repository, original release, source URL and asset attribution are preserved in mirror-manifest.json. No source was modified.",
          "draft":False,"prerelease":True}
    return api("POST",f"/repos/{TARGET}/releases",json=body).json()

def upload(rel,path,name,ctype):
    url=rel["upload_url"].split("{",1)[0]
    headers={"Authorization":f"Bearer {TOKEN}","Accept":"application/vnd.github+json","Content-Type":ctype}
    with open(path,"rb") as f:
        for n in range(5):
            r=requests.post(url,params={"name":name},headers=headers,data=f,timeout=(30,900))
            if r.status_code==201: return r.json()
            if r.status_code in (429,500,502,503,504) and n<4:
                time.sleep(10*(n+1)); f.seek(0); continue
            raise RuntimeError(f"Upload failed {name}: {r.status_code} {r.text[:350]}")
    raise RuntimeError(f"Upload retry limit: {name}")

def remote_ok(asset,size,digest):
    if not asset or int(asset.get("size",-1))!=size: return False
    remote=(asset.get("digest") or "").lower().removeprefix("sha256:")
    if remote: return remote==digest
    h=hashlib.sha256()
    with requests.get(asset["browser_download_url"],stream=True,timeout=(30,300)) as r:
        r.raise_for_status()
        for b in r.iter_content(1024*1024):
            if b: h.update(b)
    return h.hexdigest()==digest

def run_batch(cat,batch,done):
    rel=create_release(cat); tag=rel["tag_name"]; folder=TMP/tag
    folder.mkdir(parents=True,exist_ok=True)
    files=[]; sums=[]
    print(f"BATCH {tag}: {len(batch)} assets; {rel['html_url']}",flush=True)
    for i,x in enumerate(batch,1):
        clean=re.sub(r"[^\w.\-()+ ]","_",Path(x["name"]).name,flags=re.UNICODE)
        target=f"{i:04d}--{clean or 'asset.bin'}"; p=folder/target
        print(f"Download {i}/{len(batch)} {x['name']}",flush=True)
        size,digest=download(x,p)
        print(f"Upload {target} ({size:,} bytes)",flush=True)
        upload(rel,p,target,x["type"])
        files.append({"completed_key":key(x),"source_repo":x["repo"],"source_tag":x["tag"],
          "source_asset_name":x["name"],"source_release_url":x["release_url"],"source_download_url":x["url"],
          "category":x["category"],"size_bytes":size,"sha256":digest,"target_asset_name":target})
        sums.append(f"{digest}  {target}")
    manifest={"schema_version":1,"mirror_tag":tag,"target_repository":TARGET,
      "created_at":datetime.now(timezone.utc).isoformat(),"verification":"pending",
      "completed_keys":[z["completed_key"] for z in files],"files":files}
    mp=folder/"mirror-manifest.json"; sp=folder/"SHA256SUMS.txt"
    mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    sp.write_text("\n".join(sums)+"\n",encoding="utf-8")
    upload(rel,mp,"mirror-manifest.json","application/json")
    upload(rel,sp,"SHA256SUMS.txt","text/plain")
    remote={a["name"]:a for a in api("GET",f"/repos/{TARGET}/releases/{rel['id']}/assets?per_page=100").json()}
    for z in files:
        if not remote_ok(remote.get(z["target_asset_name"]),z["size_bytes"],z["sha256"]):
            raise RuntimeError(f"Remote verification failed: {z['target_asset_name']}")
    for name,p in (("mirror-manifest.json",mp),("SHA256SUMS.txt",sp)):
        if not remote_ok(remote.get(name),p.stat().st_size,sha_file(p)):
            raise RuntimeError(f"Remote metadata verification failed: {name}")
    manifest["verification"]="PASS"
    mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    api("DELETE",f"/repos/{TARGET}/releases/assets/{remote['mirror-manifest.json']['id']}")
    final=upload(rel,mp,"mirror-manifest.json","application/json")
    if not remote_ok(final,mp.stat().st_size,sha_file(mp)): raise RuntimeError("Final manifest verification failed")
    done.update(z["completed_key"] for z in files)
    save_progress(done)
    print(f"PASS {tag}; verified completed total={len(done)}",flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dry-run",action="store_true")
    p.add_argument("--category",choices=["all"]+CATEGORIES,default="all")
    a=p.parse_args()
    items=inventory_items(); done=read_progress()
    if a.dry_run:
        print(f"DRY RUN only. Target={TARGET}; recovered verified keys={len(done)}")
        for c in CATEGORIES:
            if a.category in ("all",c):
                b=choose(items,done,c)
                print(f"{c}: next batch {len(b)} assets / {sum(x['size'] for x in b):,} bytes")
        return
    started=time.monotonic()
    for c in CATEGORIES:
        if a.category not in ("all",c): continue
        while time.monotonic()-started < 315*60:
            b=choose(items,done,c)
            if not b:
                print(f"{c}: complete/no pending assets",flush=True); break
            run_batch(c,b,done)
        if time.monotonic()-started >= 315*60:
            print("Time budget reached safely. Verified checkpoint saved; dispatch workflow again to continue.",flush=True)
            return
    print(f"Finished selected categories. Verified assets={len(done)}",flush=True)

if __name__=="__main__":
    try: main()
    except Exception as e:
        print(f"STOPPED SAFELY: {e}",file=sys.stderr,flush=True); raise
