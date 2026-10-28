import ICAL from 'ical.js';
import type {RadarEvent} from './types';
import {safeUrl,normalize} from './lib.ts';

export function publicUrl(value:string):string|null{
 const safe=safeUrl(value);if(!safe)return null;const u=new URL(safe);
 if(/^(localhost|127\.|0\.|10\.|192\.168\.|169\.254\.|\[::1\])/.test(u.hostname)||u.hostname.endsWith('.local'))return null;
 if([...u.searchParams.keys()].some(k=>/token|password|secret|signature|api[_-]?key|^sig$/i.test(k)))return null;
 u.hash='';for(const key of [...u.searchParams.keys()])if(key.startsWith('utm_')||['fbclid','gclid'].includes(key))u.searchParams.delete(key);return u.href;
}
export function extractionRequestUrl(url:string):string|null{
 const valid=publicUrl(url);if(!valid)return null;
 const query=new URLSearchParams({title:'[Import public] '+new URL(valid).hostname,body:'SACLAY_RADAR_PUBLIC_IMPORT_V1\n\nURL: '+valid+'\n\nCette demande concerne une annonce publique. Aucun accès privé ni contenu personnel ne doit être publié.'});
 return 'https://github.com/izzki/Saclay-science-radar/issues/new?'+query;
}
function isoWall(time:ICAL.Time,zoneHint?:string):string{
 if(time.isDate)return time.toString();
 const zone=zoneHint||time.zone.tzid;
 if(zone==='UTC'||zone==='Z')return time.toJSDate().toISOString();
 if(zone!=='floating'&&ICAL.TimezoneService.has(zone))return time.toJSDate().toISOString();
 const tz=zone==='floating'?'Europe/Paris':zone;
 const wall=Date.UTC(time.year,time.month-1,time.day,time.hour,time.minute,time.second);let guess=wall;
 const formatter=new Intl.DateTimeFormat('sv-SE',{timeZone:tz,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});
 for(let i=0;i<3;i++){const p=Object.fromEntries(formatter.formatToParts(new Date(guess)).map(x=>[x.type,x.value]));const actual=Date.UTC(+p.year,+p.month-1,+p.day,+p.hour,+p.minute,+p.second);guess+=wall-actual;}
 return new Date(guess).toISOString();
}
export function privateCalendar(text:string,now=new Date()):RadarEvent[]{
 if(text.length>5_000_000)throw new Error('Calendrier trop volumineux (5 Mo maximum par import).');
 const calendar=new ICAL.Component(ICAL.parse(text));
 if(calendar.name!=='vcalendar')throw new Error('Le fichier ne contient pas de calendrier ICS.');
 for(const component of calendar.getAllSubcomponents('vtimezone'))ICAL.TimezoneService.register(new ICAL.Timezone({component}));
 const components=calendar.getAllSubcomponents('vevent');const exceptions=components.filter(c=>c.hasProperty('recurrence-id'));
 const output:RadarEvent[]=[];const floor=new Date(now.getTime()-366*86400000);const ceiling=new Date(now.getTime()+730*86400000);const at=now.toISOString();
 for(const component of components.filter(c=>!c.hasProperty('recurrence-id'))){
  const master=new ICAL.Event(component);
  for(const ex of exceptions)if(ex.getFirstPropertyValue('uid')===master.uid){if(!ex.hasProperty('dtstart'))ex.updatePropertyWithValue('dtstart',ex.getFirstPropertyValue('recurrence-id'));if(!ex.hasProperty('summary'))ex.updatePropertyWithValue('summary',master.summary);master.relateException(ex);}
  const recurring=master.isRecurring();const iterator=recurring?master.iterator():null;let iterations=0;
  while(true){
   if(++iterations>10000)throw new Error('Une série récurrente est trop dense pour un import sûr sur cet appareil.');
   const next=iterator?.next();if(recurring&&!next)break;
   const detail=next?master.getOccurrenceDetails(next):{item:master,startDate:master.startDate,endDate:master.endDate};
   const item=detail.item;const hint=String(item.component.getFirstProperty('dtstart')?.getParameter('tzid')||'');
   const start=isoWall(detail.startDate,hint||undefined);const instant=new Date(start.length===10?start+'T12:00Z':start);
   if(recurring&&instant>ceiling)break;
   if(!recurring||instant>=floor){
    const hasEnd=item.component.hasProperty('dtend')||item.component.hasProperty('duration');
    const end=hasEnd?isoWall(detail.endDate,hint||undefined):null;
    const url=safeUrl(String(item.component.getFirstPropertyValue('url')||''))||'';
    const description=item.description||'';const title=item.summary||'Événement du calendrier privé';const words=normalize(title+' '+description);
    const disciplines=[['Photonique',/photon|optique|laser|optical/],['Quantique',/quantique|quantum|qubit/],['Instrumentation',/instrument|metrolog|capteur/],['Deeptech',/deeptech|startup|innovation/]].filter(([,rx])=>(rx as RegExp).test(words)).map(([name])=>String(name));
    const organizer=String(item.component.getFirstProperty('organizer')?.getParameter('cn')||'Calendrier personnel');
    output.push({id:'private-'+encodeURIComponent(master.uid||title)+'-'+(next?next.toString():start),title,description,start,end,endExclusive:!!end&&detail.endDate.isDate,timezone:hint||'Europe/Paris',organizer,location:item.location||null,address:null,city:null,format:'Non précisé',category:'Calendrier importé',disciplines:disciplines.length?disciplines:['Sciences générales'],price:null,currency:null,studentPrice:null,priceLabel:'Non précisé',access:'Annonce privée importée sur cet appareil uniquement',registration:null,registrationUrl:null,deadline:null,speakers:[],companies:[],labs:[],level:null,url,status:item.component.getFirstPropertyValue('status')==='CANCELLED'?'Annulé':'À confirmer',reliability:'Faible',sources:[{id:'private',name:'Calendrier privé importé localement',url,listingUrl:url,checkedAt:at}],firstSeen:at,lastVerified:at,history:[],score:{total:0,parts:{'Import privé non classé':0},reasons:['Annonce privée : aucune vérification publique ni scoring automatique.']},local:true,privacy:'private',warnings:['Import local : ces informations ne sont pas envoyées au dépôt ou au collecteur. Les dates sont celles du fichier importé.']});
   }
   if(!recurring)break;
  }
 }
 return output;
}
