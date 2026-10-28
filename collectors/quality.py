"""Contrôles de périmètre et de traçabilité, indépendants du score personnalisé."""
import re
from urllib.parse import urlsplit
from .model import norm,compact,event_url_identity

STRUCTURAL={'agenda','evenements','nos evenements','grands evenements','tous les evenements','evenements a venir','resume','intervenant s','intervenants','abstract','programme','informations pratiques','inscription','lieu','date'}

def prepare_sources(registry):
    for source in registry:
        if source['name']=='Université PSL':
            source.update(enabled=False,status='Intégration nécessaire — métadonnées ambiguës',note='Des métadonnées globales ont été retrouvées sur des pages sans rapport avec certaines annonces. Collecte suspendue jusqu’à validation du rattachement aux pages individuelles. Les annonces déjà repérées restent accessibles avec une fiabilité faible.')
    return registry

def clean_catalog(events):
    accepted=[];quarantine=[]
    for original in events:
        e=dict(original);title=norm(e['title']);text=norm(e['title']+' '+e.get('description',''))
        reason=None
        if title in STRUCTURAL:reason='Rubrique de navigation interprétée comme événement'
        # Exclusion de périmètre explicite, sans aucun critère de score ou de prix.
        artistic=re.search(r'\b(concert|festival musique|spectacle|atelier photo|art fair|soiree etudiante|soiree dansante|gala etudiant)\b',title)
        science=re.search(r'\b(sciences?|scientifique|recherche|chercheur|physique|quantique|photonique|ingenierie|technologie|mathematiques|science art)\b',text)
        if artistic and not science:reason='Événement artistique ou festif sans lien scientifique identifiable dans l’annonce extraite'
        if reason:
            quarantine.append({'event':e,'reason':reason});continue
        if not urlsplit(e['url']).path.startswith('/agenda/'):
            precise={x['url'] for x in events if x['start']==e['start'] and norm(x['title'])==title and x['organizer']==e['organizer'] and urlsplit(x['url']).netloc==urlsplit(e['url']).netloc and urlsplit(x['url']).path.startswith('/agenda/')}
            if len(precise)==1:e['url']=next(iter(precise))
        if any(s.get('name')=='Université PSL' for s in e.get('sources',[])):
            e.update(reliability='Faible',status='Annonce à confirmer',url='https://psl.eu/agenda')
            e['registrationUrl']=None
            e['warnings']=['Métadonnées institutionnelles non rattachées à une page individuelle : date, heure et accès à confirmer. La source n’est plus collectée automatiquement en attendant réparation.']
        if 'institutoptique.fr' in e['url'] and 'T00:00:00' in e['start']:
            precise={x['start'] for x in events if x['start'][:10]==e['start'][:10] and 'T' in x['start'] and 'T00:00:00' not in x['start'] and norm(x['title'])==title and event_url_identity(x['url'])==event_url_identity(e['url'])}
            if len(precise)==1:e['start']=next(iter(precise));e['timezone']='Europe/Paris'
        accepted.append(e)
    return compact(accepted),quarantine
