import unittest
from collectors.model import make_event,compact
from collectors.quality import clean_catalog,prepare_sources
SOURCE={'id':'test','name':'Organisme scientifique','url':'https://example.org/agenda'}
def event(title,**kw):return make_event(dict(title=title,start='2026-11-01',url='https://example.org/event',**kw),SOURCE)
class QualityTests(unittest.TestCase):
 def test_no_score_or_price_exclusion(self):
  e=event('Séminaire interdisciplinaire',price=200)
  accepted,rejected=clean_catalog([e]);self.assertEqual(len(accepted),1);self.assertEqual(rejected,[])
 def test_explicit_entertainment_scope(self):
  accepted,rejected=clean_catalog([event('Concert de musique')]);self.assertEqual(accepted,[]);self.assertEqual(len(rejected),1)
  self.assertEqual(len(clean_catalog([event('Spectacle Arts & Sciences')])[0]),1)
 def test_ambiguous_source_not_confirmed(self):
  e=event('Annonce interdisciplinaire');e['sources'][0]['name']='Université PSL'
  accepted,_=clean_catalog([e]);self.assertEqual(accepted[0]['reliability'],'Faible');self.assertTrue(accepted[0]['warnings'])
 def test_language_and_export_identity(self):
  a=event('Atelier de mathématiques',location='Endroit IHP')
  a['url']='https://www.ihp.fr/fr/agenda/atelier'
  b=dict(a,id='autre',url='https://www.ihp.fr/en/events/atelier',location='Place IHP')
  self.assertEqual(len(compact([a,b])),1)
 def test_suspend_ambiguous_source(self):
  s=prepare_sources([{'name':'Université PSL','enabled':True}])[0];self.assertFalse(s['enabled'])
if __name__=='__main__':unittest.main()
