"""Connecteurs fixes : JSON-LD Event, ICS, RSS/Atom avec dates explicites, HTML institutionnel."""
import json
import re
from datetime import datetime
from urllib.parse import urljoin,urlsplit
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from icalendar import Calendar
from .model import clean,parse_date,canonical,norm
from .recurrence import expand_calendar
from .practical import enrich_event
from .landing_pages import landing_events


def flatten_json(value):
    if isinstance(value,list):
        for v in value: yield from flatten_json(v)
    elif isinstance(value,dict):
        yield value
        for k,v in value.items():
            if k!='@context' and isinstance(v,(list,dict)): yield from flatten_json(v)

def schema_events(text,base):
    soup=BeautifulSoup(text,'html.parser');out=[]
    for script in soup.find_all('script',type='application/ld+json'):
        try: data=json.loads(script.string or script.get_text())
        except (ValueError,TypeError): continue
        for item in flatten_json(data):
            types=item.get('@type',[])
            if isinstance(types,str): types=[types]
            if not any(t.endswith('Event') for t in types if isinstance(t,str)): continue
            if not parse_date(item.get('startDate')):continue
            location=item.get('location') or {}
            if isinstance(location,list):location=location[0] if location else {}
            if isinstance(location,str):location={'name':location}
            address=location.get('address') or {}
            if isinstance(address,str):address={'streetAddress':address}
            organizer=item.get('organizer') or {}
            if isinstance(organizer,list):organizer=organizer[0] if organizer else {}
            offer=item.get('offers') or {}
            if isinstance(offer,list):offer=offer[0] if offer else {}
            if not isinstance(offer,dict):offer={}
            price=offer.get('price')
            if price is None and item.get('isAccessibleForFree') is True:price=0
            mode=item.get('eventAttendanceMode','')
            performers=item.get('performer',[])
            if isinstance(performers,dict):performers=[performers]
            status=item.get('eventStatus','')
            event_url=urljoin(base,item.get('url') or base)
            event_name=norm(item.get('name'))
            linked_title=False
            if event_name:
                for link in soup.find_all('a',href=True):
                    if norm(link.get_text(' '))==event_name and not link['href'].startswith('#'):
                        linked=canonical(urljoin(base,link['href']))
                        if linked and urlsplit(linked).netloc==urlsplit(base).netloc:event_url=linked;linked_title=True;break
            h1=soup.find('h1')
            if not linked_title and not item.get('url') and h1 and norm(h1.get_text(' '))!=event_name:continue
            out.append({'title':item.get('name'),'description':item.get('description'),'start':item.get('startDate'),'end':item.get('endDate'),
                'url':event_url,'externalId':item.get('@id'),
                'organizer':organizer.get('name') if isinstance(organizer,dict) else organizer,
                'location':location.get('name'),'address':', '.join(str(address[k]) for k in ['streetAddress','postalCode','addressLocality'] if address.get(k)),
                'city':address.get('addressLocality'),'format':'Hybride' if 'Mixed' in mode else 'En ligne' if 'Online' in mode else 'Présentiel' if 'Offline' in mode else 'Non précisé',
                'price':price,'currency':offer.get('priceCurrency'),'registrationUrl':urljoin(base,offer['url']) if offer.get('url') else None,
                'status':'Annulé' if 'Cancelled' in status else 'Reporté' if 'Postponed' in status else 'Reprogrammé' if 'Rescheduled' in status else 'Annoncé',
                'speakers':[{'name':clean(p.get('name')),'institution':clean((p.get('affiliation') or {}).get('name')) if isinstance(p.get('affiliation'),dict) else None} for p in performers if isinstance(p,dict) and p.get('name')]})
    return out

def ics_events(text,base,reference=None):
    out=[]
    components,series=expand_calendar(text,reference)
    for item in components:
        start=item.get('dtstart')
        if not start:continue
        dt=start.dt;end=item.get('dtend');end_value=end.dt if end else None
        if end_value is None and item.get('duration'):end_value=dt+item.decoded('duration')
        uid=str(item.get('uid',''));recurrence=item.get('recurrence-id')
        instance=recurrence.dt.isoformat() if recurrence else dt.isoformat()
        url=urljoin(base,str(item.get('url') or base))
        out.append({'title':str(item.get('summary','')),'description':str(item.get('description','')),'start':dt.isoformat(),'end':end_value.isoformat() if end_value else None,
            'endExclusive':bool(end_value and not isinstance(end_value,datetime)),
            'location':str(item.get('location','')),'url':url,'externalId':uid+('#'+instance if uid in series else ''),
            'status':'Annulé' if str(item.get('status'))=='CANCELLED' else 'Annoncé'})
    return out

def feed_links(text,base):
    # pubDate is a publication date, never an event date.
    root=ET.fromstring(text);out=[]
    for item in list(root.findall('.//item'))+list(root.findall('.//{http://www.w3.org/2005/Atom}entry')):
        link=item.find('link')
        if link is None:link=item.find('{http://www.w3.org/2005/Atom}link')
        if link is not None:
            target=link.get('href') or link.text
            if target:out.append(urljoin(base,target))
    return out

def calendar_links(text,base):
    soup=BeautifulSoup(text,'html.parser');out=[]
    for node in soup.find_all(['a','link']):
        href=node.get('href','');kind=node.get('type','');label=clean(node.get_text(' '))
        if href and (re.search(r'\.ics(?:\?|$)|/feed/?(?:\?|$)|/rss(?:[./?]|$)|[?&](?:format|type)=ical|/ical(?:[/?]|$)',href,re.I) or kind in ('text/calendar','application/rss+xml','application/atom+xml')):
            out.append({'url':canonical(urljoin(base,href)),'label':label,'format':'ics' if re.search(r'\.ics(?:\?|$)|[?&](?:format|type)=ical|/ical(?:[/?]|$)',href,re.I) or kind=='text/calendar' else 'feed'})
    return [v for v in out if v['url']]

def detail_links(text,base):
    soup=BeautifulSoup(text,'html.parser');out=[]
    for a in soup.find_all('a',href=True):
        if a['href'].startswith('#'):continue
        url=canonical(urljoin(base,a['href']));label=clean(a.get_text(' '))
        if not url or urlsplit(url).netloc!=urlsplit(base).netloc or url==canonical(base):continue
        path=urlsplit(url).path
        if re.search(r'/(?:login|logout|manage|attachments)(?:/|$)',path) or re.search(r'\.(?:pdf|png|jpe?g|svg|webp)$',path,re.I):continue
        if 'indico.' in (urlsplit(base).hostname or ''):
            # Timetables, contributions, forms and display styles are not separate events.
            if re.fullmatch(r'/event/\d+/?',path):out.append((0,url.split('?')[0].rstrip('/')+'/'))
            continue
        pagination='page=' in a['href'] and urlsplit(url).path==urlsplit(base).path
        if re.search(r'(evenement|event|seminar|seminaire|agenda|conference|colloque|soutenance|workshop)',a['href']+' '+label,re.I) or pagination:
            priority=0 if a.find_parent('article') or a.find_parent(['h2','h3']) else 1 if pagination else 2
            out.append((priority,url))
    return list(dict.fromkeys(url for _,url in sorted(out,key=lambda item:item[0])))

def html_events(text,base,source):
    soup=BeautifulSoup(text,'html.parser');out=[]
    # Institut d'Optique / LCF : données intégrées au bouton « Ajouter au calendrier ».
    for span in (soup.select('.atc_event') or soup.select('.addtocalendar, .vevent')):
        def pick(cls):
            el=span.select_one('.'+cls)
            return clean(el.get_text(' ')) if el else None
        start=pick('atc_date_start') or pick('start') or pick('dtstart')
        title=pick('atc_title') or pick('title') or pick('summary')
        if not start or not title:continue
        desc=pick('atc_description') or pick('description')
        # Calendar widgets sometimes encode midnight despite a precise time in the description.
        parsed=parse_date(start)
        described=parse_date(desc,text=True)
        if parsed and described and parsed[:10]==described[:10] and 'T' in described:parsed=described
        if parsed and 'T00:00:00' in parsed and not (described and 'T' in described):parsed=parsed[:10]
        parent=span.find_parent('article')
        direct=span.find_parent('a',href=True)
        if parent is None:
            parent=next((node for node in span.parents if 'event' in node.get('class',[])),None)
        link=direct or (parent.select_one('a.card-title-link[href], h2 a[href], h3 a[href], a[href]') if parent else None)
        end=parse_date(pick('atc_date_end') or pick('end'))
        if end and 'T00:00:00' in end:end=end[:10]
        if end and parsed and end[:10]==parsed[:10] and len(end)==10:end=None
        description=desc or (clean(parent.get_text(' '))[:3000] if parent else '')
        raw={'title':title,'description':description,'start':parsed,'end':end,'location':pick('atc_location') or pick('location'),'extractionVersion':2,
            'url':urljoin(base,link['href']) if link else base}
        if parent:
            from .practical import practical_from_node
            raw={**practical_from_node(parent,base),**raw}
        out.append(raw)
    # Conservative fallback: explicit event date in a semantic card or event page.
    candidates=soup.select('article, .views-row, .event, .event-item, .seminaire, .seminar, .tribe-events-calendar-list__event, .events-list .event-card')
    if not candidates and re.search(r'/(event|evenement|seminaire|seminar|agenda)/[^/]+',urlsplit(base).path):
        main=soup.find('main') or soup.find('article')
        if main:candidates=[main]
    # CEA/WordPress agendas use small heading-led blocks rather than article elements.
    if source.get('name','').startswith('CEA IRAMIS'):
        for heading in soup.find_all(['h2','h3']):
            parent=heading
            for _ in range(5):
                parent=parent.parent
                if not parent or parent.name in ('body','html'):break
                body=parent.get_text(' ',strip=True)
                if len(body)>3500:break
                if re.search(r'\b\d{2}/\d{2}/\d{4}\b',body) and len(parent.find_all(['h2','h3']))==1:
                    candidates.append(parent);break
    for card in candidates:
        if card.select_one('.addtocalendar, .atc_event'):continue
        heading=card.find(['h1','h2','h3','h4'])
        if not heading:continue
        classes=' '.join(card.get('class',[]))+' '+' '.join(card.parent.get('class',[]))
        event_semantics=bool(re.search(r'event|evenement|seminar|agenda',classes,re.I) or re.search(r'/(?:events?|evenements?|seminaires?|agenda)/',urlsplit(base).path) or card.select_one('[itemprop=startDate]'))
        if not event_semantics:continue
        title=clean(heading.get_text(' '));body=clean(card.get_text(' '))
        times=card.find_all('time',datetime=True)
        start=parse_date(times[0].get('datetime')) if times else None
        end=parse_date(times[1].get('datetime')) if len(times)>1 else None
        location=card.select_one('.event-lieu, .is-place, [itemprop=location]')
        speaker=card.select_one('.event-info')
        # Avoid converting the publication date of news into the event's date.
        if not start and (card.select_one('.event-date') or 'type-evenement' in card.parent.get('class',[]) or re.search(r'séminaire|seminar|soutenance|thèses|conference|conférence|workshop|colloque|agenda|événement',title+' '+body[:160],re.I)):
            start=parse_date(body,text=True)
        if not start:continue
        if not end and start and 'T' in start:
            interval=re.search(r'\b\d{1,2}[h:]\d{2}\s*[-–]\s*(\d{1,2})[h:](\d{2})\b',body)
            if interval:end=parse_date(start[:10]+f'T{int(interval[1]):02d}:{interval[2]}:00')
        a=heading.find('a',href=True) or heading.find_parent('a',href=True) or card.select_one('.suite a[href], a.card-title-link[href], .item-title a[href], a.event-link[href]')
        out.append({'title':title,'description':body[:3000],'start':start,'end':end,'location':clean(location.get_text(' ')) if location else None,'speakers':[{'name':clean(speaker.get_text(' ')).lstrip('👤 ')}] if speaker else [],'url':urljoin(base,a['href']) if a else base})
    return out

def extract(text,url,source,kind=None):
    lower=text.lstrip().lower()
    if kind=='ics' or lower.startswith('begin:vcalendar'):return ics_events(text,url)
    landing=landing_events(text,url,source)
    # Landing templates contain former exhibitors and prices for stands: don't enrich from those.
    if landing:return landing
    return [enrich_event(raw,text,url) for raw in schema_events(text,url)+html_events(text,url,source)]
