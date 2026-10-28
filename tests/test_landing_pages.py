import unittest
from collectors.connectors import extract,ics_events
from collectors.landing_pages import enrich_forum
from collectors.crawl import collection_queue,is_listing_page

class LandingTests(unittest.TestCase):
    def test_forum_banner_does_not_reuse_exhibitors_or_deadlines(self):
        html='<main><section><h1>FORUM DE LA PHOTONIQUE</h1><p>40e édition le19 novembre 2026 uniquement sur inscription</p></section><p>Inscription avant le 15 octobre 2026</p><h2>Ils nous ont fait confiance en 2025</h2><p>Sponsor précédent</p></main>'
        e=extract(html,'https://www.forumdelaphotonique.fr/',{})[0]
        self.assertEqual(e['start'],'2026-11-19');self.assertNotIn('Sponsor précédent',e['description'])
        self.assertFalse(e.get('price'));self.assertFalse(e.get('companies'))
        visitor='<main><p>Le Forum se déroule au bâtiment 503.</p><a href="https://forms.gle/visitor">Inscription visiteur</a></main>'
        enriched=enrich_forum(e,visitor,'https://www.forumdelaphotonique.fr/espace-visiteur')
        self.assertEqual(enriched['location'],'bâtiment 503');self.assertEqual(enriched['registrationUrl'],'https://forms.gle/visitor')

    def test_forum_without_current_banner_date_is_not_extrapolated(self):
        html='<main><section><h1>Forum de la Photonique</h1><p>Prochaine édition à annoncer</p></section><p>Les sponsors du 19 novembre 2026</p></main>'
        self.assertEqual(extract(html,'https://www.forumdelaphotonique.fr/',{}),[])

    def test_quest_dates_are_current_but_old_keynotes_are_not(self):
        html='<p>QUEST-IS 2027 EDF Lab, PARIS Saclay</p><h2 class="elementor-heading-title">6th December 2027</h2><h2 class="elementor-heading-title">10th December 2027</h2><p>In the heart of quantum engineering. Learn more QUEST-IS’25 KEYNOTE SPEAKERS Someone</p>'
        e=extract(html,'https://conference-questis.org/',{})[0]
        self.assertEqual((e['start'],e['end']),('2027-12-06','2027-12-10'));self.assertFalse(e.get('speakers'))

    def test_cigre_cross_month_in_2028_does_not_read_stand_price(self):
        html='<p>Technical Exhibition Paris Session 2028</p><p>27 August to 01 September, 2028</p><p>Palais des Congrès, Paris</p><p>Exhibitor insurance €400 per square metre</p>'
        e=extract(html,'https://www.cigre-exhibition.com/',{})[0]
        self.assertEqual((e['start'],e['end']),('2028-08-27','2028-09-01'));self.assertIsNone(e.get('price'))

    def test_sfo_scoped_date_interval(self):
        html='<main><div class="row-content"><h2 class="row-title">OPTDIAG 2027 - du 19 au 21 mai 2027 à Paris</h2><p>Photonique, Institut Langevin</p></div></main>'
        e=extract(html,'https://www.sfoptique.org/',{})[0]
        self.assertEqual((e['start'],e['end']),('2027-05-19','2027-05-21'))

    def test_quantum_networks_two_days(self):
        html='<p>4TH EDITION 7|8 April 2027</p><h1>Towards Fully Quantum Networks</h1><p>Palais des Congrès de Paris</p>'
        e=extract(html,'https://www.uppersideconferences.com/quantum-networks/2027/index.html',{})[0]
        self.assertEqual((e['start'],e['end']),('2027-04-07','2027-04-08'))

    def test_parser_cannot_be_applied_on_another_domain(self):
        html='<section><h1>Forum de la Photonique</h1><p>19 novembre 2026</p></section>'
        self.assertEqual(extract(html,'https://unrelated.example/',{}),[])

    def test_last_calendar_page_precedes_detail_pages_and_resumes(self):
        base='https://www.ihp.fr/fr/agenda';detail=base+'/seminaire';p1=base+'?page=1';p10=base+'?page=10';pending=base+'?page=6'
        self.assertEqual(collection_queue([detail,p1,p10],[pending,detail],base),[pending,p10,p1,detail])
        self.assertFalse(is_listing_page('https://evil.example/fr/agenda?page=10',base))
        self.assertFalse(is_listing_page(base+'/seminaire?page=2',base))

    def test_explicit_ics_dates_have_no_future_cutoff(self):
        ics='BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:future\r\nSUMMARY:Future dated event\r\nDTSTART;VALUE=DATE:20351210\r\nEND:VEVENT\r\nEND:VCALENDAR'
        self.assertEqual(ics_events(ics,'https://example.org/cal.ics')[0]['start'],'2035-12-10')

    def test_social_games_are_outside_scientific_scope(self):
        from collectors.model import make_event
        from collectors.quality import clean_catalog
        source={'id':'test','name':'Université de test','url':'https://example.org/agenda'}
        event=make_event({'title':'Game Night','description':'Soirée de jeux au centre étudiant','start':'2027-07-09','url':'https://example.org/agenda/game-night'},source)
        accepted,quarantine=clean_catalog([event])
        self.assertEqual(accepted,[]);self.assertEqual(len(quarantine),1)

    def test_practical_page_is_kept_as_provenance(self):
        from collectors.model import make_event
        raw={'title':'Forum de la Photonique','start':'2026-11-19','url':'https://www.forumdelaphotonique.fr/'}
        raw=enrich_forum(raw,'<p>bâtiment 503</p>','https://www.forumdelaphotonique.fr/espace-visiteur')
        event=make_event(raw,{'id':'s103','name':'Forum','url':raw['url']})
        self.assertEqual(len(event['sources']),2)
        self.assertTrue(any(s['url'].endswith('/espace-visiteur') for s in event['sources']))
