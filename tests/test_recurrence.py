import unittest
from datetime import datetime,timezone
from collectors.connectors import ics_events
BASE='https://example.org/agenda.ics'
def cal(parts):return 'BEGIN:VCALENDAR\r\nVERSION:2.0\r\n'+parts+'\r\nEND:VCALENDAR'
class RecurrenceTests(unittest.TestCase):
 def test_weekly_exdate_and_rdate(self):
  text=cal('BEGIN:VEVENT\r\nUID:weekly\r\nDTSTART;TZID=Europe/Paris:20261019T130000\r\nDTEND;TZID=Europe/Paris:20261019T140000\r\nSUMMARY:Séminaire\r\nRRULE:FREQ=WEEKLY;COUNT=3\r\nEXDATE;TZID=Europe/Paris:20261026T130000\r\nRDATE;TZID=Europe/Paris:20261105T130000\r\nEND:VEVENT')
  result=ics_events(text,BASE,datetime(2026,10,28,tzinfo=timezone.utc))
  self.assertEqual({e['start'][:10] for e in result},{'2026-10-19','2026-11-02','2026-11-05'})
  self.assertEqual(len({e['externalId'] for e in result}),3)
 def test_moved_occurrence(self):
  text=cal('BEGIN:VEVENT\r\nUID:series\r\nDTSTART;TZID=Europe/Paris:20261102T130000\r\nRRULE:FREQ=WEEKLY;COUNT=2\r\nSUMMARY:Initial\r\nEND:VEVENT\r\nBEGIN:VEVENT\r\nUID:series\r\nRECURRENCE-ID;TZID=Europe/Paris:20261109T130000\r\nDTSTART;TZID=Europe/Paris:20261109T150000\r\nSUMMARY:Séance décalée\r\nEND:VEVENT')
  result=ics_events(text,BASE,datetime(2026,10,28,tzinfo=timezone.utc))
  shifted=next(e for e in result if e['title']=='Séance décalée')
  self.assertIn('15:00',shifted['start']);self.assertIn('13:00',shifted['externalId'])
 def test_dst_keeps_local_wall_time(self):
  text=cal('BEGIN:VEVENT\r\nUID:dst\r\nDTSTART;TZID=Europe/Paris:20261019T130000\r\nRRULE:FREQ=WEEKLY;COUNT=2\r\nSUMMARY:Test DST\r\nEND:VEVENT')
  result=ics_events(text,BASE,datetime(2026,10,28,tzinfo=timezone.utc))
  self.assertTrue(any(e['start'].endswith('+02:00') for e in result));self.assertTrue(any(e['start'].endswith('+01:00') for e in result))
 def test_all_day_end_is_exclusive(self):
  text=cal('BEGIN:VEVENT\r\nUID:day\r\nDTSTART;VALUE=DATE:20261102\r\nDTEND;VALUE=DATE:20261104\r\nSUMMARY:Deux journées\r\nEND:VEVENT')
  event=ics_events(text,BASE)[0];self.assertTrue(event['endExclusive']);self.assertEqual(event['end'],'2026-11-04')
if __name__=='__main__':unittest.main()
