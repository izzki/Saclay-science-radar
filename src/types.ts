export interface Provenance { id: string; name: string; url: string; listingUrl: string; checkedAt: string }
export interface RadarEvent {
 id:string; title:string; description:string; start:string; end:string|null; timezone:string; organizer:string;
 location:string|null; address:string|null; city:string|null; format:string; category:string; disciplines:string[];
 price:number|null; currency:string|null; studentPrice:number|null; priceLabel:string; access:string|null; registration:string|null;
 registrationUrl:string|null; deadline:string|null; speakers:{name:string;institution?:string|null}[]; companies:string[]; labs:string[];level:string|null;
 url:string;status:string;reliability:string;sources:Provenance[];firstSeen:string;lastVerified:string;
 history:{at:string;changes:Record<string,{before:unknown;after:unknown}>}[]; score:{total:number;parts:Record<string,number>;reasons:string[]}; local?:boolean;
}
export interface Source { id:string;name:string;url:string;group:string;connector:string;enabled:boolean;priority:boolean;status:string;note?:string;lastSuccess?:string;lastCheck?:string;lastCheckError?:string;lastAttempt?:string;lastResult?:string;lastEventCount?:number;verifiedUrl?:string;discoveredAt?:string;discoveredFrom?:string;errors?:{error:string;url?:string}[] }
export interface Run { startedAt?:string;finishedAt?:string;lastSuccessfulCollection?:string;status?:string;scheduled?:boolean;workflowRunUrl?:string|null;newEvents?:number;schedule?:string;discoverySchedule?:string;httpRequests?:number }
export interface Coverage { inventory:number;automated:number;enabled:number;verifiedUrls:number;discovered:number;successfulCollectors:number;attemptedCollectors:number;collectorSuccessRate:number|null;inventoryAutomationRate:number;globalRecall:null;auditedRecall:number|null;events:number;lastSuccessfulCollection?:string;limits:string[];nextPriorities:string[];audits:{id:string;expected:number;detected:number;observedRecall:number;reviewedAt:string;window?:string;method?:string;missed?:{title:string;date:string;url:string}[]}[] }
export interface Filters { search:string;period:string;from:string;to:string;city:string;zone:string;price:string;discipline:string;organizer:string;category:string;score:string;reliability:string;format:string;access:string;archives:boolean }
