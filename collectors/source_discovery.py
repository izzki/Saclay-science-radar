"""Découverte par liens et autodéclaration de flux ; aucun moteur de recherche requis."""
import hashlib
import re
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup
from .connectors import calendar_links,extract
from .model import canonical,now,make_event

BLOCKED=('linkedin.com','instagram.com','facebook.com','x.com','twitter.com','meetup.com')

def candidates(text,base):
    soup=BeautifulSoup(text,'html.parser');result=calendar_links(text,base)
    for a in soup.find_all('a',href=True):
        label=a.get_text(' ',strip=True);url=canonical(urljoin(base,a['href']))
        if not url:continue
        if re.search(r'agenda|calendar|séminaires|seminars|événements|events|laboratoires|laboratories',label,re.I):
            result.append({'url':url,'label':label,'format':'auto'})
    return list({c['url']:c for c in result}.values())

def discover(registry,fetcher,pages,report):
    known={canonical(s['url']) for s in registry};added=[]
    for parent,text,base in pages:
        for candidate in candidates(text,base):
            url=candidate['url']
            if url in known:continue
            known.add(url)
            same_origin=urlsplit(url).netloc==urlsplit(base).netloc
            source={'id':'auto-'+hashlib.sha256(url.encode()).hexdigest()[:12], 'name':candidate['label'] or parent['name']+' — flux',
                'url':url,'group':parent['group'],'connector':candidate['format'],'enabled':False,'priority':False,
                'status':'Source découverte — intégration nécessaire','discoveredAt':now(),
                'discoveredFrom':base,'parentId':parent['id'],'reliability':'Élevée' if same_origin else 'Moyenne',
                'note':'Lien découvert automatiquement ; légitimité et périmètre à confirmer.'}
            if any(urlsplit(url).hostname==h or urlsplit(url).hostname.endswith('.'+h) for h in BLOCKED):
                source['status']='Surveillance automatique indisponible'
            elif same_origin and candidate['format']=='ics':
                try:
                    body,final,_=fetcher.get(url);raw=extract(body,final,source,'ics')
                    valid=[make_event(e,source) for e in raw]
                    if any(valid):
                        source.update(enabled=True,status='Connecteur validé',note='ICS du même domaine officiel ; extraction de dates valides testée.',verifiedUrl=final,lastCheck=now())
                except Exception as e:source['note']='Test automatique : '+str(e)[:220]
            elif not same_origin:source['note']='Lien externe découvert : validation institutionnelle nécessaire avant activation.'
            added.append(source)
    registry.extend(added);report['newSources']=len(added)
    return registry
