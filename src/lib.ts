import type { Filters, RadarEvent } from './types.ts';
export const EMPTY_FILTERS:Filters={search:'',period:'all',year:'',from:'',to:'',city:'',zone:'',price:'',discipline:'',organizer:'',category:'',score:'',reliability:'',format:'',access:'',archives:false,timeScope:'future',sort:'date-asc'};
export const normalize=(s:string)=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
export function safeUrl(value:unknown):string|null {try{const u=new URL(String(value));return ['https:','http:'].includes(u.protocol)&&!u.username&&!u.password?u.href:null;}catch{return null;}}
export function dayInParis(now=new Date()):string {return new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Paris',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);}
export type EventPhase='upcoming'|'ongoing'|'ended'|'started'|'today';
export function eventPhase(e:RadarEvent,now=new Date()):EventPhase{
 const today=dayInParis(now);const startDay=e.start.slice(0,10);
 if(e.end){
  const ended=e.end.length===10?(e.endExclusive?today>=e.end:today>e.end):now.getTime()>=Date.parse(e.end);
  if(ended)return 'ended';
  const began=e.start.length===10?today>=startDay:now.getTime()>=Date.parse(e.start);
  return began?'ongoing':'upcoming';
 }
 if(startDay<today)return 'ended';
 if(startDay>today)return 'upcoming';
 if(e.start.length===10)return 'today';
 return Date.parse(e.start)<=now.getTime()?'started':'upcoming';
}
export function phaseLabel(e:RadarEvent,now=new Date()):string{
 const phase=eventPhase(e,now);
 return phase==='ended'?'Terminé':phase==='ongoing'?'En cours':phase==='started'?'Déjà commencé · fin non précisée':phase==='today'?'Aujourd’hui · heure non précisée':'À venir';
}
export function endLabel(e:RadarEvent):string{
 if(!e.end)return 'Fin non précisée';
 let end=e.end;
 if(end.length===10&&e.endExclusive){const d=new Date(end+'T12:00Z');d.setUTCDate(d.getUTCDate()-1);end=d.toISOString().slice(0,10);}
 return formatDate(end,true);
}
export function searchTokens(search:string):string[]{return (search.match(/"[^"]+"|[^\s,;]+/g)||[]).map(x=>normalize(x.replace(/^"|"$/g,'')).trim()).filter(Boolean);}
export function sortEvents(events:RadarEvent[],sort:Filters['sort']='date-asc'):RadarEvent[]{
 return [...events].sort((a,b)=>sort==='score'?b.score.total-a.score.total||a.start.localeCompare(b.start):sort==='date-desc'?b.start.localeCompare(a.start):sort==='newest'?b.firstSeen.localeCompare(a.firstSeen):sort==='price-asc'?(a.price??Infinity)-(b.price??Infinity)||a.start.localeCompare(b.start):a.start.localeCompare(b.start));
}
export function filterEvents(events:RadarEvent[],f:Filters,now=new Date()):RadarEvent[]{
 const today=dayInParis(now);const limit=new Date(today+'T12:00:00Z');
 const backwards=(f.timeScope==='past'&&!f.archives);
 if(f.period==='week')limit.setUTCDate(limit.getUTCDate()+(backwards?-7:7));if(f.period==='month')limit.setUTCDate(limit.getUTCDate()+(backwards?-30:30));
 const cities=['palaiseau','orsay','gif-sur-yvette','saclay','bures-sur-yvette','saint-aubin'];
 const scope=f.archives?'all':f.timeScope||'future';
 return events.filter(e=>{
  const day=(e.end||e.start).slice(0,10);const start=e.start.slice(0,10);const phase=eventPhase(e,now);
  const hay=normalize([e.title,e.description,e.organizer,e.city,e.category,...e.disciplines,...e.speakers?.map(s=>s.name+' '+(s.institution||''))||[],...e.companies||[],...e.labs||[]].join(' '));
  const temporal=scope==='all'||(scope==='past'?['ended','started'].includes(phase):!['ended','started'].includes(phase));
  return temporal&&searchTokens(f.search).every(w=>hay.includes(w))&&
   (f.period==='all'||(scope==='past'?(start<=today&&day>=limit.toISOString().slice(0,10)):(day>=today&&start<=limit.toISOString().slice(0,10))))&&(!f.year||(start<=f.year+'-12-31'&&day>=f.year+'-01-01'))&&(!f.from||day>=f.from)&&(!f.to||start<=f.to)&&
   (!f.city||e.city===f.city)&&(!f.zone||(f.zone==='saclay'?cities.includes(normalize(e.city||'')):f.zone==='paris'?normalize(e.city||'')==='paris':f.zone==='online'?['En ligne','Hybride'].includes(e.format):true))&&
   (!f.price||(f.price==='free'?e.price===0:f.price==='unknown'?e.price===null:f.price==='paid'?e.price!==null&&e.price>0:e.price!==null&&e.currency==='EUR'&&e.price<=Number(f.price)))&&
   (!f.discipline||e.disciplines.includes(f.discipline))&&(!f.organizer||e.organizer===f.organizer)&&(!f.category||e.category===f.category)&&
   (!f.score||e.score.total>=Number(f.score))&&(!f.reliability||e.reliability===f.reliability)&&(!f.format||e.format===f.format)&&
   (!f.access||(f.access==='unknown'?!e.access:!!e.access));
 });
}
export function scoreLabel(n:number):string{return n>=85?'Priorité exceptionnelle':n>=70?'Très recommandé':n>=50?'Intéressant':n>=30?'Secondaire':'Peu pertinent';}
export function verdict(n:number):string{return n>=85?'Je recommande fortement.':n>=70?'Je recommande.':n>=50?'Optionnel.':'Peu intéressant pour ton projet.';}
export function formatDate(value:string|null|undefined,includeTime=false):string{
 if(!value)return 'Non précisé';const d=new Date(value.length===10?value+'T12:00:00Z':value);
 if(Number.isNaN(d.getTime()))return 'Date non valide';
 return new Intl.DateTimeFormat('fr-FR',{dateStyle:'medium',...(includeTime&&value.length>10?{timeStyle:'short'}:{}),timeZone:'Europe/Paris'}).format(d);
}
export function eventTime(e:RadarEvent):string {return e.start.length===10?'Heure non précisée':new Intl.DateTimeFormat('fr-FR',{hour:'2-digit',minute:'2-digit',timeZone:'Europe/Paris'}).format(new Date(e.start));}
export function isStale(value?:string,days=2):boolean{return !value||Date.now()-new Date(value).getTime()>days*86400000;}
export function recommendation(e:RadarEvent):string{
 if(e.disciplines.includes('Photonique'))return 'Explore les techniques optiques annoncées et leur place dans la R&D expérimentale.';
 if(e.disciplines.includes('Quantique'))return 'Un éclairage quantique ; vérifie le lien avec le matériel expérimental dans le programme.';
 if(e.disciplines.includes('Deeptech'))return 'Découvre le passage de la recherche au développement industriel.';
 return 'Élargis ta culture scientifique à partir du programme officiel.';
}
const esc=(v:string)=>v.replace(/\\/g,'\\\\').replace(/\r\n|\r|\n/g,'\\n').replace(/;/g,'\\;').replace(/,/g,'\\,');
export function toIcs(e:RadarEvent,now=new Date()):string {
 const stamp=(d:string)=>new Date(d).toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z/,'Z');
 const dateOnly=e.start.length===10;
 const lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Saclay Science Radar//FR','CALSCALE:GREGORIAN','BEGIN:VEVENT',`UID:${esc(e.id)}@saclay-science-radar`,`DTSTAMP:${stamp(now.toISOString())}`,dateOnly?`DTSTART;VALUE=DATE:${e.start.replace(/-/g,'')}`:`DTSTART:${stamp(e.start)}`];
 if(e.end){let end=e.end;if(end.length===10&&!e.endExclusive){const d=new Date(end+'T12:00Z');d.setUTCDate(d.getUTCDate()+1);end=d.toISOString().slice(0,10);}lines.push(end.length===10?`DTEND;VALUE=DATE:${end.replace(/-/g,'')}`:`DTEND:${stamp(end)}`);}
 lines.push(`SUMMARY:${esc(e.title)}`,`DESCRIPTION:${esc(e.description+(e.url?'\nSource : '+e.url:''))}`);
 if(safeUrl(e.url))lines.push(`URL:${esc(e.url)}`);
 if(e.location||e.address)lines.push(`LOCATION:${esc([e.location,e.address].filter(Boolean).join(', '))}`);
 if(e.status==='Annulé')lines.push('STATUS:CANCELLED');
 lines.push('END:VEVENT','END:VCALENDAR');
 // RFC 5545: fold at 75 octets, preserving UTF-8 code points.
 return lines.map(line=>{let rows='';let size=0;for(const char of line){const bytes=new TextEncoder().encode(char).length;if(size+bytes>75){rows+='\r\n ';size=1;}rows+=char;size+=bytes;}return rows;}).join('\r\n')+'\r\n';
}
export function download(name:string,text:string,type='application/json'):void{const url=URL.createObjectURL(new Blob([text],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
export function localRead<T>(key:string,fallback:T):T{try{return JSON.parse(localStorage.getItem(key)||'null')??fallback;}catch{return fallback;}}
export function localWrite(key:string,value:unknown):boolean{try{localStorage.setItem(key,JSON.stringify(value));return true;}catch{return false;}}
export function validateLocalEvent(x:unknown):x is RadarEvent {
 if(!x||typeof x!=='object')return false;const e=x as RadarEvent;
 const strings=['id','title','start','organizer','description','format','category','priceLabel','status','reliability','firstSeen','lastVerified','timezone'] as const;
 if(!strings.every(k=>typeof e[k]==='string')||e.title.length<4||!/^\d{4}-\d{2}-\d{2}(T.*)?$/.test(e.start)||Number.isNaN(new Date(e.start).getTime())||(!safeUrl(e.url)&&!(e.privacy==='private'&&!e.url)))return false;
 if(e.end!==null&&(typeof e.end!=='string'||Number.isNaN(new Date(e.end).getTime())))return false;
 if(e.price!==null&&(typeof e.price!=='number'||!Number.isFinite(e.price)||e.price<0))return false;
 if(!['city','location','address','access','registration','level','currency'].every(k=>e[k as keyof RadarEvent]===null||typeof e[k as keyof RadarEvent]==='string'))return false;
 if(!Array.isArray(e.disciplines)||!e.disciplines.every(d=>typeof d==='string')||!Array.isArray(e.labs)||!e.labs.every(v=>typeof v==='string')||!Array.isArray(e.companies)||!e.companies.every(v=>typeof v==='string'))return false;
 if(!e.score||!Number.isFinite(e.score.total)||e.score.total<0||e.score.total>100||!Array.isArray(e.score.reasons)||!e.score.reasons.every(r=>typeof r==='string')||!e.score.parts||typeof e.score.parts!=='object'||!Object.values(e.score.parts).every(v=>typeof v==='number'&&Number.isFinite(v)))return false;
 if(e.warnings!==undefined&&(!Array.isArray(e.warnings)||!e.warnings.every(w=>typeof w==='string')))return false;
 if(!Array.isArray(e.sources)||!e.sources.every(s=>s&&typeof s.id==='string'&&typeof s.name==='string'&&(!!safeUrl(s.url)||(e.privacy==='private'&&!s.url))&&typeof s.checkedAt==='string'))return false;
 if(!Array.isArray(e.speakers)||!e.speakers.every(s=>s&&typeof s.name==='string'))return false;
 return Array.isArray(e.history)&&e.history.every(h=>h&&typeof h.at==='string'&&h.changes&&typeof h.changes==='object'&&Object.values(h.changes).every(v=>v&&typeof v==='object'&&'before' in v&&'after' in v));
}

export function mergeLocalEvents(previous:RadarEvent[],incoming:RadarEvent[]):RadarEvent[]{
 const events=new Map(previous.map(e=>[e.id,e]));
 for(const e of incoming){const old=events.get(e.id);const changes:Record<string,{before:unknown;after:unknown}>={};if(old)for(const key of ['start','end','location','price','status'] as const)if(old[key]!==e[key])changes[key]={before:old[key],after:e[key]};events.set(e.id,old?{...e,firstSeen:old.firstSeen,history:[...old.history,...(Object.keys(changes).length?[{at:new Date().toISOString(),changes}]:[])]}:e);}
 return [...events.values()];
}
