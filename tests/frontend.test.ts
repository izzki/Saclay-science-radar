import test from 'node:test';
import assert from 'node:assert/strict';
import type {RadarEvent} from '../src/types.ts';
import {EMPTY_FILTERS,filterEvents,toIcs,safeUrl,dayInParis,scoreLabel,validateLocalEvent} from '../src/lib.ts';
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
