import unittest
from collectors.model import canonical,norm,parse_date,make_event,reconcile,compact
SOURCE={'id':'test','name':'Laboratoire de test','url':'https://example.org/agenda'}
# Fixtures synthétiques, strictement confinées aux tests.
def event(**kw):
    return make_event(dict(title='Séminaire photonique',start='2026-11-03T11:00:00+01:00',url='https://example.org/event/1',**kw),SOURCE,'2026-10-28T00:00:00+00:00')
class ModelTests(unittest.TestCase):
    def test_normalization(self):self.assertEqual(norm('  Optique QUANTIQUE : séminaire !'),'optique quantique seminaire')
    def test_url(self):
        self.assertEqual(canonical('https://example.org/a?utm_source=x&id=2#top'),'https://example.org/a?id=2')
        self.assertEqual(canonical('javascript:alert(1)'),'')
        self.assertEqual(canonical('https://user:secret@example.org'),'')
    def test_dates(self):
        self.assertEqual(parse_date('3 novembre 2026 à 11h15',True),'2026-11-03T11:15:00+01:00')
        self.assertEqual(parse_date('2026-07-03T11:00:00'),'2026-07-03T11:00:00+02:00')
        self.assertEqual(parse_date('2026-11-03'),'2026-11-03')
        self.assertIsNone(parse_date('31 février 2026',True))
        self.assertIsNone(parse_date('sans date'))
    def test_timezone_normalized(self):
        self.assertEqual(parse_date('2026-11-03T10:00:00Z'),parse_date('2026-11-03T11:00:00+01:00'))
    def test_explicit_city_and_status(self):
        e=event(description='REPORTÉ : séminaire à Palaiseau')
        self.assertEqual(e['city'],'Palaiseau');self.assertEqual(e['status'],'Reporté')
    def test_affiliation_does_not_determine_venue(self):
        self.assertIsNone(event(description='Intervenant de Paris')['city'])
    def test_nonfinite_price_unknown(self):
        self.assertIsNone(event(price='NaN')['price'])
    def test_no_invention(self):
        e=event();self.assertIsNone(e['price']);self.assertIsNone(e['city']);self.assertIsNone(e['registrationUrl']);self.assertEqual(e['priceLabel'],'Non précisé')
    def test_quantum_word_not_max(self):
        e=make_event({'title':'Culture quantique','start':'2026-11-01'},SOURCE)
        self.assertLess(e['score']['parts']['Adéquation scientifique'],35)
    def test_hardware_and_weights(self):
        e=event(description='Sources de photons uniques et optique quantique')
        self.assertEqual(e['score']['parts']['Adéquation scientifique'],35)
        self.assertLessEqual(e['score']['total'],100)
        self.assertEqual(sum(e['score']['parts'].values()),e['score']['total'])
    def test_date_precision_dedup(self):
        a=event();b=dict(a,start='2026-11-03',id='date-only')
        self.assertEqual(len(compact([a,b])),1)
        c=dict(a,start='2026-11-03T14:00:00+01:00',id='second-session')
        self.assertEqual(len(compact([a,b,c])),3)
    def test_sessions_preserved(self):
        a=event();b=dict(a,start='2026-11-03T14:00:00+01:00',id='session2')
        self.assertEqual(len(reconcile([],[a,b])),2)
    def test_identity_stable_across_translations(self):
        a=event(location='Endroit IHP');b=event(location='Place IHP');b['url']='https://example.org/en/event/1';b['sources'][0]['url']=b['url']
        result=compact([a,b]);self.assertEqual(len(result),1);self.assertEqual(len(result[0]['sources']),2)
    def test_merge_provenance(self):
        a=event();b=event();b['sources']=[dict(b['sources'][0],id='other')]
        result=reconcile([a],[b]);self.assertEqual(len(result),1);self.assertEqual(len(result[0]['sources']),2)
    def test_history_and_first_seen(self):
        a=event(price=10);b=event(price=0);b['firstSeen']='2026-10-29T00:00:00+00:00'
        result=reconcile([a],[b])[0]
        self.assertEqual(result['firstSeen'],a['firstSeen']);self.assertEqual(result['history'][0]['changes']['price']['after'],0)
    def test_conserve_during_failure(self):
        self.assertEqual(reconcile([event()],[]),[event()])
    def test_missing_date_rejected(self):self.assertIsNone(make_event({'title':'Annonce sans date'},SOURCE))
if __name__=='__main__':unittest.main()
