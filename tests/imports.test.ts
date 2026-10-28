import test from 'node:test';
import assert from 'node:assert/strict';
import {privateCalendar,publicUrl,extractionRequestUrl} from '../src/imports.ts';
import {validateLocalEvent,toIcs} from '../src/lib.ts';
const at=new Date('2026-10-28T12:00Z');
const wrap=(event:string)=>'BEGIN:VCALENDAR\r\nVERSION:2.0\r\n'+event+'\r\nEND:VCALENDAR';
test('calendrier privé sans URL reste local sans inventer de lien',()=>{
 const [e]=privateCalendar(wrap('BEGIN:VEVENT\r\nUID:local\r\nDTSTART;TZID=Europe/Paris:20261103T130000\r\nSUMMARY:Séminaire privé\r\nEND:VEVENT'),at);
 assert.equal(e.start,'2026-11-03T12:00:00.000Z');assert.equal(e.url,'');assert.equal(e.privacy,'private');assert.equal(validateLocalEvent(e),true);
});
test('import privé récurrent avec exclusion et exception horaire',()=>{
 const events=privateCalendar(wrap('BEGIN:VEVENT\r\nUID:series\r\nDTSTART;TZID=Europe/Paris:20261102T130000\r\nRRULE:FREQ=WEEKLY;COUNT=3\r\nEXDATE;TZID=Europe/Paris:20261109T130000\r\nSUMMARY:Séminaire\r\nEND:VEVENT\r\nBEGIN:VEVENT\r\nUID:series\r\nRECURRENCE-ID;TZID=Europe/Paris:20261116T130000\r\nDTSTART;TZID=Europe/Paris:20261116T150000\r\nSUMMARY:Séance déplacée\r\nEND:VEVENT'),at);
 assert.equal(events.length,2);assert.ok(events.some(e=>e.title==='Séance déplacée'&&e.start.includes('14:00')));
});
test('pas de publication d’un lien signé ou de localhost',()=>{assert.equal(publicUrl('https://example.org/?token=secret'),null);assert.equal(extractionRequestUrl('http://localhost/private'),null);assert.equal(publicUrl('https://example.org/event?utm_source=x#top'),'https://example.org/event');});
test('réexport d’une date de fin ICS exclusive ne gagne pas un jour',()=>{
 const [e]=privateCalendar(wrap('BEGIN:VEVENT\r\nUID:day\r\nDTSTART;VALUE=DATE:20261103\r\nDTEND;VALUE=DATE:20261104\r\nSUMMARY:Journée privée\r\nEND:VEVENT'),at);assert.ok(toIcs(e,at).includes('DTEND;VALUE=DATE:20261104'));
});
