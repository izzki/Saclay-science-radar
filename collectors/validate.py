import json
from pathlib import Path
from .model import canonical,parse_date

def validate():
    events=json.loads(Path('public/data/events.json').read_text());seen=set()
    for e in events:
        assert e['id'] not in seen, 'Identifiant dupliqué'
        seen.add(e['id'])
        assert canonical(e['url']) and parse_date(e['start']) and e['title'] and e['sources']
        assert 0<=e['score']['total']<=100
        assert sum(e['score']['parts'].values())==e['score']['total']
        assert all(canonical(s['url']) and s['checkedAt'] for s in e['sources'])
    print(len(events),'événements validés ; aucun jeu de démonstration chargé')
if __name__=='__main__':validate()
