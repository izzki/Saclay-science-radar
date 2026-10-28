"""Diagnostic borné de la structure des agendas officiels, sans copie intégrale des pages."""
import json,sys
from pathlib import Path
from bs4 import BeautifulSoup
from .network import Fetcher
from .connectors import extract,calendar_links
from .model import clean,make_event,reconcile
SOURCES=[('LCF','https://www.lcf.institutoptique.fr/agenda'),('C2N','https://www.c2n.universite-paris-saclay.fr/fr/agenda/'),('CEA IRAMIS','https://iramis.cea.fr/'),('Institut Henri Poincaré','https://www.ihp.fr/fr/agenda')]
if __name__=='__main__':
 f=Fetcher(30);catalog=[]
 for name,url in SOURCES:
  try:
   body,final,_=f.get(url);soup=BeautifulSoup(body,'html.parser');events=extract(body,final,{'name':name})
   data={'name':name,'url':final,'events':len(events),'samples':events[:2],'calendars':calendar_links(body,final)[:8],'structure':[]}
   nodes=soup.find_all(['article','time','h2','h3'])[:25]
   nodes+=soup.find_all(class_=lambda c:c and any(k in c.lower() for k in ['atc_','calendar','event']))[:30]
   for n in nodes:
    data['structure'].append({'tag':n.name,'class':n.get('class'),'text':clean(n.get_text(' '))[:230],'parent':{'tag':n.parent.name,'class':n.parent.get('class')},'children':[{'tag':ch.name,'class':ch.get('class')} for ch in n.find_all(recursive=False) if ch.name][:12]})
   catalog.extend(e for e in (make_event(raw,{'id':'diag-'+name,'name':name,'url':url}) for raw in events) if e)
   print(json.dumps(data,ensure_ascii=False),flush=True)
  except Exception as e:print(json.dumps({'name':name,'error':str(e)}),flush=True)

 if '--write-catalog' in sys.argv:
  Path('public/data/events.json').write_text(json.dumps(reconcile([],catalog),ensure_ascii=False,indent=2)+'\n')
  print('CATALOGUE RÉEL DE VÉRIFICATION',len(reconcile([],catalog)))
