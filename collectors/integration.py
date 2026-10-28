"""Validation continue des agendas candidats avec les seuls connecteurs prédéfinis."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timedelta,timezone
from urllib.parse import urlsplit,urljoin
import re
from bs4 import BeautifulSoup
from .network import Fetcher,RequestBudget
from .model import canonical,make_event,compact,now,parse_date
from .connectors import extract,calendar_links,feed_links,detail_links
from .quality import clean_catalog

MANUAL_GROUPS={'Réseaux et annonces manuelles','Plateformes transversales'}


def agenda_links(text,base):
    soup=BeautifulSoup(text,'html.parser');out=[]
    for a in soup.find_all('a',href=True):
        label=a.get_text(' ',strip=True);url=canonical(urljoin(base,a['href']))
        if not url or url==canonical(base) or a['href'].startswith('#') or urlsplit(url).netloc!=urlsplit(base).netloc:continue
        if re.search(r'\b(agenda|calendrier|événements|evenements|events|seminars|séminaires)\b',label,re.I):out.append(url)
    return list(dict.fromkeys(out))


def eligible(source,registry):
    if source['group'] in MANUAL_GROUPS or 'Export d’événement' in source.get('status','') or re.search(r'/agenda/\d+/ical/?|[?&]method=ical&.*id=',source['url']):return False
    if source.get('enabled') and source.get('lastResult')=='ok':return False
    if source.get('discoveredAt'):
        parent=next((s for s in registry if s['id']==source.get('parentId')),None)
        if not parent or urlsplit(source['url']).netloc!=urlsplit(source.get('discoveredFrom','')).netloc:return False
        if not re.search(r'agenda|calendar|seminar|séminaire|événement|evenement|events|rss|feed|\.ics',source['name']+' '+source['url'],re.I):return False
    return True


def validate_source(original,budget):
    source=dict(original);source['lastIntegrationAttempt']=now();fetcher=Fetcher(10,shared_budget=budget);records=[];errors=[];pages=[]
    try:
        try:body,base,kind=fetcher.get(source['url'])
        except Exception as e:
            # A stale path returning 404 can be rediscovered from its institution's public homepage.
            if getattr(getattr(e,'response',None),'status_code',None) not in (404,410):raise
            origin=urlsplit(source['url']);body,base,kind=fetcher.get(f'{origin.scheme}://{origin.netloc}/')
        pages.append((source,body,base))
        is_feed=source.get('connector')=='feed' or 'application/rss' in kind or body.lstrip().startswith('<rss')
        links=feed_links(body,base) if is_feed else []
        if not is_feed:records+=extract(body,base,source,source.get('connector'))
        if records:
            dated=sorted(records,key=lambda e:((parse_date(e.get('end')) or parse_date(e.get('start')) or '')[:10]<now()[:10],parse_date(e.get('start')) or ''))
            links+=[e['url'] for e in dated if e.get('url') and canonical(e['url'])!=canonical(base) and urlsplit(e['url']).netloc==urlsplit(base).netloc][:2]
        feeds=calendar_links(body,base) if not is_feed else []
        if not records:
            # This is an extraction validation sample, not a limit on future collection.
            links+=detail_links(body,base)[:2]+agenda_links(body,base)[:2]
        for feed in feeds[:2]:
            if fetcher.requests>=8:break
            try:
                text,url,typ=fetcher.get(feed['url'])
                if feed['format']=='feed':links+=feed_links(text,url)[:2]
                else:records+=extract(text,url,source,'ics')
            except Exception as e:errors.append(str(e)[:180])
        for link in list(dict.fromkeys(links))[:3]:
            if fetcher.requests>=9:break
            try:
                text,url,_=fetcher.get(link);new=extract(text,url,source);records+=new;pages.append((source,text,url))
                if new and not is_feed and not extract(body,base,source) and re.search(r'/(?:agenda|evenements|events|seminaires)/?$',urlsplit(url).path):base=url
            except Exception as e:errors.append(str(e)[:180])
        valid=[e for raw in records if (e:=make_event(raw,source))]
        valid,_=clean_catalog(compact(valid))
        if valid:
            if source.get('discoveredAt') and source.get('connector')=='ics' and len(valid)==1:
                source.update(enabled=False,status='Export d’événement — source parente collectée');return source,valid,pages
            source.pop('lastCheckError',None);source.pop('lastIntegrationError',None)
            source.update(enabled=True,status='Connecteur validé automatiquement',lastResult='ok',lastEventCount=len(valid),lastSuccess=now(),lastAttempt=now(),lastCheck=now(),verifiedUrl=base,note='Extraction de dates et de liens testée sur une page publique institutionnelle. Les champs manquants restent inconnus.',errors=[{'error':e} for e in errors])
            if not is_feed and source['url']!=base:source['url']=base
            return source,valid,pages
        source.update(lastIntegrationError='Aucune extraction datée et rattachée à un événement ; connecteur spécifique nécessaire',lastCheck=now(),verifiedUrl=base,lastResult='empty',lastEventCount=0,lastAttempt=now(),status='Extraction vide — contrôle nécessaire')
    except Exception as e:source.update(lastIntegrationError=str(e)[:280],lastResult='error',lastAttempt=now(),status='Indisponible')
    return source,[],pages


def integrate(registry,http_budget=320,workers=4):
    for source in registry:
        parent=next((s for s in registry if s['id']==source.get('parentId')),None)
        if parent:source['organizerName']=parent.get('organizerName') or parent['name']
    candidates=[s for s in registry if eligible(s,registry)]
    candidates.sort(key=lambda s:(s.get('lastIntegrationAttempt',''),not s.get('priority',False),bool(s.get('discoveredAt'))))
    budget=RequestBudget(http_budget);updates={};events=[];pages=[]
    # At most four independent sources at once; the network layer spaces all requests per host.
    with ThreadPoolExecutor(max_workers=workers) as pool:
        pending={};queue=iter(candidates)
        def fill():
            while len(pending)<workers and budget.used<budget.limit:
                try:source=next(queue)
                except StopIteration:break
                pending[pool.submit(validate_source,source,budget)]=source['id']
        fill()
        while pending:
            done=next(as_completed(pending));pending.pop(done)
            source,new,discovered=done.result();updates[source['id']]=source;events+=new;pages+=discovered
            print('INTÉGRATION',source['name'],len(new),source.get('lastIntegrationError','validée'),flush=True)
            fill()
    return [updates.get(s['id'],s) for s in registry],events,pages,{'tested':len(updates),'activated':sum(bool(s.get('enabled')) and s.get('lastResult')=='ok' for s in updates.values()),'httpRequests':budget.used}
