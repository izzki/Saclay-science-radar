import unittest
from collectors.import_url import request_url,public_url,import_events
class FakeFetcher:
 def get(self,url):return '<script type="application/ld+json">{"@type":"Event","name":"Conférence publique test","startDate":"2026-11-10","url":"https://example.org/event"}</script>',url,'text/html'
class ImportTests(unittest.TestCase):
 def test_owner_can_request_only_public_url(self):
  payload={'action':'opened','repository':{'owner':{'login':'owner'}},'sender':{'login':'owner'},'issue':{'user':{'login':'owner'},'number':1,'title':'[Import public] Test','body':'SACLAY_RADAR_PUBLIC_IMPORT_V1\n\nURL: https://example.org/event'}}
  self.assertEqual(request_url(payload),('https://example.org/event',1));payload['sender']['login']='other'
  with self.assertRaises(PermissionError):request_url(payload)
 def test_signed_link_rejected(self):
  with self.assertRaises(ValueError):public_url('https://example.org/event?access_token=secret')
 def test_real_connector_used_without_inventing_price(self):
  events,source=import_events('https://example.org/event',[],FakeFetcher());self.assertEqual(len(events),1);self.assertIsNone(events[0]['price']);self.assertEqual(source['reliability'],'Faible')
if __name__=='__main__':unittest.main()
