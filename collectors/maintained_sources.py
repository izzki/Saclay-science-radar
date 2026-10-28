"""Sources officielles suivies pour leurs éditions et programmes à long terme."""
SOURCES=[
    {'id':'s050','name':'Société Française d’Optique','url':'https://www.sfoptique.org/','connector':'edition-landing','group':'Écosystème quantique et photonique','priority':True},
    {'id':'s103','name':'Forum de la Photonique','url':'https://www.forumdelaphotonique.fr/','connector':'edition-landing','group':'Salons et grands événements','priority':True,'enrichmentUrls':['https://www.forumdelaphotonique.fr/espace-visiteur']},
    {'id':'ihp-qcrypto-2027','name':'IHP — cryptographie quantique 2027','url':'https://indico.math.cnrs.fr/category/837/','connector':'auto','group':'Institutions scientifiques parisiennes','priority':True},
    {'id':'quest-is','name':'QUEST-IS — ingénierie quantique','url':'https://conference-questis.org/','connector':'edition-landing','group':'Salons et grands événements','priority':True},
    {'id':'cigre-paris','name':'CIGRE — Paris Session et exposition technique','url':'https://www.cigre-exhibition.com/','connector':'edition-landing','group':'Salons et grands événements','priority':False},
    {'id':'quantum-networks-2027','name':'Quantum Networks Summit 2027','url':'https://www.uppersideconferences.com/quantum-networks/2027/index.html','connector':'edition-landing','group':'Écosystème quantique et photonique','priority':True},
]

def maintained_sources(registry):
    for config in SOURCES:
        source=next((s for s in registry if s['id']==config['id']),None)
        if source:source.update(config)
        else:
            source={**config,'enabled':True,'reliability':'Élevée','status':'Validation programmée','note':'Source officielle d’édition ou de programme ; dates collectées dans la page, sans extrapolation annuelle.'}
            registry.append(source)
        source['enabled']=True
        if source.get('lastResult')=='ok':
            source.pop('lastIntegrationError',None);source.pop('lastCheckError',None)
    return registry
