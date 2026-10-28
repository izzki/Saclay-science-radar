"""Parcours des pages d'agenda : les éditions lointaines avant les fiches détaillées."""
import re
from urllib.parse import urlsplit,parse_qs

def page_number(url):
    p=urlsplit(url);values=parse_qs(p.query).get('page',[])
    if values and re.fullmatch(r'\d+',values[0]):return int(values[0])+1
    match=re.search(r'/page/(\d+)/?',p.path)
    return int(match[1]) if match else None

def is_listing_page(url,base):
    a,b=urlsplit(url),urlsplit(base)
    return a.netloc==b.netloc and page_number(url) is not None and (a.path==b.path or re.sub(r'/page/\d+/?$','',a.path).rstrip('/')==b.path.rstrip('/'))

def collection_queue(links,pending,base):
    pages=[u for u in links if is_listing_page(u,base)]
    pages.sort(key=lambda u:page_number(u) or 0,reverse=True)
    # Resume unfinished listing pages first; then jump to the furthest visible page.
    return list(dict.fromkeys([u for u in pending if is_listing_page(u,base)]+pages+pending+[u for u in links if u not in pages]))
