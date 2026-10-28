import {test,expect} from '@playwright/test';
test('catalogue Android, navigation, filtres et sources',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await expect(page.getByRole('heading',{name:/La science bouge/})).toBeVisible();
 await expect(page.getByRole('button',{name:'◉ Tout voir',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'✧ Pour moi',exact:true}).click();
 await expect(page.getByRole('button',{name:'✧ Pour moi',exact:true})).toHaveAttribute('aria-pressed','true');
 await page.getByLabel('Rechercher un événement').fill('zzzintrouvable');
 await expect(page.getByText(/Aucun événement dans cette sélection|Le catalogue attend sa première collecte/)).toBeVisible();
 await page.getByRole('button',{name:'Tout réinitialiser',exact:true}).click();
 await page.getByRole('navigation').getByRole('button',{name:'Les sources',exact:false}).click();
 await expect(page.getByRole('heading',{name:'Un registre ouvert, des statuts explicites.'})).toBeVisible();
 await page.getByLabel('Rechercher une source').fill('Charles Fabry');
 await expect(page.locator('.source-card').first()).toContainText('Charles Fabry');
 for(const text of await page.locator('.source-card h3').allTextContents())expect(text).toContain('Charles Fabry');
 await page.getByRole('button',{name:'Couverture',exact:false}).click();
 await expect(page.getByText('Exhaustivité globale',{exact:true})).toBeVisible();
 await expect(page.getByText('Inconnue',{exact:true})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
 expect(errors).toEqual([]);
 await page.screenshot({path:'test-results/radar-android.png',fullPage:true});
});
test('favoris persistants, fiche et export calendrier sur données réelles',async({page})=>{
 await page.goto('/');await page.waitForSelector('.result-line');
 const cards=page.locator('.event-card');
 test.skip(await cards.count()===0,'Pas encore de données réelles à venir pour ce contrôle.');
 const first=cards.first();await first.getByRole('button',{name:'Ajouter aux favoris'}).click();
 await first.getByRole('button',{name:'Détails'}).click();
 await expect(page.getByRole('dialog')).toBeVisible();
 const downloaded=page.waitForEvent('download');await page.getByRole('button',{name:'↓ Mon calendrier'}).click();
 expect((await downloaded).suggestedFilename()).toBe('evenement.ics');
 await page.getByRole('button',{name:'Fermer la fiche'}).click();
 await page.reload();await page.getByRole('button',{name:'Mes favoris',exact:false}).click();
 await expect(page.locator('.event-card')).toHaveCount(1);
});

test('ajout local accessible sur Android et conservé après rechargement',async({page})=>{
 await page.goto('/');await page.waitForSelector('.result-line');
 await page.getByRole('button',{name:'Ajouter une annonce',exact:true}).click();
 await page.getByLabel('Lien de l’annonce publique').fill('https://example.org/annonce-de-test');
 await page.getByLabel('Titre',{exact:true}).fill('Annonce synthétique réservée au test navigateur');
 await page.getByLabel('Date',{exact:true}).fill('2026-12-10');
 await page.getByLabel('Organisateur',{exact:true}).fill('Organisateur de test');
 await page.getByRole('button',{name:'Enregistrer sur cet appareil'}).click();
 await expect(page.getByRole('dialog')).toBeVisible();
 await page.getByRole('button',{name:'Fermer la fiche'}).click();
 await page.reload();await page.getByRole('button',{name:'Ajouter une annonce',exact:true}).click();
 await expect(page.locator('.local-row')).toContainText('Annonce synthétique réservée au test navigateur');
 await page.getByRole('button',{name:'Supprimer cet ajout local'}).click();
 await expect(page.locator('.local-row')).toHaveCount(0);
});

test('thèmes, mots-clés, tri et archives sont visibles et fonctionnels',async({page})=>{
 const response=await page.request.get('/data/events.json');const original=(await response.json())[0];
 const make=(id:string,title:string,start:string,end:string|null,discipline:string)=>({...original,id,title,start,end,disciplines:[discipline],speakers:[],description:title,registrationUrl:'https://example.org/register',organizer:'Source de test'});
 const fixtures=[make('ended','Fête de la science terminée','2026-10-04T14:00:00+02:00','2026-10-04T17:30:00+02:00','Physique'),make('future','Laser et photons uniques','2026-11-03T11:00:00+01:00',null,'Photonique'),make('ongoing','Programme de mathématiques en cours','2026-10-20','2026-11-20','Mathématiques')];
 await page.clock.install({time:new Date('2026-10-28T17:00:00Z')});
 await page.route('**/data/events.json',route=>route.fulfill({json:fixtures}));
 await page.addInitScript(()=>localStorage.setItem('ssr-filters',JSON.stringify({archives:true,timeScope:'all'})));
 await page.goto('/');await expect(page.getByLabel('Thème scientifique')).toBeVisible();await expect(page.getByLabel('Trier par')).toBeVisible();
 await expect(page.locator('.event-card')).toHaveCount(2);await expect(page.getByText('Fête de la science terminée',{exact:true})).toHaveCount(0);
 await expect(page.locator('.phase-ongoing')).toHaveCount(1);
 await page.getByLabel('Trier par').selectOption('date-desc');await expect(page.locator('.event-card').first()).toContainText('Laser et photons uniques');
 await page.getByLabel('Thème scientifique').selectOption('Photonique');await page.getByLabel('Rechercher un événement').fill('laser, photons');await expect(page.locator('.event-card')).toHaveCount(1);
 await page.getByRole('button',{name:'Tout réinitialiser',exact:true}).click();
 await page.getByLabel('Période du catalogue').selectOption('past');await expect(page.locator('.event-card')).toHaveCount(1);await expect(page.locator('.phase-ended')).toHaveText('Terminé');
 await page.getByRole('button',{name:'Détails'}).click();await expect(page.getByRole('dialog')).toContainText('Terminé');await expect(page.getByRole('link',{name:'S’inscrire ↗'})).toHaveCount(0);
});

test('import ICS privé récurrent, local et conservé après rechargement',async({page})=>{
 const posts:string[]=[];page.on('request',r=>{if(r.method()==='POST')posts.push(r.url());});
 await page.clock.install({time:new Date('2026-10-28T17:00:00Z')});await page.goto('/');await page.waitForSelector('.result-line');
 await page.getByRole('button',{name:'Ajouter une annonce',exact:true}).click();
 const ics='BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:private-test\r\nDTSTART;TZID=Europe/Paris:20261102T130000\r\nRRULE:FREQ=WEEKLY;COUNT=2\r\nSUMMARY:Invitation privée test\r\nEND:VEVENT\r\nEND:VCALENDAR';
 await page.getByLabel('Importer un calendrier ICS privé').setInputFiles({name:'invitation.ics',mimeType:'text/calendar',buffer:Buffer.from(ics)});
 await expect(page.locator('.local-row')).toHaveCount(2);expect(posts).toEqual([]);
 await page.reload();await page.getByRole('button',{name:'Ajouter une annonce',exact:true}).click();await expect(page.locator('.local-row')).toHaveCount(2);
 const stored=await page.evaluate(()=>JSON.parse(localStorage.getItem('ssr-local')||'[]'));expect(stored.every((e:{privacy:string;url:string})=>e.privacy==='private'&&e.url==='')).toBeTruthy();
});

test('analyse de lien public et garde contre les liens privés signés',async({page})=>{
 await page.goto('/');await page.waitForSelector('.result-line');await page.getByRole('button',{name:'Ajouter une annonce',exact:true}).click();
 await page.getByLabel('Lien public à analyser').fill('https://example.org/event?token=secret');await page.getByRole('button',{name:'Analyser ce lien',exact:true}).click();await expect(page.getByRole('alert')).toContainText('sans jeton');await expect(page.getByRole('link',{name:'Autoriser l’extraction sur GitHub ↗'})).toHaveCount(0);
 await page.getByLabel('Lien public à analyser').fill('https://example.org/new-public-event');await page.getByRole('button',{name:'Analyser ce lien',exact:true}).click();await expect(page.getByRole('link',{name:'Autoriser l’extraction sur GitHub ↗'})).toHaveAttribute('href',/SACLAY_RADAR_PUBLIC_IMPORT_V1/);
});
