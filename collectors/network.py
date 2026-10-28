"""HTTP borné, robots.txt, contrôle SSRF et redirections revérifiées."""
import ipaddress
import socket
import time
from urllib.parse import urlsplit, urljoin
from urllib.robotparser import RobotFileParser
import requests
from .model import canonical

AGENT='SaclayScienceRadar/1.0 (+https://github.com/izzki/Saclay-science-radar)'
MAX_BYTES=6_000_000

class Fetcher:
    def __init__(self, budget=350):
        self.session=requests.Session()
        self.session.headers['User-Agent']=AGENT
        self.robots={}; self.last={}; self.cache={}; self.budget=budget; self.requests=0
    def validate(self,url):
        url=canonical(url)
        if not url: raise ValueError('URL HTTP(S) invalide')
        p=urlsplit(url)
        if p.port not in (None,80,443): raise ValueError('Port non autorisé')
        if any(k in p.hostname.lower() for k in ('intranet.','webmail.','vpn.')): raise ValueError('Source privée exclue')
        addresses=socket.getaddrinfo(p.hostname,p.port or (443 if p.scheme=='https' else 80),type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses): raise ValueError('Destination réseau non publique')
        return url
    def _request(self,url):
        for _ in range(6):
            self.validate(url)
            if self.requests>=self.budget: raise RuntimeError('Budget HTTP atteint ; reprise à la prochaine exécution')
            host=urlsplit(url).netloc
            delay=max(1.0,self.robots.get(host,(None,1.0))[1])
            time.sleep(max(0,delay-(time.monotonic()-self.last.get(host,0))))
            self.last[host]=time.monotonic(); self.requests+=1
            r=self.session.get(url,timeout=(8,22),allow_redirects=False,stream=True)
            if r.status_code in (301,302,303,307,308):
                target=urljoin(url,r.headers.get('Location',''));r.close()
                # Never silently carry a robots authorization onto a new origin/path.
                if not target.endswith('/robots.txt'): self.allowed(target)
                url=target;continue
            if r.status_code in (429,503):
                r.close();raise RuntimeError('HTTP '+str(r.status_code)+' : réessai à la prochaine collecte')
            r.raise_for_status()
            chunks=[];size=0
            for chunk in r.iter_content(65536):
                size+=len(chunk)
                if size>MAX_BYTES: r.close();raise ValueError('Document trop volumineux')
                chunks.append(chunk)
            body=b''.join(chunks)
            encoding=r.encoding if r.encoding and r.encoding.lower()!='iso-8859-1' else 'utf-8'
            return body.decode(encoding,errors='replace'),url,r.headers.get('Content-Type','')
        raise RuntimeError('Trop de redirections')
    def allowed(self,url):
        url=self.validate(url);p=urlsplit(url);host=p.netloc
        if host not in self.robots:
            self.robots[host]=(None,1.0)
            rp=RobotFileParser();robots_url=f'{p.scheme}://{host}/robots.txt'
            try:
                text,_,_=self._request(robots_url);rp.parse(text.splitlines())
            except requests.HTTPError as e:
                if e.response.status_code in (404,410): rp.parse([])
                else: raise RuntimeError('robots.txt inaccessible : collecte suspendue') from e
            except Exception as e: raise RuntimeError('robots.txt non vérifié : collecte suspendue') from e
            delay=rp.crawl_delay(AGENT) or rp.crawl_delay('*') or 1
            self.robots[host]=(rp,min(max(delay,1),60))
        rp=self.robots[host][0]
        if rp and not rp.can_fetch(AGENT,url): raise PermissionError('Interdit par robots.txt')
    def get(self,url):
        url=canonical(url)
        if url in self.cache: return self.cache[url]
        self.allowed(url)
        result=self._request(url);self.cache[url]=result
        return result
