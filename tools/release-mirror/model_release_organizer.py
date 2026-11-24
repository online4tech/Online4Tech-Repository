#!/usr/bin/env python3
"""Copy verified mirrored receiver backups into dedicated model releases. Never alter existing releases."""
import base64, hashlib, json, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
import requests
API="https://api.github.com"; TARGET=os.getenv("TARGET_REPO","online4tech/Online4Tech-Repository")
TOKEN=os.environ["GITHUB_TOKEN"]; H={"Accept":"application/vnd.github+json","Authorization":f"Bearer {TOKEN}","X-GitHub-Api-Version":"2022-11-28"}
ROOT=Path(__file__).resolve().parents[2]; INV=ROOT/"catalog/release-assets-inventory.json"
TMP=Path(os.getenv("RUNNER_TEMP","/tmp"))/"o4t-model-releases"; TMP.mkdir(parents=True,exist_ok=True)
S=requests.Session(); S.headers.update(H); MAX_SECONDS=315*60
MODELS=[
("Dreambox DM520","dreambox-dm520",r"dm520"),("Dreambox Two","dreambox-two",r"dreamtwo"),
("Vu+ Zero 4K","vu-zero-4k",r"vuzero4k"),("Vu+ Zero","vu-zero",r"vuzero(?!4k)"),
("Vu+ Duo 4K SE","vu-duo-4k-se",r"vuduo4kse"),("Vu+ Duo 4K","vu-duo-4k",r"vuduo4k(?!se)"),
("Vu+ Uno 4K SE","vu-uno-4k-se",r"vuuno4kse"),("Vu+ Uno 4K","vu-uno-4k",r"vuuno4k(?!se)"),
("Vu+ Ultimo 4K","vu-ultimo-4k",r"vuultimo4k"),("Vu+ Solo 4K","vu-solo-4k",r"vusolo4k"),
("Novaler 4K Pro","novaler-4k-pro",r"novaler4kpro"),("Novaler 4K","novaler-4k",r"novaler4k"),
("Multibox Pro","multibox-pro",r"multiboxpro"),("Novaler Pro","novaler-pro",r"novalerpro"),
("Multibox SE","multibox-se",r"multiboxse"),("Novaler SE","novaler-se",r"novalerse")]
MODELS=[(n,s,re.compile(p,re.I)) for n,s,p in MODELS]

def api(method,path,**kw):
 url=path if path.startswith("https://") else API+path
 for i in range(5):
  r=S.request(method,url,timeout=(30,300),**kw)
  if r.status_code in (200,201,202,204): return r
  if r.status_code in (429,500,502,503,504) and i<4: time.sleep(8*(i+1)); continue
  raise RuntimeError(f"GitHub API {method} {r.status_code}: {r.text[:500]}")
 raise RuntimeError("GitHub API retry limit")
def get(path): return api("GET",path).json()
def k(x): return "|".join([x["repo"],x["tag"],x["name"]])
def put(path,content,msg):
 p=f"/repos/{TARGET}/contents/{path}"
 try: old=get(p); sha=old["sha"]
 except RuntimeError as e:
  if " 404:" not in str(e): raise
  sha=None
 b={"message":msg,"content":base64.b64encode(content.encode()).decode(),"branch":"main"}
 if sha: b["sha"]=sha
 api("PUT",p,json=b)
def read_rows():
 data=json.loads(INV.read_text(encoding="utf-8-sig")); rows=[]
 for rel in data.get("releases",[]):
  for a in rel.get("assets",[]):
   if a.get("category")!="receiver_backups": continue
   x={"repo":rel["repo"],"tag":rel["tag"],"release_name":rel.get("name",""),"release_url":rel.get("html_url",""),
      "name":a["name"],"size":int(a.get("size_bytes",0)),"source_url":a.get("download_url","")}
   hit=next((m for m in MODELS if m[2].search(x["name"]+" "+x["release_name"])),None)
   if not hit: raise RuntimeError("Unclassified backup; stop for manual review: "+x["name"])
   x["model"],x["slug"]=hit[0],hit[1]; rows.append(x)
 return rows
def get_mirrors():
 found={}; releases=[]; page=1
 while True:
  rs=get(f"/repos/{TARGET}/releases?per_page=100&page={page}")
  if not rs: break
  releases.extend(rs)
  for rel in rs:
   ma=next((a for a in rel.get("assets",[]) if a.get("name")=="mirror-manifest.json"),None)
   if not ma: continue
   try:
    r=requests.get(ma["browser_download_url"],timeout=(20,120)); r.raise_for_status()
    m=json.loads(r.content.decode("utf-8-sig"))
    if m.get("verification")!="PASS": continue
    for z in m.get("files",[]):
     kk="|".join([z["source_repo"],z["source_tag"],z["source_asset_name"]])
     found[kk]={"target_name":z["target_asset_name"],"sha256":z["sha256"],"size":int(z["size_bytes"]),
                "mirror_tag":m.get("mirror_tag",""),"url":""}
   except Exception as e: print("NOTICE manifest",rel.get("tag_name"),e,flush=True)
  if len(rs)<100: break
  page+=1
 for rel in releases:
  for a in rel.get("assets",[]):
   for v in found.values():
    if v["mirror_tag"]==rel.get("tag_name") and v["target_name"]==a.get("name"): v["url"]=a["browser_download_url"]
 return found
def model_release(model,slug):
 tag=f"o4t-device-{slug}-backups"
 try: return get(f"/repos/{TARGET}/releases/tags/{tag}")
 except RuntimeError as e:
  if " 404:" not in str(e): raise
 body={"tag_name":tag,"name":f"{model} — Backup Images",
       "body":f"Dedicated backup images for {model} only. Original source releases, attribution, original filenames and SHA-256 values are preserved in the manifest. Previous mixed mirror releases remain unchanged.",
       "draft":False,"prerelease":False}
 return api("POST",f"/repos/{TARGET}/releases",json=body).json()
def list_assets(rel):
 out={}; page=1
 while True:
  batch=get(f"/repos/{TARGET}/releases/{rel['id']}/assets?per_page=100&page={page}")
  for a in batch: out[a["name"]]=a
  if len(batch)<100: break
  page+=1
 return out
def copy_asset(rel,x,m,target):
 if not m.get("url"): raise RuntimeError("Missing central mirror URL: "+k(x))
 p=TMP/("a-"+hashlib.sha1(k(x).encode()).hexdigest()); h=hashlib.sha256(); n=0
 print(f"Copy {x['model']}: {x['name']} ({x['size']:,} bytes)",flush=True)
 with requests.get(m["url"],stream=True,timeout=(30,300)) as r:
  r.raise_for_status()
  with open(p,"wb") as f:
   for b in r.iter_content(1024*1024):
    if b: f.write(b); h.update(b); n+=len(b)
 digest=h.hexdigest()
 if n!=x["size"] or digest!=m["sha256"]:
  p.unlink(missing_ok=True); raise RuntimeError("Central copy SHA/size mismatch: "+x["name"])
 url=rel["upload_url"].split("{",1)[0]
 hh={"Authorization":f"Bearer {TOKEN}","Accept":"application/vnd.github+json","Content-Type":"application/octet-stream"}
 with open(p,"rb") as f: r=requests.post(url,params={"name":target},headers=hh,data=f,timeout=(30,900))
 p.unlink(missing_ok=True)
 if r.status_code!=201: raise RuntimeError(f"Upload failed {target}: {r.status_code} {r.text[:400]}")
 a=r.json()
 if int(a.get("size",-1))!=n: raise RuntimeError("Target size mismatch: "+target)
 rd=(a.get("digest") or "").lower().removeprefix("sha256:")
 if rd and rd!=digest: raise RuntimeError("Target SHA mismatch: "+target)
 return a,digest,n
def process(model,slug,rows,mirrors):
 rel=model_release(model,slug); existing=list_assets(rel); byname={}
 for x in rows: byname.setdefault(x["name"],[]).append(x)
 binaries={}
 for x in rows:
  m=mirrors.get(k(x))
  if not m or not m.get("url"): raise RuntimeError("No verified central mirror: "+k(x))
  binaries.setdefault((x["name"],m["sha256"]),[]).append((x,m))
 files=[]; sums=[]
 for (original,digest),records in sorted(binaries.items(),key=lambda z:z[0][0].lower()):
  x,m=records[0]; target=original
  if len(byname[original])>1:
   stem,ext=os.path.splitext(original); target=f"{stem}--source-{re.sub(r'[^A-Za-z0-9._-]+','-',x['tag'])}{ext}"
  if target in existing:
   a=existing[target]; rd=(a.get("digest") or "").lower().removeprefix("sha256:")
   if int(a.get("size",-1))!=x["size"] or (rd and rd!=digest): raise RuntimeError("Conflicting existing asset: "+target)
   if not rd:
    h=hashlib.sha256(); n=0
    with requests.get(a["browser_download_url"],stream=True,timeout=(30,300)) as r:
     r.raise_for_status()
     for b in r.iter_content(1024*1024):
      if b: h.update(b); n+=len(b)
    if n!=x["size"] or h.hexdigest()!=digest: raise RuntimeError("Existing target SHA mismatch: "+target)
  else:
   a,_,_=copy_asset(rel,x,m,target); existing[target]=a
  sources=[{"repository":sx["repo"],"release_tag":sx["tag"],"release_name":sx["release_name"],
            "release_url":sx["release_url"],"asset_name":sx["name"],"original_download_url":sx["source_url"]} for sx,sm in records]
  files.append({"original_filename":original,"asset_name":target,"size_bytes":x["size"],"sha256":digest,
                "download_url":a["browser_download_url"],"source_records":sources})
  sums.append(f"{digest}  {target}")
 manifest={"schema_version":1,"verification":"PASS","model":model,"release_tag":rel["tag_name"],
  "created_at":datetime.now(timezone.utc).isoformat(),"target_repository":TARGET,
  "source_asset_records":len(rows),"unique_binary_assets":len(files),"files":files}
 cur=list_assets(rel); up=rel["upload_url"].split("{",1)[0]
 for name,content,ctype in [
  ("SHA256SUMS.txt",("\n".join(sums)+"\n").encode(),"text/plain"),
  ("mirror-manifest.json",(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n").encode(),"application/json")]:
  if name in cur: continue
  hh={"Authorization":f"Bearer {TOKEN}","Accept":"application/vnd.github+json","Content-Type":ctype}
  r=requests.post(up,params={"name":name},headers=hh,data=content,timeout=(30,300))
  if r.status_code!=201: raise RuntimeError(f"Metadata upload failed {name}: {r.status_code} {r.text[:300]}")
 return {"model":model,"tag":rel["tag_name"],"url":rel["html_url"],"source_records":len(rows),
         "unique_assets":len(files),"bytes":sum(f["size_bytes"] for f in files),"files":files}
def main():
 rows=read_rows(); mirrors=get_mirrors(); missing=[k(x) for x in rows if k(x) not in mirrors or not mirrors[k(x)].get("url")]
 if missing: raise RuntimeError(f"{len(missing)} backups lack a verified central mirror URL; first={missing[:3]}")
 groups={}
 for x in rows: groups.setdefault((x["model"],x["slug"]),[]).append(x)
 print(f"Prepared {len(rows)} source records across {len(groups)} device models.",flush=True)
 results=[]; started=time.monotonic()
 for (model,slug),items in groups.items():
  if time.monotonic()-started>MAX_SECONDS-600:
   print("Time budget reached. Existing per-model releases are resumable; rerun this workflow to continue.",flush=True); return
  z=process(model,slug,items,mirrors); results.append(z)
  print(f"MODEL PASS {model}: {z['unique_assets']} files — {z['url']}",flush=True)
  state={"schema_version":1,"updated_at":datetime.now(timezone.utc).isoformat(),
         "completed_models":[x["model"] for x in results],"models":results,
         "source_records":len(rows),"total_models":len(groups)}
  put("catalog/model-release-organizer-progress.json",json.dumps(state,ensure_ascii=False,indent=2)+"\n",
      f"Checkpoint model releases ({len(results)}/{len(groups)})")
 if len(results)!=len(groups): raise RuntimeError("Model releases incomplete.")
 print("ALL MODEL RELEASES PASS: "+json.dumps([{"model":x["model"],"url":x["url"],"files":x["unique_assets"]} for x in results],ensure_ascii=False),flush=True)
if __name__=="__main__":
 try: main()
 except Exception as e: print("STOPPED SAFELY:",e,file=sys.stderr,flush=True); raise
