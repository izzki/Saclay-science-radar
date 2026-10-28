"""Inventaire initial. Une URL candidate n'est pas une source automatisée validée."""
import json
from pathlib import Path

GROUPS={
'Campus Paris-Saclay':[
('Institut d’Optique Graduate School','https://www.institutoptique.fr/agenda'),('Laboratoire Charles Fabry','https://www.lcf.institutoptique.fr/agenda'),
('École polytechnique','https://www.polytechnique.edu/evenements'),('Institut Polytechnique de Paris','https://www.ip-paris.fr/actualites/agenda'),
('CentraleSupélec','https://www.centralesupelec.fr/'),('ENS Paris-Saclay','https://ens-paris-saclay.fr/agenda'),('Université Paris-Saclay','https://www.universite-paris-saclay.fr/actualites/agenda'),
('Faculté des sciences d’Orsay','https://www.sciences.universite-paris-saclay.fr/'),('Graduate Schools Paris-Saclay','https://www.universite-paris-saclay.fr/graduate-schools'),
('Écoles doctorales Paris-Saclay','https://www.universite-paris-saclay.fr/recherche/doctorat-et-hdr'),('Institut Pascal','https://www.institut-pascal.universite-paris-saclay.fr/'),
('LUMEN Paris-Saclay','https://www.lumen.universite-paris-saclay.fr/'),('AgroParisTech','https://www.agroparistech.fr/'),('Télécom Paris','https://www.telecom-paris.fr/'),
('ENSTA','https://www.ensta.fr/'),('ENSAE Paris','https://www.ensae.fr/'),('Mines Paris – PSL','https://www.minesparis.psl.eu/'),('HEC Paris — innovation','https://www.hec.edu/fr')],
'Laboratoires et recherche':[
('C2N','https://www.c2n.universite-paris-saclay.fr/fr/agenda/'),('ISMO','https://www.ismo.universite-paris-saclay.fr/'),('Laboratoire de Physique des Solides','https://www.lps.u-psud.fr/'),
('Laboratoire Aimé Cotton','https://www.lac.universite-paris-saclay.fr/'),('IJCLab','https://www.ijclab.in2p3.fr/'),('Laboratoire d’Optique Appliquée','https://loa.ensta-paris.fr/'),
('Laboratoire Kastler Brossel','https://www.lkb.fr/'),('CEA Paris-Saclay','https://www.cea.fr/paris-saclay/'),('CEA List','https://list.cea.fr/'),('CEA Leti','https://www.leti-cea.fr/'),
('CEA IRAMIS','https://iramis.cea.fr/'),('CEA SPEC','https://iramis.cea.fr/spec/'),('CEA NeuroSpin','https://joliot.cea.fr/drf/joliot/Pages/Entites/NeuroSpin.aspx'),
('Inria Saclay','https://www.inria.fr/fr/centre-inria-de-saclay'),('GeePs','https://geeps.centralesupelec.fr/'),('ONERA','https://www.onera.fr/'),('CNRS','https://www.cnrs.fr/fr/agenda'),
('LULI','https://portail.polytechnique.edu/luli/'),('CPHT','https://www.cpht.polytechnique.fr/'),('LLR','https://llr.in2p3.fr/'),('LadHyX','https://www.ladhyx.polytechnique.fr/'),
('Institut de physique théorique CEA','https://www.ipht.fr/'),('CEA IRFU','https://irfu.cea.fr/'),('SOLEIL','https://www.synchrotron-soleil.fr/'),
('LSI','https://lsi.ip-paris.fr/'),('LMPS','https://lmps.ens-paris-saclay.fr/'),('L2S','https://l2s.centralesupelec.fr/'),('SATIE','https://satie.ens-paris-saclay.fr/'),('LISN','https://www.lisn.upsaclay.fr/')],
'Quantique et photonique':[
('Quantum-Saclay','https://www.quantum-saclay.fr/'),('France Quantum','https://www.francequantum.fr/'),('Société Française d’Optique','https://www.sfoptique.org/'),
('Société Française de Physique','https://www.sfpnet.fr/'),('Photonics France','https://www.photonics-france.org/'),('Quandela','https://www.quandela.com/'),('PASQAL','https://www.pasqal.com/'),
('Alice & Bob','https://alice-bob.com/'),('C12','https://www.c12qe.com/'),('Welinq','https://www.welinq.eu/'),('Exail','https://www.exail.com/'),('Thales','https://www.thalesgroup.com/'),
('Safran','https://www.safran-group.com/'),('STMicroelectronics','https://www.st.com/'),('Eviden','https://eviden.com/'),('Quantonation','https://www.quantonation.com/'),
('Le Lab Quantique','https://lelabquantique.com/'),('Systematic Paris-Region','https://systematic-paris-region.org/'),('Opticsvalley — Systematic','https://systematic-paris-region.org/hub-optics-photonics/'),('QICS','https://qics.sorbonne-universite.fr/')],
'Innovation et entreprises':[
('French Tech Paris-Saclay','https://www.lafrenchtech-paris-saclay.fr/'),('21st by CentraleSupélec','https://www.21st.centralesupelec.fr/'),('Paris-Saclay SPRING','https://paris-saclay-spring.com/'),
('SATT Paris-Saclay','https://satt-paris-saclay.fr/'),('Incubateur IncubAlliance','https://www.incuballiance.fr/'),('STATION F','https://stationf.co/'),('Bpifrance','https://www.bpifrance.fr/'),
('Bpifrance BIG','https://big.bpifrance.fr/'),('Hello Tomorrow','https://hello-tomorrow.org/'),('Deeptech Bpifrance','https://deeptech.bpifrance.fr/'),('Agoranov','https://www.agoranov.com/'),
('Incubateur IP Paris','https://www.ip-paris.fr/innovation'),('Établissement public Paris-Saclay','https://epa-paris-saclay.fr/'),('Choose Paris Region','https://www.chooseparisregion.org/'),
('Pôle Medicen','https://www.medicen.org/'),('SupOptique Alumni','https://www.supoptique-alumni.com/')],
'Paris et culture scientifique':[
('Collège de France','https://www.college-de-france.fr/fr/agenda'),('Académie des sciences','https://www.academie-sciences.fr/'),('Sorbonne Université','https://www.sorbonne-universite.fr/agenda'),
('Université Paris Cité','https://u-paris.fr/agenda/'),('Université PSL','https://psl.eu/agenda'),('École normale supérieure','https://www.ens.psl.eu/agenda'),('ESPCI Paris – PSL','https://www.espci.psl.eu/'),
('Institut Langevin','https://www.institut-langevin.espci.fr/'),('Institut Curie','https://curie.fr/'),('Observatoire de Paris','https://www.observatoiredeparis.psl.eu/'),
('Institut Henri Poincaré','https://www.ihp.fr/fr/agenda'),('CNRS Physique','https://www.inp.cnrs.fr/'),('Muséum national d’Histoire naturelle','https://www.mnhn.fr/fr/agenda'),
('Cité des sciences et de l’industrie','https://www.cite-sciences.fr/'),('Palais de la découverte','https://www.palais-decouverte.fr/'),('CNRS Île-de-France','https://www.iledefrance-gif.cnrs.fr/'),
('Institut d’astrophysique de Paris','https://www.iap.fr/'),('Institut Jacques Monod','https://www.ijm.fr/'),('Institut de la Vision','https://www.institut-vision.org/')],
'Salons et grands rendez-vous':[
('Forum de la Photonique','https://www.forumdelaphotonique.fr/'),('Paris-Saclay Summit','https://www.paris-saclay-summit.com/'),('VivaTech','https://vivatechnology.com/'),
('Fête de la science','https://www.fetedelascience.fr/'),('Nuit européenne des chercheurs','https://www.lanuitdeschercheurs-france.eu/'),('Forum entreprises Polytechnique','https://www.forum-polytechnique.com/')],
'Plateformes transversales':[
('OpenAgenda','https://openagenda.com/'),('Sciencesconf','https://www.sciencesconf.org/'),('Eventbrite','https://www.eventbrite.fr/'),('Luma','https://lu.ma/'),('Meetup','https://www.meetup.com/'),('HelloAsso','https://www.helloasso.com/')],
'Réseaux et annonces manuelles':[
('LinkedIn — recherche d’annonces publiques','https://www.linkedin.com/'),('X — annonces publiques','https://x.com/'),('Instagram — annonces publiques','https://www.instagram.com/'),
('Bluesky — annonces publiques','https://bsky.app/'),('Mastodon — annonces publiques','https://joinmastodon.org/'),('YouTube — chaînes scientifiques','https://www.youtube.com/')]
}

ACTIVE={'Laboratoire Charles Fabry','Institut d’Optique Graduate School','C2N','CEA IRAMIS','Université Paris-Saclay','ENS Paris-Saclay','École polytechnique','Institut Polytechnique de Paris','Collège de France','Institut Henri Poincaré','Laboratoire Kastler Brossel','Sorbonne Université','Université PSL','École normale supérieure','Institut de physique théorique CEA','ISMO','IJCLab','Laboratoire de Physique des Solides','Quantum-Saclay','Photonics France'}

def seed():
    out=[]
    for group,items in GROUPS.items():
        for name,url in items:
            sid='s'+str(len(out)+1).zfill(3)
            unavailable=group in ('Réseaux et annonces manuelles','Plateformes transversales')
            out.append({'id':sid,'name':name,'url':url,'group':group,'connector':'auto','enabled':name in ACTIVE,
                'priority':name in {'Laboratoire Charles Fabry','C2N','CEA IRAMIS','Quantum-Saclay'},
                'status':'Surveillance automatique indisponible' if unavailable else 'À tester' if name in ACTIVE else 'Inventoriée — intégration nécessaire',
                'reliability':'Élevée','note':'URL candidate : contrôle HTTP et format nécessaires. Aucun agenda ni événement public supposé.' if not unavailable else 'Lien direct uniquement. Aucun accès automatique configuré ; pas de collecte privée.'})
    return out

if __name__=='__main__':
    p=Path('data/sources.json')
    if not p.exists():p.write_text(json.dumps(seed(),ensure_ascii=False,indent=2)+'\n')
    print(len(json.loads(p.read_text())),'sources inventoriées')
