"""Connecteurs fixes : JSON-LD Event, ICS, RSS/Atom avec dates explicites, HTML institutionnel."""
import json
import re
from datetime import datetime
from urllib.parse import urljoin,urlsplit
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from icalendar import Calendar
from .model import clean,parse_date,canonical


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
            out.append({'title':item.get('name'),'description':item.get('description'),'start':item.get('startDate'),'end':item.get('endDate'),
                'url':urljoin(base,item.get('url') or base),'externalId':item.get('@id'),
                'organizer':organizer.get('name') if isinstance(organizer,dict) else organizer,
                'location':location.get('name'),'address':', '.join(str(address[k]) for k in ['streetAddress','postalCode','addressLocality'] if address.get(k)),
                'city':address.get('addressLocality'),'format':'Hybride' if 'Mixed' in mode else 'En ligne' if 'Online' in mode else 'Présentiel' if 'Offline' in mode else 'Non précisé',
                'price':price,'currency':offer.get('priceCurrency'),'registrationUrl':urljoin(base,offer['url']) if offer.get('url') else None,
                'status':'Annulé' if 'Cancelled' in status else 'Reporté' if 'Postponed' in status else 'Reprogrammé' if 'Rescheduled' in status else 'Annoncé',
                'speakers':[{'name':clean(p.get('name')),'institution':clean((p.get('affiliation') or {}).get('name')) if isinstance(p.get('affiliation'),dict) else None} for p in performers if isinstance(p,dict) and p.get('name')]})
    return out

def ics_events(text,base):
    out=[]
    for item in Calendar.from_ical(text).walk('VEVENT'):
        start=item.get('dtstart')
        if not start:continue
        dt=start.dt
        # Recurrence is expanded with a dedicated library; unsupported rules are not silently flattened.
        if item.get('rrule'): raise ValueError('Calendrier récurrent : expansion RRULE à intégrer')
        end=item.get('dtend')
        out.append({'title':str(item.get('summary','')),'description':str(item.get('description','')),'start':dt.isoformat(),'end':end.dt.isoformat() if end else None,
            'location':str(item.get('location','')),'url':urljoin(base,str(item.get('url') or base)),'externalId':str(item.get('uid','')),
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
        url=canonical(urljoin(base,a['href']));label=clean(a.get_text(' '))
        if not url or urlsplit(url).netloc!=urlsplit(base).netloc or url==canonical(base):continue
        if re.search(r'(evenement|event|seminar|seminaire|agenda|conference|colloque|soutenance|workshop)',a['href']+' '+label,re.I):out.append(url)
    return list(dict.fromkeys(out))

def html_events(text,base,source):
    soup=BeautifulSoup(text,'html.parser');out=[]
    # Institut d'Optique / LCF : données intégrées au bouton « Ajouter au calendrier ».
    for span in soup.select('.addtocalendar, .atcb, .atc_event, .vevent'):
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
        parent=span
        for _ in range(5):
            if parent.parent and parent.parent.name not in ('body','html'):parent=parent.parent
            if parent.find(['h2','h3']):break
        link=parent.find('a',href=True)
        out.append({'title':title,'description':desc,'start':parsed,'end':None,'location':pick('atc_location') or pick('location'),
            'url':urljoin(base,link['href']) if link else base})
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
        a=heading.find('a',href=True) or card.find('a',href=True)
        out.append({'title':title,'description':body[:3000],'start':start,'end':end,'location':clean(location.get_text(' ')) if location else None,'speakers':[{'name':clean(speaker.get_text(' ')).lstrip('👤 ')}] if speaker else [],'url':urljoin(base,a['href']) if a else base})
    return out

def extract(text,url,source,kind=None):
    lower=text.lstrip().lower()
    if kind=='ics' or lower.startswith('begin:vcalendar'):return ics_events(text,url)
    return schema_events(text,url)+html_events(text,url,source)
