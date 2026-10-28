"""Import ponctuel d'une URL publique demandé par le propriétaire via GitHub Issues."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit,parse_qsl
from .network import Fetcher
from .connectors import extract
from .model import canonical,make_event,compact,reconcile,now
from .quality import clean_catalog
from .audit import coverage
from .pipeline import read,write,ROOT


def public_url(value):
    url=canonical(value)
    if not url:raise ValueError('URL HTTP(S) valide requise')
    if any(re.search(r'token|password|secret|signature|api[_-]?key|^sig$',key,re.I) for key,_ in parse_qsl(urlsplit(url).query)):
        raise ValueError('Les liens avec un jeton ou une signature privée ne peuvent pas être publiés')
    return url


def request_url(payload):
    if payload.get('action') not in ('opened','edited'):raise ValueError('Action non autorisée')
    owner=payload.get('repository',{}).get('owner',{}).get('login')
    issue=payload.get('issue',{})
    if not owner or issue.get('user',{}).get('login')!=owner or payload.get('sender',{}).get('login')!=owner:raise PermissionError('Seul le propriétaire du dépôt peut demander un import')
    body=issue.get('body') or ''
    if not issue.get('title','').startswith('[Import public]') or not body.startswith('SACLAY_RADAR_PUBLIC_IMPORT_V1'):raise ValueError('Demande d’import non reconnue')
    match=re.search(r'^URL:\s*(https?://\S+)\s*$',body,re.M)
    if not match:raise ValueError('Lien public absent de la demande')
    return public_url(match[1]),issue.get('number')


def import_events(url,registry,fetcher):
    url=public_url(url);body,final,_=fetcher.get(url)
    known=next((s for s in registry if urlsplit(s['url']).netloc==urlsplit(final).netloc and not s.get('discoveredAt')),None)
    source={'id':'url-'+hashlib.sha256(final.encode()).hexdigest()[:12],'name':known['name'] if known else 'Annonce publique — '+urlsplit(final).hostname,'url':final,'group':'Ajouts publics depuis une URL','connector':'auto','enabled':False,'priority':False,'status':'Extraction ponctuelle depuis une URL','reliability':'Élevée' if known else 'Faible','lastCheck':now(),'verifiedUrl':final,'note':'Import ponctuel demandé par le propriétaire. Ne constitue pas une surveillance quotidienne de cet organisateur.'}
    events=[e for raw in extract(body,final,source) if (e:=make_event(raw,source))]
    events,_=clean_catalog(compact(events))
    if not events:raise ValueError('Aucun événement daté rattaché à cette page. Le formulaire manuel reste disponible ; aucune date n’a été inventée.')
    source.update(lastSuccess=now(),lastEventCount=len(events),lastResult='ok',lastAttempt=now())
    return events,source


def run(url,number=None):
    os.chdir(ROOT);url=public_url(url);at=now();registry=read('data/sources.json',[]);previous=read('public/data/events.json',[]);run=read('public/data/run.json',{})
    entry={'url':url,'issueNumber':number,'checkedAt':at,'status':'error','eventIds':[]}
    try:
        incoming,source=import_events(url,registry,Fetcher(25))
        events=compact(reconcile(previous,incoming))
        if not any(s['id']==source['id'] for s in registry):registry.append(source)
        else:registry=[source if s['id']==source['id'] else s for s in registry]
        entry.update(status='imported',message=f'{len(incoming)} annonce(s) extraite(s) et validée(s). Les événements terminés sont accessibles dans les archives.',eventIds=[e['id'] for e in events if any(e['url']==x['url'] and e['start']==x['start'] for x in incoming)])
        run.update(lastSuccessfulCollection=now(),finishedAt=now(),status='Import public depuis une URL réussi',reprocessed=False,scheduled=bool(os.getenv('GITHUB_ACTIONS')))
        if os.getenv('GITHUB_RUN_ID'):run['workflowRunUrl']=f"https://github.com/{os.getenv('GITHUB_REPOSITORY')}/actions/runs/{os.getenv('GITHUB_RUN_ID')}"
        write('public/data/events.json',events);write('data/sources.json',registry);write('public/data/sources.json',registry);write('public/data/run.json',run);write('public/data/coverage.json',coverage(registry,events,run))
    except Exception as e:entry['message']='Extraction non réalisée : '+str(e)[:350]
    report=read('public/data/imports.json',{'requests':[]})
    report['requests']=[entry]+[x for x in report['requests'] if x['url']!=url]
    write('public/data/imports.json',report);print(entry['status'],entry['message'])
    return entry

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url');args=parser.parse_args()
    if args.url:run(args.url)
    else:
        payload=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text());url,number=request_url(payload);run(url,number)
