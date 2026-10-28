"""Extraction factuelle des tarifs, accès et inscriptions dans le contenu d'un événement."""
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .model import clean,norm,canonical,parse_date


def practical_from_node(node,base):
    node=BeautifulSoup(str(node),'html.parser')
    for unrelated in node.select('nav,header,footer,script,style,aside,.related-events,.related-content,.newsletter'):unrelated.decompose()
    body=clean(node.get_text(' ',strip=True));data={};evidence={}
    # A price is accepted only with a currency and a nearby practical label.
    match=re.search(r'\b(?:tarif|prix|participation|entrée|entree|inscription|billet)\s*(?:normal|plein|standard|général|general)?\s*[:–-]?\s*(\d+(?:[,.]\d+)?)\s*(?:€|EUR\b|euros?\b)',body,re.I)
    free=re.search(r'\b(?:entrée|entree|accès|acces|participation|événement|evenement|inscription)\s+(?:est\s+)?(?:libre\s+et\s+)?gratuite?\b|\bentrée libre\b|\b(?:prix|tarifs?|conditions)\s*:?\s*gratuit(?:e)?\b(?!\s+pour\s+(?:les\s+)?[ée]tudiants)',body,re.I)
    if match:data.update(price=float(match[1].replace(',','.')),currency='EUR');evidence['price']=match[0]
    elif free:
        qualifier=body[free.end():free.end()+60]
        if re.match(r'\s+pour\s+(?:les\s+)?[ée]tudiants',qualifier,re.I):data.update(studentPrice=0,currency='EUR');evidence['studentPrice']=free[0]+qualifier[:35]
        else:data.update(price=0,currency='EUR');evidence['price']=free[0]
    student=re.search(r'\b(?:tarif\s+)?[ée]tudiants?\s*[:–-]?\s*(\d+(?:[,.]\d+)?)\s*(?:€|EUR\b|euros?\b)',body,re.I)
    if student:data['studentPrice']=float(student[1].replace(',','.'));data['currency']='EUR';evidence['studentPrice']=student[0]
    access=re.search(r'[^.!?]{0,70}\b(?:inscription obligatoire|entrée libre|entree libre|sur inscription|ouvert(?:e)? au public|accessible à tous|accès restreint|acces restreint|réservation obligatoire|sur invitation|réservé(?:e)? aux)[^.!?]{0,180}',body,re.I)
    if access:data['access']=clean(access[0]);evidence['access']=clean(access[0])
    mandatory=re.search(r'\b(inscription|réservation)\s+(obligatoire|facultative)\b',body,re.I)
    if mandatory:data['registration']=mandatory[0]
    for a in node.find_all('a',href=True):
        label=clean(a.get_text(' '))
        if re.search(r"s[’']inscrire|inscription|register|registration|billetterie|réserver|reserver",label,re.I) and not re.search(r'newsletter|lettre|formation|connexion|login|compte',label,re.I):
            url=canonical(urljoin(base,a['href']))
            if url and not a['href'].startswith('#'):data['registrationUrl']=url;evidence['registrationUrl']=label;break
    if re.search(r'\b(?:en ligne|webinaire|visioconférence|distanciel)\b',body,re.I):data['format']='En ligne'
    if re.search(r'\bhybride\b',body,re.I):data['format']='Hybride'
    if evidence:data['evidence']=evidence
    return data


def enrich_event(raw,text,base):
    soup=BeautifulSoup(text,'html.parser');title=norm(raw.get('title'));node=None
    for heading in soup.find_all(['h1','h2','h3','h4']):
        if norm(heading.get_text(' '))!=title:continue
        node=heading.find_parent(['article','main'])
        if heading.name!='h1':
            for parent in heading.parents:
                if parent.name in ('body','html'):break
                classes=' '.join(parent.get('class',[]))
                if re.search(r'event|evenement|thumbnail|views-row|card',classes,re.I):node=parent;break
        if node:break
    if node is None:return raw
    practical=practical_from_node(node,base)
    return {**practical,**{k:v for k,v in raw.items() if v is not None and v!=''},'evidence':{**practical.get('evidence',{}),**raw.get('evidence',{})}}
