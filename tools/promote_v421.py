#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, gzip, hashlib, json, re, shutil, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path

VERSION='4.2.1'
RC6_BLOB='3dede116014ae19de2f23f6deabefae139ffa18f'
LEGACY_STABLE_SHA256='5896562604d4985624ad260fbca9e8cf6f76819c8975837c96be1200a92e31db'
STABLE_SHA256='6d3900a2c973dc2d36099fc596b77b21268c11fdc1cff46bba7e66f08d83aba6'
PATCH_NAME='v421-release.patch.gz.b64'
THEME_LOADER_OLD="state.theme = p.theme === 'dark' ? 'dark' : p.theme === 'light' ? 'light' : systemDark ? 'dark' : 'light';"
THEME_LOADER_NEW="state.theme = MANUSCRIPT_THEMES.some(theme => theme.id === p.theme) ? p.theme : systemDark ? 'dark' : 'light';"
CONTRACTS={
 'scroll':'screen-scoped-scroll-ownership-v2',
 'mobile_viewport':'dvh-keyboard-safe-v3',
 'themes':'curated-interface-themes-v2',
 'visual':'editorial-interface-v1.1',
 'stable':'production-stable-v1',
 'certification':'scroll-v2+themes-v2+visual-v1.1',
}

def sha256(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def git_blob(b:bytes)->str:
 h=hashlib.sha1();h.update(f'blob {len(b)}\0'.encode());h.update(b);return h.hexdigest()

def apply_release_fixes(stable:bytes)->bytes:
 text=stable.decode('utf-8')
 old_count=text.count(THEME_LOADER_OLD)
 new_count=text.count(THEME_LOADER_NEW)
 if old_count==1:
  text=text.replace(THEME_LOADER_OLD,THEME_LOADER_NEW,1)
 elif old_count==0 and new_count==1:
  pass
 else:
  raise SystemExit(f'Unexpected interface-theme loader state: old={old_count}, new={new_count}')
 return text.encode('utf-8')

def validate(text:str)->list[dict]:
 checks=[]
 def add(label,ok,detail=''):checks.append({'label':label,'passed':bool(ok),'detail':'' if ok else detail})
 add('Stable title', '<title>Manuscript v4.2.1 Stable</title>' in text)
 required={
  'manuscript-release-channel':'stable',
  'manuscript-stable-contract':CONTRACTS['stable'],
  'manuscript-certification-contract':CONTRACTS['certification'],
  'manuscript-scroll-contract':CONTRACTS['scroll'],
  'manuscript-mobile-viewport-contract':CONTRACTS['mobile_viewport'],
  'manuscript-theme-contract':CONTRACTS['themes'],
  'manuscript-visual-contract':CONTRACTS['visual'],
 }
 for name,value in required.items():
  add(name, re.search(rf'<meta\s+name=["\']{re.escape(name)}["\']\s+content=["\']{re.escape(value)}["\']',text,re.I) is not None)
 add('v401 exactly once', text.count('id="v401-scroll-architecture"')==1)
 add('v411 exactly once', text.count('id="v411-theme-system"')==1)
 add('v421 exactly once', text.count('id="v421-visual-architecture"')==1)
 add('v420 absent', 'id="v420-visual-architecture"' not in text)
 add('RC6 scroll override absent', 'id="rc6-scroll-ownership-fixes"' not in text)
 add('legacy app visual height absent', '--app-visual-height' not in text)
 add('legacy scroll contract absent', 'explicit-scroll-ownership-v1' not in text)
 add('legacy viewport contract absent', 'fit-width-safe-area-pinch-v2' not in text)
 add('manual main-stage arithmetic absent', re.search(r'\.main-stage\s*\{[^}]*height\s*:\s*calc\([^}]*--appbar-h',text,re.S) is None)
 add('six neutral paper themes', text.count('--paper:#fffefa;--paper-muted:#f8f5ec;')>=6)
 add('all curated themes persist', text.count(THEME_LOADER_NEW)==1 and THEME_LOADER_OLD not in text)
 add('HTML doctype', text.lstrip().lower().startswith('<!doctype html'))
 add('APP_VERSION', 'exports.APP_VERSION' not in text or re.search(r'exports\.APP_VERSION\s*=\s*["\']4\.2\.1["\']',text) is not None)
 return checks

def patch_bytes(patch_file:Path)->bytes:
 if patch_file.is_file(): return patch_file.read_bytes()
 parts=sorted(patch_file.parent.glob(patch_file.name+'.part*'))
 if not parts: raise SystemExit(f'Release patch not found: {patch_file}')
 return b''.join(part.read_bytes() for part in parts)

def promote(source:Path,output:Path,manifest:Path,patch_file:Path):
 original=source.read_bytes(); source_sha=sha256(original); source_blob=git_blob(original)
 if source_sha==STABLE_SHA256:
  stable=original
 elif source_sha==LEGACY_STABLE_SHA256:
  stable=apply_release_fixes(original)
 elif source_blob==RC6_BLOB:
  if not shutil.which('git'):raise SystemExit('git is required')
  raw=gzip.decompress(base64.b64decode(patch_bytes(patch_file)))
  with tempfile.TemporaryDirectory(prefix='manuscript-v421-') as td:
   work=Path(td); (work/'index.html').write_bytes(original); (work/'release.patch').write_bytes(raw)
   subprocess.run(['git','init','-q'],cwd=work,check=True)
   subprocess.run(['git','apply','--check','release.patch'],cwd=work,check=True)
   subprocess.run(['git','apply','release.patch'],cwd=work,check=True)
   stable=apply_release_fixes((work/'index.html').read_bytes())
 else:
  raise SystemExit(f'Unsupported source: git blob {source_blob}, sha256 {source_sha}')

 stable_hash=sha256(stable)
 if stable_hash!=STABLE_SHA256:raise SystemExit(f'Stable SHA mismatch: {stable_hash}')
 text=stable.decode('utf-8'); checks=validate(text)
 failed=[c for c in checks if not c['passed']]
 if failed:raise SystemExit('Static Stable checks failed: '+json.dumps(failed))
 output.write_bytes(stable)
 payload={
  'schema':'manuscript-release-manifest-v1','product':'Manuscript','version':VERSION,'channel':'stable',
  'release_name':'Manuscript v4.2.1 Stable','generated_at_utc':datetime.now(timezone.utc).isoformat(),
  'source':{'filename':source.name,'bytes':len(original),'sha256':source_sha,'git_blob_sha1':source_blob},
  'artifact':{'filename':output.name,'bytes':len(stable),'sha256':stable_hash},
  'contracts':CONTRACTS,'checks':checks,
  'summary':{'passed':sum(c['passed'] for c in checks),'total':len(checks),'stable_promotion_passed':all(c['passed'] for c in checks)}
 }
 manifest.write_text(json.dumps(payload,indent=2),encoding='utf-8')
 print(f"Stable promotion PASS — {payload['summary']['passed']}/{payload['summary']['total']} static checks")
 print(f'SHA256 {stable_hash}')

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--output',type=Path,default=Path('Manuscript_v4.2.1_Stable.html'));ap.add_argument('--manifest',type=Path,default=Path('Manuscript_v4.2.1_Stable_RELEASE_MANIFEST.json'));ap.add_argument('--patch',type=Path,default=Path(__file__).with_name(PATCH_NAME));a=ap.parse_args();promote(a.source,a.output,a.manifest,a.patch)