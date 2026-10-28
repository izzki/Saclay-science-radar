import test from 'node:test';
import assert from 'node:assert/strict';
import type {RadarEvent} from '../src/types.ts';
import {EMPTY_FILTERS,filterEvents,toIcs,safeUrl,dayInParis,scoreLabel,validateLocalEvent,eventPhase,sortEvents,mergeLocalEvents} from '../src/lib.ts';
const e={id:'test',title:'Optique, quantique\nTest',description:'Description',start:'2026-11-03T11:00:00+01:00',end:null,url:'https://example.org/',city:'Palaiseau',organizer:'Laboratoire',disciplines:['Photonique'],category:'Séminaire',format:'Présentiel',price:null,currency:null,access:null,reliability:'Élevée',score:{total:22}} as RadarEvent;
const today=new Date('2026-10-28T12:00:00Z');
test('aucun score faible exclu du mode exhaustif',()=>assert.equal(filterEvents([e],EMPTY_FILTERS,today).length,1));
test('tarif inconnu distinct de gratuit',()=>{assert.equal(filterEvents([e],{...EMPTY_FILTERS,price:'free'},today).length,0);assert.equal(filterEvents([e],{...EMPTY_FILTERS,price:'unknown'},today).length,1);});
test('recherche insensible aux accents',()=>assert.equal(filterEvents([e],{...EMPTY_FILTERS,search:'OPTIQUE'},today).length,1));
test('filtres combinés',()=>assert.equal(filterEvents([e],{...EMPTY_FILTERS,city:'Paris',discipline:'Photonique'},today).length,0));
test('archives explicites',()=>{assert.equal(filterEvents([e],EMPTY_FILTERS,new Date('2027-01-01')).length,0);assert.equal(filterEvents([e],{...EMPTY_FILTERS,archives:true},new Date('2027-01-01')).length,1);});
test('heure française près de minuit UTC',()=>assert.equal(dayInParis(new Date('2026-11-01T23:30:00Z')),'2026-11-02'));
test('URL active et credentials refusés',()=>{assert.equal(safeUrl('javascript:alert(1)'),null);assert.equal(safeUrl('https://a:b@example.org'),null);});
test('export ICS UTC, échappement et pas de durée inventée',()=>{const s=toIcs(e,today);assert.ok(s.includes('DTSTART:20261103T100000Z'));assert.ok(s.includes('SUMMARY:Optique\\, quantique\\nTest'));assert.ok(!s.includes('DTEND:'));});
test('ICS UTF8 respecte 75 octets',()=>{for(const line of toIcs({...e,title:'É'.repeat(120)},today).split('\r\n'))assert.ok(new TextEncoder().encode(line).length<=75);});
test('seuils de classement',()=>{assert.equal(scoreLabel(85),'Priorité exceptionnelle');assert.equal(scoreLabel(29),'Peu pertinent');});

test('une sauvegarde refuse les avertissements mal formés',()=>{
 const value={...e,timezone:'Europe/Paris',location:null,address:null,studentPrice:null,priceLabel:'Non précisé',registration:null,registrationUrl:null,deadline:null,speakers:[],companies:[],labs:[],level:null,status:'À confirmer',firstSeen:'2026-10-28T00:00:00Z',lastVerified:'2026-10-28T00:00:00Z',history:[],sources:[],score:{total:0,parts:{},reasons:[]}};
 assert.equal(validateLocalEvent(value),true);
 assert.equal(validateLocalEvent({...value,warnings:{invalid:true}}),false);
});

test('un événement terminé aujourd’hui est masqué à l’heure réelle',()=>{
 const ended={...e,start:'2026-10-28T14:00:00+01:00',end:'2026-10-28T15:00:00+01:00'};
 const now=new Date('2026-10-28T16:00:00Z');assert.equal(eventPhase(ended,now),'ended');assert.equal(filterEvents([ended],EMPTY_FILTERS,now).length,0);
 assert.equal(filterEvents([ended],{...EMPTY_FILTERS,timeScope:'past'},now).length,1);
});
test('fin inconnue : déjà commencé ne signifie pas confirmé terminé',()=>{
 const started={...e,start:'2026-10-28T14:00:00+01:00',end:null};assert.equal(eventPhase(started,new Date('2026-10-28T16:00Z')),'started');assert.equal(filterEvents([started],EMPTY_FILTERS,new Date('2026-10-28T16:00Z')).length,0);
});
test('événement en cours et fin ICS exclusive',()=>{
 const ongoing={...e,start:'2026-10-26',end:'2026-10-29',endExclusive:true};assert.equal(eventPhase(ongoing,new Date('2026-10-28T12:00Z')),'ongoing');assert.equal(eventPhase(ongoing,new Date('2026-10-29T12:00Z')),'ended');
});
test('tri chronologique explicite dans les deux sens',()=>{
 const later={...e,id:'later',start:'2026-12-01'};assert.equal(sortEvents([later,e],'date-asc')[0].id,e.id);assert.equal(sortEvents([later,e],'date-desc')[0].id,'later');
});
test('mots-clés séparés par virgules et noms d’intervenants',()=>{
 const item={...e,speakers:[{name:'Camille Test',institution:'Laboratoire'}]};assert.equal(filterEvents([item],{...EMPTY_FILTERS,search:'optique, Camille'},today).length,1);
});

test('les sept derniers jours fonctionnent dans les archives',()=>{const past={...e,start:'2026-10-24T11:00:00+02:00',end:null};assert.equal(filterEvents([past],{...EMPTY_FILTERS,timeScope:'past',period:'week'},today).length,1);});
test('réimport local : la nouvelle séance remplace la précédente et conserve son historique',()=>{const old={...e,history:[],firstSeen:'2026-10-01T00:00Z'};const newer={...old,start:'2026-11-03T14:00:00+01:00'};const result=mergeLocalEvents([old],[newer]);assert.equal(result.length,1);assert.equal(result[0].firstSeen,old.firstSeen);assert.equal(result[0].history.length,1);assert.equal(result[0].start,newer.start);});

test('les annonces datées restent accessibles en 2027, 2028 et au-delà',()=>{
 const events=[{...e,id:'a',start:'2027-11-15',end:'2027-11-19'},{...e,id:'b',start:'2028-08-27',end:'2028-09-01'},{...e,id:'c',start:'2035-12-10',end:null}];
 assert.equal(filterEvents(events,{...EMPTY_FILTERS},today).length,3);
 assert.deepEqual(filterEvents(events,{...EMPTY_FILTERS,year:'2027'},today).map(x=>x.id),['a']);
 assert.deepEqual(filterEvents(events,{...EMPTY_FILTERS,year:'2028'},today).map(x=>x.id),['b']);
 assert.equal(filterEvents(events,{...EMPTY_FILTERS,year:'2035'},today).length,1);
});
test('filtre année inclut un programme chevauchant le nouvel an',()=>{
 const event={...e,start:'2027-12-29',end:'2028-01-05'};
 assert.equal(filterEvents([event],{...EMPTY_FILTERS,year:'2028'},today).length,1);
 assert.equal(filterEvents([event],{...EMPTY_FILTERS,year:'2029'},today).length,0);
});
