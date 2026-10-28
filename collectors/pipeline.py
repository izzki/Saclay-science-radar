from __future__ import annotations
import argparse
import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit
from .model import make_event,reconcile,now,canonical,compact
from .network import Fetcher
from .connectors import extract,detail_links,calendar_links,feed_links
from .source_discovery import discover
from .audit import coverage
from .quality import prepare_sources,clean_catalog
from .seed_registry import seed
from .integration import integrate
from .maintained_sources import maintained_sources
from .crawl import collection_queue,is_listing_page
from .landing_pages import enrich_forum

ROOT=Path(__file__).resolve().parents[1]

def read(path,default):
    try:return json.loads((ROOT/path).read_text())
    except FileNotFoundError:return default

def write(path,value):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_suffix('.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');temp.replace(p)

def run(args):
    os.chdir(ROOT)
    registry=maintained_sources(prepare_sources(read('data/sources.json',seed())));previous=read('public/data/events.json',[])
    prior=read('public/data/run.json',{})
    fetcher=Fetcher(budget=args.budget)
    report={'startedAt':now(),'lastSuccessfulCollection':prior.get('lastSuccessfulCollection'),'newSources':0,'sources':[],'errors':[],
            'scheduled':bool(os.getenv('GITHUB_ACTIONS')),'workflowRunUrl':f"https://github.com/{os.getenv('GITHUB_REPOSITORY')}/actions/runs/{os.getenv('GITHUB_RUN_ID')}" if os.getenv('GITHUB_RUN_ID') else None,
            'schedule':'06:15 et 16:15 UTC ; sources prioritaires au second passage','discoverySchedule':'Dimanche, 06:15 UTC','auditSchedule':'Premier jour du mois : recalcul des audits indépendants disponibles'}
    incoming=[];pages=[]
    if getattr(args,'integrate',False) and not args.reprocess:
        registry,new,found,integration=integrate(registry,http_budget=max(100,args.budget//2))
        incoming.extend(new);pages.extend(found);report['integration']=integration
    # An individual event export stays attached to its parent agenda.
    for source in registry:
        if source.get('discoveredAt') and source.get('connector')=='ics' and re.search(r'(?:[?&](?:method=ical&(?:[^#]*&)?id=|event_id=|mec-ical=event)|/agenda/\d+/ical/)',source['url']):
            source.update(enabled=False,status='Export d’événement — source parente collectée')
    selected=getattr(args,'source',None)
    active=[] if args.reprocess else [s for s in registry if s.get('enabled') and (not args.priority or s.get('priority')) and (not selected or s['id'] in selected)]
    if selected:report['targetedSources']=selected
    for source_index,source in enumerate(active):
        source_budget=max(6,(args.budget-fetcher.requests)//max(1,len(active)-source_index))
        source_start_requests=fetcher.requests
        if not source.get('enabled') or (args.priority and not source.get('priority')):continue
        source['lastAttempt']=now();records=[];errors=[]
        try:
            body,final,content_type=fetcher.get(source['url']);source.update(verifiedUrl=final,lastCheck=now())
            pages.append((source,body,final))
            is_feed=source.get('connector')=='feed'
            if not is_feed:records.extend(extract(body,final,source,source.get('connector')))
            for extra in source.get('enrichmentUrls',[]):
                if urlsplit(extra).netloc!=urlsplit(final).netloc:continue
                try:
                    text,page_url,_=fetcher.get(extra);pages.append((source,text,page_url))
                    if source['id']=='s103':
                        records=[enrich_forum(raw,text,page_url) for raw in records]
                except Exception as e:errors.append({'url':extra,'error':str(e)[:240]})
            children=[] if is_feed else calendar_links(body,final)
            pending=source.get('pendingDetails',[])
            root_links=feed_links(body,final) if is_feed else [] if source.get('connector')=='edition-landing' else detail_links(body,final)
            links=collection_queue(root_links,[] if source.get('connector')=='edition-landing' else pending,final)
            # A per-run request budget bounds traffic, not catalog size. Unvisited URLs persist.
            source['pendingDetails']=[]
            for child in children:
                if child['url']==canonical(final):continue
                try:
                    text,url,_=fetcher.get(child['url'])
                    if child['format']=='feed':links+=feed_links(text,url)
                    else:records.extend(extract(text,url,source,child['format']))
                except Exception as e:errors.append({'url':child['url'],'error':str(e)[:240]})
            visited=set()
            for index,link in enumerate(links):
                if link in visited or canonical(link)==canonical(final):continue
                if fetcher.requests>=args.budget-10 or fetcher.requests-source_start_requests>=source_budget:
                    source['pendingDetails']=list(dict.fromkeys(links[index:]));break
                if urlsplit(link).netloc!=urlsplit(final).netloc:continue
                visited.add(link)
                try:
                    text,url,_=fetcher.get(link);records.extend(extract(text,url,source));pages.append((source,text,url))
                    # Follow calendar pagination only; no arbitrary recursive crawl.
                    following=[u for u in detail_links(text,url) if is_listing_page(u,final) and u not in visited and u not in links]
                    # Traverse the calendar itself before spending the budget on detail pages.
                    links[index+1:index+1]=collection_queue(following,[],final)
                except Exception as e:errors.append({'url':link,'error':str(e)[:240]})
            valid=[e for e in (make_event(raw,source) for raw in records) if e]
            incoming.extend(valid)
            source.update(lastResult='ok' if valid else 'empty',lastEventCount=len(compact(valid)),errors=errors,
                status='Collecte opérationnelle' if valid and not errors else 'Collecte partielle' if valid else 'Extraction vide — contrôle nécessaire')
            if valid:
                source['lastSuccess']=now()
                source.pop('lastIntegrationError',None);source.pop('lastCheckError',None)
            report['sources'].append({'id':source['id'],'count':source['lastEventCount'],'result':source['lastResult'],'errors':len(errors),'pending':len(source['pendingDetails'])})
            # Diagnostic structure only: makes selector repair possible without copying whole pages.
            if not valid:
                from bs4 import BeautifulSoup
                soup=BeautifulSoup(body,'html.parser')
                print('STRUCTURE',source['name'],json.dumps([{'tag':n.name,'class':n.get('class'),'text':n.get_text(' ',strip=True)[:150]} for n in soup.find_all(['article','time','h2','h3'])][:24],ensure_ascii=False),flush=True)
        except Exception as e:
            source.update(lastResult='error',status='Indisponible',errors=[{'at':now(),'error':str(e)[:300]}])
            report['errors'].append({'source':source['id'],'error':str(e)[:300]})
        print(source['name'],source.get('lastResult'),source.get('lastEventCount',0),flush=True)
    # Fragment links and single-event exports are not independent agendas.
    registry=[s for s in registry if not (s.get('discoveredAt') and (canonical(s['url'])==canonical(s.get('discoveredFrom','')) or (s.get('connector')=='ics' and not s.get('enabled') and not re.search(r'\.ics|/ical|[?&][^=]*ical[^=]*=',s['url'],re.I))))]
    for source in registry:
        if source.get('discoveredAt') and source.get('connector')=='ics' and ('ical' in source['url'] or '.ics' in source['url']) and ('event=' in source['url'] or '/agenda/' in source['url']):
            source.update(enabled=False,status='Export d’événement — source parente collectée')
    if args.discover and not args.reprocess:
        registry=discover(registry,fetcher,pages,report)
        for source in registry:
            if source.get('lastCheck') or source.get('status')=='Surveillance automatique indisponible':continue
            if fetcher.requests>=args.budget-5:break
            try:
                _,final,_=fetcher.get(source['url']);source.update(lastCheck=now(),verifiedUrl=final)
            except Exception as e:source.update(lastCheckError=str(e)[:240])
    # Old parser versions could expose structural headings as announcements.
    # Drop only proven extraction artefacts, never low scores or unknown prices.
    structural={'agenda','evenements','resume','intervenant s','intervenants','abstract','programme','informations pratiques','inscription','lieu','date'}
    from .model import norm
    previous=[e for e in previous if norm(e['title']) not in structural]
    # Replace old detail-page logo links when a precise official link is now available.
    previous=[old for old in previous if not (urlsplit(old['url']).path in ('/','/fr','/en') and any(norm(new['title'])==norm(old['title']) and new['start'][:10]==old['start'][:10] and urlsplit(new['url']).path not in ('/','/fr','/en') for new in incoming))]
    events,quarantine=clean_catalog(compact(reconcile(previous,incoming)))
    saved_quarantine={(q['event']['id'],q['reason']):q for q in read('data/quarantine.json',[])}
    saved_quarantine.update({(q['event']['id'],q['reason']):q for q in quarantine})
    write('data/quarantine.json',list(saved_quarantine.values()))
    report['quarantined']=len(quarantine)
    report['quarantineHistory']=len(saved_quarantine)
    if incoming:report['lastSuccessfulCollection']=now()
    report.update(finishedAt=now(),httpRequests=fetcher.requests,events=len(events),incoming=len(reconcile([],incoming)),newEvents=len([e for e in events if e['id'] not in {p['id'] for p in previous}]),
        status='Succès partiel' if report['errors'] or any(s['result']!='ok' or s.get('errors') or s.get('pending') for s in report['sources']) else 'Succès' if incoming else 'Aucune collecte confirmée')
    if args.reprocess:
        report['status']='Données récentes conservées · vérification du catalogue effectuée'
        report['reprocessed']=True
    cov=coverage(registry,events,report)
    write('data/sources.json',registry);write('public/data/sources.json',registry)
    write('public/data/events.json',events);write('public/data/run.json',report);write('public/data/coverage.json',cov)
    write('data/snapshots/latest.json',{'at':now(),'previousRun':prior,'previousEvents':previous})
    write('data/reports/'+report['startedAt'].replace(':','-').replace('+00-00','Z')+'.json',report)
    # Keep the latest full previous snapshot and dated collection reports. Event change history is persistent.
    if args.audit:write('data/coverage-history/'+report['startedAt'][:10]+'.json',cov)
    print(json.dumps({'events':len(events),'sources':len(registry),'automated':cov['automated'],'discovered':cov['discovered'],'http':fetcher.requests},ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--discover',action='store_true');parser.add_argument('--integrate',action='store_true');parser.add_argument('--audit',action='store_true');parser.add_argument('--priority',action='store_true');parser.add_argument('--reprocess',action='store_true');parser.add_argument('--source',action='append',help='Collecter uniquement ces identifiants de sources');parser.add_argument('--budget',type=int,default=350)
    run(parser.parse_args())
