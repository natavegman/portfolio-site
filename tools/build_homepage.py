"""Build /ru/ from the existing homepage translation dictionary; no model calls."""
import json,re,subprocess,shutil
from pathlib import Path
from bs4 import BeautifulSoup
site=Path(__file__).resolve().parents[1];source=(site/'index.html').read_text()
match=re.search(r'const T\s*=\s*(\{.*?\n  \});',source,re.S)
assert match
node=shutil.which('node')
assert node, 'Node.js is required to read the existing translation dictionary'
translations=json.loads(subprocess.check_output([node,'-e','process.stdout.write(JSON.stringify('+match[1]+'))'],text=True))
source=source.replace("localStorage.setItem('preferredLang', lang);","try { localStorage.setItem('preferredLang', lang); } catch(e) {}")
source=re.sub(r'  function detectLang\(\) \{.*?\n  \}',"  function detectLang() { return document.documentElement.lang; }",source,flags=re.S)
source=source.replace("btn.addEventListener('click', () => applyLang(btn.dataset.lang));","btn.addEventListener('click', () => { try { localStorage.setItem('preferredLang', btn.dataset.lang); } catch(e) {} });")
source=source.replace('href="Natalia_CV.pdf"','href="/Natalia_CV.pdf"')
source=source.replace('href="theme.css"','href="/theme.css"').replace('src="heroart.js"','src="/heroart.js"')
if '<noscript><style>.reveal' not in source:
 source=source.replace('</head>','<noscript><style>.reveal{opacity:1;transform:none}</style></noscript>\n</head>')
source=re.sub(r'<button class="lang-btn(.*?)"\s+data-lang="(en|ru)">(EN|RU)</button>',lambda m:f'<a class="lang-btn{m[1]}" data-lang="{m[2]}" href="'+('/ru/' if m[2]=='ru' else '/')+f'" hreflang="{m[2]}">{m[3]}</a>',source)
source=source.replace('hreflang="ru" href="https://vegman.dev/"','hreflang="ru" href="https://vegman.dev/ru/"')
# Keep the root English page's formatting and content intact.
source=source.replace('href="/blog/"     data-i18n="navBlog"','href="/en/blog/"     data-i18n="navBlog"')
(site/'index.html').write_text(source)
s=BeautifulSoup(source,'html.parser');s.html['lang']='ru'
for attr,mode in [('data-i18n','text'),('data-i18n-html','html'),('data-i18n-placeholder','placeholder')]:
 for el in s.select('['+attr+']'):
  v=translations['ru'].get(el[attr])
  if v is None:continue
  if mode=='text':el.string=v
  elif mode=='placeholder':el['placeholder']=v
  else:
   el.clear()
   for child in list(BeautifulSoup(v,'html.parser').contents):el.append(child)
for el in s.select('.lang-en-only'):el['style']='display:none'
for el in s.select('.lang-btn'):
 el['class']=['lang-btn']+(['active'] if el['data-lang']=='ru' else [])
s.select_one('[data-i18n="navBlog"]')['href']='/blog/'
title='Ната Вегман — автоматизация бизнеса с ИИ и ИТ-архитектура'
desc='Проектирую ИИ-агентов, интеграции и системы знаний для рабочих процессов бизнеса. Кейсы внедрения, архитектура и инженерные заметки.'
s.title.string=title
for key,value in [('description',desc),('og:title',title),('og:description',desc),('og:url','https://vegman.dev/ru/'),('og:locale','ru_RU'),('og:locale:alternate','en_US'),('twitter:title',title),('twitter:description',desc),('twitter:url','https://vegman.dev/ru/')]:
 s.find('meta',attrs={'property' if key.startswith('og:') else 'name':key})['content']=value
s.select_one('link[rel="canonical"]')['href']='https://vegman.dev/ru/'
j=s.select_one('script[type="application/ld+json"]');data=json.loads(j.string);data.update(name='Ната Вегман',alternateName='Nata Vegman',description=desc);j.string=json.dumps(data,ensure_ascii=False)
(site/'ru').mkdir(exist_ok=True);(site/'ru/index.html').write_text(str(s))
print('Homepage: EN / and static RU /ru/, shared existing translations')
