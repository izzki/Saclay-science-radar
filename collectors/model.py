from __future__ import annotations
import hashlib
import html
import re
import unicodedata
from datetime import datetime, date, timezone
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from zoneinfo import ZoneInfo

PARIS = ZoneInfo('Europe/Paris')
MONTHS = {'janvier':1,'fevrier':2,'mars':3,'avril':4,'mai':5,'juin':6,'juillet':7,'aout':8,'septembre':9,'octobre':10,'novembre':11,'decembre':12}

def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def clean(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', str(value or '')))).strip()

def norm(value):
    value = ''.join(c for c in unicodedata.normalize('NFKD', clean(value).lower()) if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', ' ', value).strip()

def canonical(url):
    try:
        p = urlsplit(str(url))
        if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password:
            return ''
        return urlunsplit((p.scheme, p.netloc.lower(), p.path or '/', urlencode([(k,v) for k,v in parse_qsl(p.query) if not k.startswith('utm_') and k not in ('fbclid','gclid')]), ''))
    except ValueError:
        return ''

def parse_date(value, text=False):
    """Date sans heure conservée comme telle ; une heure locale utilise Europe/Paris."""
    value = clean(value)
    if not value: return None
    try:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', value): return date.fromisoformat(value).isoformat()
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return (dt if dt.tzinfo else dt.replace(tzinfo=PARIS)).isoformat()
    except ValueError: pass
    if not text: return None
    n = norm(value)
    m = re.search(r'\b(\d{1,2}) ('+'|'.join(MONTHS)+r') (\d{4})\b', n)
    if m: y,mo,d = int(m[3]),MONTHS[m[2]],int(m[1])
    else:
        m = re.search(r'\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b', value)
        if not m: return None
        d,mo,y=map(int,m.groups())
    try:
        day=date(y,mo,d)
        clock=re.search(r'\b(\d{1,2})\s*[h:]\s*(\d{2})\b',value)
        if clock: return datetime(y,mo,d,int(clock[1]),int(clock[2]),tzinfo=PARIS).isoformat()
        return day.isoformat()
    except ValueError: return None

def category(text):
    n=norm(text)
    for keys,label in [('soutenance these hdr','Soutenance'),('hackathon','Hackathon'),('workshop atelier','Workshop'),('forum recrutement carriere','Forum métiers'),('salon expo','Salon'),('seminaire seminar','Séminaire'),('startup deeptech entrepreneuriat','Deeptech'),('colloque congres conference summit','Conférence'),('visite portes ouvertes','Visite')]:
        if any(k in n for k in keys.split()): return label
    return 'Événement scientifique'

def disciplines(text):
    n=norm(text)
    mapping={'Photonique':['photon','optique','optical','laser'],'Quantique':['quantum','quantique','qubit','atomes neutres','trapped ion'],'Nanosciences':['nano','semiconductor','semi conducteur'],'Instrumentation':['instrument','metrolog','cryogen','sensor','capteur'],'Deeptech':['deeptech','startup','innovation','industrie'],'Informatique':['informatique','comput','intelligence artificielle'],'Physique':['physique','physics','matter','neutron'],'Sciences du vivant':['biolog','bioph','protein','cellul'],'Mathématiques':['mathem','geometr']}
    return [label for label,keys in mapping.items() if any(k in n for k in keys)] or ['Sciences générales']

def score(event):
    n=norm(event['title']+' '+event.get('description',''))
    ds=event['disciplines']
    science=8
    reasons=[]
    if 'Photonique' in ds: science=26; reasons.append('Thématique photonique ou optique annoncée.')
    hardware=any(k in n for k in ['single photon','photon unique','integrated photonic','photonique integre','nanophoton','quantum optic','optique quantique','atomes neutres','neutral atom','trapped ion','ions piege','quantum sensor','metrologie quantique'])
    if hardware: science=35; reasons.append('Lien explicite avec le matériel photonique ou quantique.')
    elif 'Quantique' in ds: science=max(science,17); reasons.append('Quantique mentionné ; caractère expérimental à vérifier.')
    elif 'Instrumentation' in ds or 'Nanosciences' in ds: science=max(science,22)
    network=20 if any(k in n for k in ['networking','rencontre recherche industrie','rencontres recherche industrie','b2b']) else 12 if any(k in n for k in ['forum','salon','exposant','table ronde']) else 4
    careers=10 if any(k in n for k in ['stage','recrutement','cifre','carriere','metiers']) else 5 if 'Deeptech' in ds else 0
    city=norm(event.get('city',''))
    geo=15 if city in ['palaiseau','orsay','gif sur yvette','saclay','bures sur yvette','saint aubin'] else 10 if city=='paris' else 8 if event.get('format')=='En ligne' else 3
    price=event.get('price')
    cost=15 if price==0 else 12 if price is not None and price<10 else 7 if price is not None and price<=30 else 2 if price is not None else 5
    access=norm(event.get('access',''))
    if any(k in access for k in ['reserve aux','sur invitation','acces restreint']): cost=max(0,cost-4)
    level=5 if any(k in n for k in ['grand public','initiation','introduction','vulgarisation']) else 2
    parts={'Adéquation scientifique':science,'Networking annoncé':network,'Proximité':geo,'Coût et accès':cost,'Stages et métiers':careers,'Niveau étudiant':level}
    reasons+=['Networking : '+('rencontres explicitement annoncées.' if network>=12 else 'aucune rencontre professionnelle garantie.'),'Tarif non précisé : à vérifier.' if price is None else 'Tarif publié pris en compte.']
    return {'total':sum(parts.values()),'parts':parts,'reasons':reasons}

def make_event(raw, source, checked=None):
    title=clean(raw.get('title'))
    start=parse_date(raw.get('start'))
    if len(title)<4 or not start: return None
    url=canonical(raw.get('url') or source['url'])
    if not url: return None
    checked=checked or now()
    desc=clean(raw.get('description'))
    text=title+' '+desc
    price=raw.get('price')
    try: price=float(price) if price is not None and price!='' else None
    except (TypeError,ValueError): price=None
    if price is not None and (price<0 or price>100000): price=None
    event={
        'id':hashlib.sha256((url+'|'+start+'|'+norm(title)).encode()).hexdigest()[:20],
        'title':title,'description':desc,'start':start,'end':parse_date(raw.get('end')),'timezone':'Europe/Paris' if len(start)==10 else str(datetime.fromisoformat(start).tzinfo),
        'organizer':clean(raw.get('organizer') or source['name']),
        'location':clean(raw.get('location')) or None,'address':clean(raw.get('address')) or None,'city':clean(raw.get('city')) or None,
        'format':raw.get('format') or 'Non précisé','category':category(text),'disciplines':disciplines(text),
        'price':price,'currency':raw.get('currency') or ('EUR' if price is not None else None),'studentPrice':raw.get('studentPrice'),
        'priceLabel':clean(raw.get('priceLabel')) or ('Gratuit' if price==0 else str(price)+' '+(raw.get('currency') or 'EUR') if price is not None else 'Non précisé'),
        'access':clean(raw.get('access')) or None,'registration':clean(raw.get('registration')) or None,
        'registrationUrl':canonical(raw.get('registrationUrl')) or None,'deadline':parse_date(raw.get('deadline')),
        'speakers':raw.get('speakers',[]),'companies':raw.get('companies',[]),'labs':raw.get('labs',[]),'level':clean(raw.get('level')) or None,
        'url':url,'status':raw.get('status','Annoncé'),'reliability':source.get('reliability','Élevée'),
        'sources':[{'id':source['id'],'name':source['name'],'url':url,'listingUrl':source['url'],'checkedAt':checked}],
        'firstSeen':checked,'lastVerified':checked,'history':[], 'externalId':clean(raw.get('externalId')) or None,
    }
    if event['end'] and event['end']<start: event['end']=None
    event['score']=score(event)
    return event

def same_event(a,b):
    # Sessions distinctes : même date ET même précision horaire obligatoires.
    if a['start']!=b['start']: return False
    if a.get('externalId') and a.get('externalId')==b.get('externalId') and {s['id'] for s in a['sources']} & {s['id'] for s in b['sources']}: return True
    if canonical(a['url'])==canonical(b['url']) and norm(a['title'])==norm(b['title']): return True
    return norm(a['title'])==norm(b['title']) and norm(a['organizer'])==norm(b['organizer']) and norm(a.get('location'))==norm(b.get('location'))

def reconcile(previous, incoming):
    result=[dict(e) for e in previous]
    for new in incoming:
        match=next((e for e in result if same_event(e,new)),None)
        if not match:
            # Stable URL + title identifies a schedule change only when this source does not publish several sessions.
            candidates=[e for e in result if e['url']==new['url'] and norm(e['title'])==norm(new['title'])]
            sessions=[e for e in incoming if e['url']==new['url'] and norm(e['title'])==norm(new['title'])]
            if len(candidates)==1 and len(sessions)==1 and len({e['start'][:10] for e in candidates+sessions})>1 and new.get('externalId') and candidates[0].get('externalId')==new['externalId']: match=candidates[0]
        if match:
            changes={k:{'before':match.get(k),'after':new.get(k)} for k in ('start','end','location','address','price','status','registration') if match.get(k)!=new.get(k)}
            history=match.get('history',[])+([{'at':new['lastVerified'],'changes':changes}] if changes else [])
            sources={s['id']:s for s in match['sources']+new['sources']}
            # A sparse feed must not erase richer known information.
            merged={k:(v if v is not None and v!='' and v!=[] else match.get(k,v)) for k,v in new.items()}
            if new.get('price') is None and match.get('price') is not None:
                merged['priceLabel']=match['priceLabel'];merged['currency']=match.get('currency')
            match.update(merged,id=match['id'],firstSeen=match['firstSeen'],history=history,sources=list(sources.values()))
            match['score']=score(match)
        else: result.append(new)
    return sorted(result,key=lambda e:e['start'])
