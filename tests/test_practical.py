import unittest
from bs4 import BeautifulSoup
from collectors.practical import practical_from_node
from collectors.connectors import extract
class PracticalTests(unittest.TestCase):
 def test_price_student_access_registration(self):
  html='<article><h1>Conférence</h1><p>Tarif : 12 €. Étudiant : 5 €. Inscription obligatoire.</p><a href="/billets">S’inscrire</a></article>'
  e=practical_from_node(BeautifulSoup(html,'html.parser'),'https://example.org/event')
  self.assertEqual(e['price'],12);self.assertEqual(e['studentPrice'],5);self.assertEqual(e['registrationUrl'],'https://example.org/billets');self.assertIn('obligatoire',e['access'])
 def test_free_is_explicit(self):
  e=practical_from_node(BeautifulSoup('<p>Entrée libre et gratuite.</p>','html.parser'),'https://example.org/')
  self.assertEqual(e['price'],0)
  self.assertNotIn('price',practical_from_node(BeautifulSoup('<p>Free electron laser</p>','html.parser'),'https://example.org/'))
 def test_student_free_does_not_make_general_admission_free(self):
  e=practical_from_node(BeautifulSoup('<p>Entrée gratuite pour les étudiants.</p>','html.parser'),'https://example.org/')
  self.assertNotIn('price',e);self.assertEqual(e['studentPrice'],0)
 def test_unrelated_footer_price_is_not_event_price(self):
  e=practical_from_node(BeautifulSoup('<main><h1>Conférence</h1><footer>Tarif : 99 €</footer></main>','html.parser'),'https://example.org/')
  self.assertNotIn('price',e)
 def test_two_widgets_keep_their_own_links(self):
  text='<div class="event"><a href="/agenda/a"><span class="addtocalendar"><var class="atc_event"><var class="atc_title">Conférence A</var><var class="atc_date_start">2026-11-02 14:00</var><var class="atc_date_end">2026-11-02 15:00</var></var></span></a></div><div class="event"><a href="/agenda/b"><var class="atc_event"><var class="atc_title">Conférence B</var><var class="atc_date_start">2026-11-03 14:00</var></var></a></div>'
  result=extract(text,'https://example.org/agenda',{'name':'PSL'})
  self.assertEqual(len(result),2);self.assertEqual(result[0]['url'],'https://example.org/agenda/a');self.assertEqual(result[1]['url'],'https://example.org/agenda/b');self.assertIn('15:00',result[0]['end'])
if __name__=='__main__':unittest.main()
