"""Pages officielles d'éditions : dates lues dans le HTML, jamais reconduites."""
import re
from datetime import date
from urllib.parse import urlsplit, urljoin
from bs4 import BeautifulSoup
from .model import clean, parse_date, norm, MONTHS

EN_MONTHS={m:i+1 for i,m in enumerate('january february march april may june july august september october november december'.split())}

def english_date(text):
    m=re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+('+'|'.join(EN_MONTHS)+r')\s*,?\s*(20\d{2})\b',text,re.I)
    if not m:return None
    try:return date(int(m[3]),EN_MONTHS[m[2].lower()],int(m[1])).isoformat()
    except ValueError:return None

def landing_events(text,base,source):
    host=(urlsplit(base).hostname or '').removeprefix('www.')
    path=urlsplit(base).path.rstrip('/')
    soup=BeautifulSoup(text,'html.parser');main=soup.find('main') or soup
    body=clean(main.get_text(' '));out=[]
    if host=='forumdelaphotonique.fr' and not path:
        title=main.find('h1');hero=title.find_parent('section') if title else None
        # Odoo currently concatenates "le19". Only the edition banner supplies the date.
        banner=clean(hero.get_text(' ')) if hero else ''
        banner=re.sub(r'(?i)\ble(?=\d)','le ',banner)
        start=parse_date(banner,text=True)
        if title and 'forum de la photonique' in norm(title.get_text()) and start:
            edition=re.search(r'\b(\d+)\s*e?\s*édition',banner,re.I)
            out.append({'title':'Forum de la Photonique'+(' — '+edition[1]+'e édition' if edition else ''),
                'start':start,'url':base,'organizer':'Forum de la Photonique — Institut d’Optique Graduate School',
                'description':body[:body.find('Ils nous ont fait confiance')] if 'Ils nous ont fait confiance' in body else body[:2400],
                'registration':'Inscription obligatoire' if 'sur inscription' in banner else None,
                'registrationUrl':urljoin(base,'/espace-visiteur'),'format':'Présentiel',
                'warnings':['Les exposants de l’édition précédente ne sont pas présentés comme participants de cette édition.'],
                'evidence':{'start':banner}})
    elif host=='conference-questis.org' and not path:
        headings=[clean(h.get_text(' ')) for h in soup.select('h2.elementor-heading-title')]
        dates=[(h,english_date(h)) for h in headings if english_date(h)]
        edition=re.search(r'\bQUEST[- ]IS\s+(20\d{2})\b',body)
        if edition and len(dates)>=2 and all(d[1][:4]==edition[1] for d in dates[:2]):
            intro=re.search(r'In the heart.*?(?=Learn more|EDF LAB|QUEST.IS.25)',body)
            out.append({'title':'QUEST-IS '+edition[1]+' — Quantum Engineering Conference and Exhibition',
                'start':dates[0][1],'end':dates[1][1],'url':base,'organizer':'SEE',
                'description':intro[0] if intro else '', 'location':'EDF Lab Paris-Saclay' if 'EDF Lab' in body else None,
                'format':'Présentiel','evidence':{'start':dates[0][0],'end':dates[1][0]},
                'warnings':['Les intervenants et sponsors affichés pour 2025 ne sont pas attribués à l’édition 2027.']})
    elif host=='cigre-exhibition.com' and not path:
        # Read the dated 2028 banner, not the old testimonials or exhibitor fees.
        m=re.search(r'\b(\d{1,2})\s+([A-Za-z]+)\s*(?:to|[–-])\s*(\d{1,2})\s+([A-Za-z]+)\s*,?\s*(20\d{2})\b',body)
        edition=re.search(r'(?:Paris Session|CIGRE)\s+(20\d{2})',body)
        if m and edition and m[5]==edition[1]:
            start=english_date(f'{m[1]} {m[2]} {m[5]}');end=english_date(f'{m[3]} {m[4]} {m[5]}')
            if start and end:out.append({'title':'CIGRE '+edition[1]+' — Exposition technique et Paris Session',
                'start':start,'end':end,'url':base,'organizer':'CIGRE',
                'description':'Exposition technique de la Paris Session : entreprises, technologies et spécialistes de l’industrie des systèmes électriques.',
                'location':'Palais des Congrès, Paris' if 'Palais des Congrès' in body else None,'format':'Présentiel',
                'evidence':{'start':m[0],'end':m[0]},'warnings':['Tarifs et modalités de visite à confirmer pour cette édition ; les prix exposants ne sont pas des billets visiteurs.']})
    elif host=='sfoptique.org' and not path:
        for heading in main.select('h2.row-title'):
            card=heading.parent;content=clean(card.get_text(' '));n=norm(content)
            interval=re.search(r'\bdu (\d{1,2}) au (\d{1,2}) ('+'|'.join(MONTHS)+r') (20\d{2})\b',n)
            if not interval or 'paris' not in n:continue
            start=parse_date(f'{interval[1]} {interval[3]} {interval[4]}',text=True)
            end=parse_date(f'{interval[2]} {interval[3]} {interval[4]}',text=True)
            if start and end:out.append({'title':clean(heading.get_text(' ')), 'start':start,'end':end,'url':base,
                'description':content,'organizer':'Société Française d’Optique',
                'location':'Institut Langevin, Paris' if 'institut langevin' in n else 'Paris',
                'format':'Présentiel','evidence':{'start':interval[0],'end':interval[0]}})
    elif host=='uppersideconferences.com' and '/quantum-networks/' in path and path.endswith('/index.html'):
        m=re.search(r'\b(\d{1,2})\s*[|&–-]\s*(\d{1,2})\s+('+'|'.join(EN_MONTHS)+r')\s+(20\d{2})\b',body,re.I)
        if m:
            out.append({'title':'Quantum Networks Summit '+m[4], 'start':english_date(f'{m[1]} {m[3]} {m[4]}'),
                'end':english_date(f'{m[2]} {m[3]} {m[4]}'),'url':base,'organizer':'Upperside Conferences',
                'description':body[body.find('Towards Fully Quantum Networks'):body.find('Towards Fully Quantum Networks')+2400],
                'location':'Palais des Congrès de Paris' if 'Palais des Congrès' in body else None,'format':'Présentiel',
                'evidence':{'start':m[0],'end':m[0]}})
    return out

def enrich_forum(raw,text,base):
    """Compléments visiteurs, séparés de la date de l'édition et des anciens exposants."""
    soup=BeautifulSoup(text,'html.parser');body=clean((soup.find('main') or soup).get_text(' '))
    result=dict(raw)
    location=re.search(r'bâtiment\s+503',body,re.I)
    if location:result['location']=location[0];result.setdefault('evidence',{})['location']=location[0]
    result['description']=result.get('description','')+' '+body[:1600]
    result['access']='Consulter les conditions d’inscription visiteur ou étudiant sur la page officielle.'
    result['additionalSources']=[{'url':base,'name':'Forum de la Photonique — espace visiteur'}]
    visitor=next((a for a in soup.find_all('a',href=True) if norm(a.get_text(' '))=='inscription visiteur'),None)
    if visitor:result['registrationUrl']=urljoin(base,visitor['href'])
    return result
