import unittest
from unittest.mock import patch
import requests
from collectors.connectors import schema_events,ics_events,feed_links,html_events
from collectors.source_discovery import candidates
from collectors.network import Fetcher
class ConnectorTests(unittest.TestCase):
 def test_jsonld(self):
  text='<script type="application/ld+json">{"@type":"Event","name":"Test","startDate":"2026-11-01","isAccessibleForFree":true,"location":{"name":"Salle","address":{"addressLocality":"Palaiseau"}},"offers":{"url":"/register"}}</script>'
  e=schema_events(text,'https://example.org/')[0]
  self.assertEqual(e['price'],0);self.assertEqual(e['registrationUrl'],'https://example.org/register');self.assertEqual(e['city'],'Palaiseau')
 def test_ics(self):
  text='BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:test\r\nDTSTART;TZID=Europe/Paris:20261103T110000\r\nSUMMARY:Test\r\nSTATUS:CANCELLED\r\nEND:VEVENT\r\nEND:VCALENDAR'
  e=ics_events(text,'https://example.org/')[0];self.assertEqual(e['start'],'2026-11-03T11:00:00+01:00');self.assertEqual(e['status'],'Annulé')
 def test_publication_is_not_event(self):
  text='<rss><channel><item><title>Test</title><pubDate>Sun, 1 Nov 2026</pubDate><link>https://example.org/event</link></item></channel></rss>'
  self.assertEqual(feed_links(text,'https://example.org/'),['https://example.org/event'])
 def test_discovery(self):
  result=candidates('<a href="/agenda">Agenda scientifique</a><link type="text/calendar" href="/events.ics">','https://example.org/')
  self.assertEqual({c['url'] for c in result},{'https://example.org/agenda','https://example.org/events.ics'})
 def test_biomedical_link_is_not_calendar(self):
  from collectors.connectors import calendar_links
  self.assertEqual(calendar_links('<a href="/imagerie-biomedicale">Imagerie</a>','https://example.org/'),[])
 def test_c2n_card(self):
  text='<div class="events-list"><div class="event-card"><p class="event-date">3 novembre 2026 – 14h00</p><h3>Séminaire de test</h3><p class="event-lieu">Palaiseau</p><a href="/seminaire/test">Lire</a></div></div>'
  e=html_events(text,'https://example.org/',{})[0];self.assertEqual(e['start'],'2026-11-03T14:00:00+01:00');self.assertEqual(e['location'],'Palaiseau')
 def test_lcf_widget(self):
  text='<div class="addtocalendar"><span class="atc_date_start">2026-11-03 00:00:00</span><span class="atc_title">Test séminaire</span><span class="atc_description">Séminaire le 3 novembre 2026 à 13h15</span></div>'
  self.assertEqual(html_events(text,'https://example.org/',{})[0]['start'],'2026-11-03T13:15:00+01:00')
 def test_robots_error_never_leaves_permissive_cache(self):
  fetcher=Fetcher();response=requests.Response();response.status_code=403
  error=requests.HTTPError(response=response)
  with patch.object(fetcher,'validate',side_effect=lambda url:url),patch.object(fetcher,'_request',side_effect=error) as request:
   for _ in range(2):
    with self.assertRaises(RuntimeError):fetcher.allowed('https://example.org/events')
   self.assertEqual(request.call_count,2)
 def test_ssrf_literal(self):
  for url in ['http://127.0.0.1/','http://169.254.169.254/','http://[::1]/','file:///etc/passwd']:
   with self.assertRaises(ValueError):Fetcher().validate(url)
if __name__=='__main__':unittest.main()
