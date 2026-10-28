"""Audit fondé sur un relevé indépendant, jamais sur la sortie du collecteur lui-même."""
import json
from pathlib import Path
from .model import now,canonical,norm

def coverage(registry,events,run):
    automated=[s for s in registry if s.get('enabled') and s.get('lastSuccess') and s.get('lastEventCount',0)>0 and s.get('lastResult')=='ok']
    attempted=[s for s in registry if s.get('enabled') and s.get('lastAttempt')]
    success=[s for s in attempted if s.get('lastResult')=='ok']
    audits=[]
    for file in sorted(Path('data/audits').glob('*.json')):
        sample=json.loads(file.read_text())
        expected=sample.get('expected',[])
        if not expected:continue
        matched=[];missed=[]
        for item in expected:
            match=next((e for e in events if e['start'][:10]==item['date'] and (canonical(e['url'])==canonical(item['url']) or norm(e['title'])==norm(item['title']))),None)
            (matched if match else missed).append(item)
        audits.append({'id':file.stem,'sourceId':sample['sourceId'],'window':sample['window'],'reviewedAt':sample['reviewedAt'],'method':sample['method'],'expected':len(expected),'detected':len(matched),'missed':missed,'observedRecall':round(100*len(matched)/len(expected),1)})
    return {'generatedAt':now(),'inventory':len(registry),'automated':len(automated),'enabled':len([s for s in registry if s.get('enabled')]),
        'verifiedUrls':len([s for s in registry if s.get('lastCheck')]),'discovered':len([s for s in registry if s.get('discoveredAt')]),
        'successfulCollectors':len(success),'attemptedCollectors':len(attempted),'collectorSuccessRate':round(len(success)/len(attempted)*100,1) if attempted else None,
        'inventoryAutomationRate':round(100*len(automated)/len(registry),1) if registry else 0,'globalRecall':None,
        'audits':audits,'auditedRecall':round(100*sum(a['detected'] for a in audits)/sum(a['expected'] for a in audits),1) if audits else None,
        'lastSuccessfulCollection':run.get('lastSuccessfulCollection'),'events':len(events),
        'limits':['L’inventaire comprend des URL candidates non vérifiées.','Le succès technique d’un collecteur ne prouve pas l’exhaustivité de l’agenda.','Les annonces privées et les réseaux sans API autorisée ne sont pas collectés.','La découverte suit des liens publics ; elle ne parcourt pas tout le Web.','Les récurrences sont développées sur une fenêtre glissante : douze mois passés et deux ans à venir ; les règles à la seconde/minute sont signalées pour contrôle.'],
        'nextPriorities':[s['name'] for s in registry if s.get('enabled') and s.get('lastResult')!='ok']}
