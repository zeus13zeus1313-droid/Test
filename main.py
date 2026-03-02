import os
import json
import time
import threading
import requests
import re
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin


# ==========================================
# إعدادات التطبيق
# ==========================================
app = Flask(__name__)
CORS(app)

API_SECRET = os.getenv('API_SECRET', 'Zeusndndjddnejdjdjdejekk29393838msmskxcm9239484jdndjdnddjj99292938338zeuslojdnejxxmejj82283849')  # ⚠️ غيّره في ENV
NODE_BACKEND_URL = os.getenv('NODE_BACKEND_URL', 'https://c-production-fba8.up.railway.app')
MARKAZ_COOKIES = os.getenv('MARKAZ_COOKIES', 'wordpress_sec_198f6e9e82ba200a53325105f201ddc5=mikey%7C1771590380%7CKJphcZkhBFCpXyLUDrDcGPi9XmNOC47IPCSEHAPyfXS%7C5e8e596c5389b65f91a30668be6f16c7134b98b3ae55a007ed360594dd035527; cf_clearance=qYXkJIaj1IiaBKgi561_IQ.9oWgJ3fx10itfVR20lXY-1765278736-1.2.1.1-soYoRwUhDSq_.2cCoaJ22MPadmCmaQ0cW3AkfA1L97BJIbxQQro5hvpmuJxhQaT57TxfEW10l9gQYsmy5QgrwLsiWHScUWVvqYzZufRRYs9LIDPAhyxiOnL2Byevi12fb8iAZWttVNlqYWeKjH06tTp8bNhPx4dsmudPpIh0qzijEZhRk8lK6nWip1SeDFO2Of35W2rBKDEtjidGFyIj1RU3B7Xt.4CVoQbE9pGFaS8gFTMOp.0qmMMiz1UmHoFc; wpmanga-body-contrast=light; wpmanga-reading-history=W3siaWQiOjEyODE3LCJjIjoiMzEzMDgiLCJwIjoxLCJpIjoiIiwidCI6MTc2ODEwMTY3MH1d; sbjs_migrations=1418474375998%3D1; sbjs_current_add=fd%3D2026-02-06%2012%3A25%3A57%7C%7C%7Cep%3Dhttps%3A%2F%2Fmarkazriwayat.com%2F%7C%7C%7Crf%3Dhttps%3A%2F%2Fwww.bing.com%2F; sbjs_first_add=fd%3D2026-02-06%2012%3A25%3A57%7C%7C%7Cep%3Dhttps%3A%2F%2Fmarkazriwayat.com%2F%7C%7C%7Crf%3Dhttps%3A%2F%2Fwww.bing.com%2F; sbjs_current=typ%3Dreferral%7C%7C%7Csrc%3Dbing.com%7C%7C%7Cmdm%3Dreferral%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%2F%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29; sbjs_first=typ%3Dreferral%7C%7C%7Csrc%3Dbing.com%7C%7C%7Cmdm%3Dreferral%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%2F%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29; sbjs_udata=vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%206.2%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F109.0.0.0%20Safari%2F537.36%20Edg%2F109.0.1518.140; wordpress_test_cookie=WP%20Cookie%20check; _lscache_vary=8d8d3777c370b0211addc5b0a9411cd9; wordpress_logged_in_198f6e9e82ba200a53325105f201ddc5=mikey%7C1771590380%7CKJphcZkhBFCpXyLUDrDcGPi9XmNOC47IPCSEHAPyfXS%7Cb7d906dce3f0b160d5c2f585bfec331fe7d0cc3e4640a74945cc619df837e5c9; sbjs_session=pgs%3D2%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fmarkazriwayat.com%2F%3Fnsl_bypass_cache%3D74d71305203b9ce18787813c87e33f8c')

# ==========================================
# Scheduler config
# ==========================================
SCHEDULER_CONFIG = {
    'active': False,
    'interval_seconds': 86400,
    'next_run': 0,
    'last_run': None,
    'status': 'idle',
    'admin_email': 'system@auto'
}


# ==========================================
# Helpers
# ==========================================
def get_headers(use_cookies=False, referer=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    if referer:
        headers['Referer'] = referer
    
    if use_cookies and MARKAZ_COOKIES and MARKAZ_COOKIES != 'ضع_هنا_الكوكيز_الخاصة_بك_كاملة':
        headers['Cookie'] = MARKAZ_COOKIES
        
    return headers

def fix_image_url(url, base_url='https://api.rewayat.club'):
    if not url: return ""
    if url.startswith('//'):
        return 'https:' + url
    elif url.startswith('/'):
        # Fix for absolute paths without domain
        if 'novelfire.net' in base_url:
            return 'https://novelfire.net' + url
        elif 'wuxiabox.com' in base_url or 'wuxiaspot.com' in base_url:
             parsed = urlparse(base_url)
             domain = f"{parsed.scheme}://{parsed.netloc}"
             return domain + url
        return base_url + url
    elif not url.startswith('http'):
        return base_url + '/' + url
    return url

def parse_relative_date(date_str):
    """تحويل التواريخ النسبية (منذ 5 ساعات، يومين ago) إلى تاريخ حقيقي"""
    try:
        if not date_str: return None
        
        now = datetime.now()
        text = str(date_str).lower().strip()
        
        # معالجة النصوص العربية الخاصة (يومين، ساعتين، إلخ)
        if 'يومين' in text:
            return (now - timedelta(days=2)).isoformat()
        if 'ساعتين' in text:
            return (now - timedelta(hours=2)).isoformat()
        if 'دقيقتين' in text:
            return (now - timedelta(minutes=2)).isoformat()
        if 'أمس' in text or 'امس' in text:
            return (now - timedelta(days=1)).isoformat()
        
        # إزالة كلمات زائدة
        text = text.replace('updated', '').replace('ago', '').replace('منذ', '').strip()
        
        # استخراج الرقم والوحدة (عربي وإنجليزي)
        # Match number followed by optional whitespace and unit
        match = re.search(r'(\d+)\s*(sec|min|hour|day|week|month|year|ثانية|ثواني|دقيقة|دقائق|ساعة|ساعات|يوم|أيام|ايام|أسبوع|اسبوع|أسابيع|اسابيع|شهر|أشهر|اشهر|سنة|سنوات)', text)
        
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            
            if unit in ['sec', 'ثانية', 'ثواني']:
                return (now - timedelta(seconds=amount)).isoformat()
            elif unit in ['min', 'دقيقة', 'دقائق']:
                return (now - timedelta(minutes=amount)).isoformat()
            elif unit in ['hour', 'ساعة', 'ساعات']:
                return (now - timedelta(hours=amount)).isoformat()
            elif unit in ['day', 'يوم', 'أيام', 'ايام']:
                return (now - timedelta(days=amount)).isoformat()
            elif unit in ['week', 'أسبوع', 'اسبوع', 'أسابيع', 'اسابيع']:
                return (now - timedelta(weeks=amount)).isoformat()
            elif unit in ['month', 'شهر', 'أشهر', 'اشهر']:
                return (now - timedelta(days=amount * 30)).isoformat()
            elif unit in ['year', 'سنة', 'سنوات']:
                return (now - timedelta(days=amount * 365)).isoformat()
        
        return None
    except Exception:
        return None

def normalize_chapter_title(title):
    if not title: return ""
    # Remove multiple spaces, weird separators
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def clean_text_keep_lines(text):
    if not text: return ""
    # Remove extra empty lines and trim
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines).strip()

# ==========================================
# Backend integration
# ==========================================
def send_data_to_backend(payload):
    try:
        url = f"{NODE_BACKEND_URL}/api/scraper/receive"
        response = requests.post(url, json=payload, timeout=30)
        print(f"Backend Response: {response.status_code} {response.text[:150]}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending to backend: {e}")
        return False

def check_existing_chapters(title):
    """Ask backend which chapter numbers exist for this title"""
    try:
        url = f"{NODE_BACKEND_URL}/api/scraper/check-chapters"
        response = requests.post(url, json={'title': title}, timeout=20)
        if response.status_code != 200:
            return set()
        data = response.json()
        chapters = data.get('chapters', [])
        return set(int(x) for x in chapters if str(x).isdigit())
    except Exception:
        return set()


# ==========================================
# 🟣 1. Rewayat Club (Nuxt/Vue)
# ==========================================
def fetch_metadata_rewayat(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None

        soup = BeautifulSoup(response.content, 'html.parser')

        # Title
        title_el = soup.find('h1')
        title = title_el.get_text(strip=True) if title_el else ''

        # Find description
        desc_el = soup.select_one(".text-pre-line") or soup.select_one(".v-card__text")
        description = desc_el.get_text("\n", strip=True) if desc_el else ''

        # Find status (chips)
        status = ""
        for chip in soup.select(".v-chip"):
            txt = chip.get_text(strip=True).lower()
            if 'مكتملة' in txt or 'completed' in txt:
                status = "Completed"
                break
            if 'مستمرة' in txt or 'ongoing' in txt:
                status = "Ongoing"

        # Find cover from __NUXT__ script
        cover = ""
        scripts = soup.find_all('script')
        for sc in scripts:
            if sc.string and 'window.__NUXT__' in sc.string:
                m = re.search(r'poster_url":"(.*?)"', sc.string)
                if m:
                    cover = m.group(1).replace('\\u002F', '/')
                    break
        cover = fix_image_url(cover, 'https://api.rewayat.club')

        # Find updatedAt (try YYYY/MM/DD)
        updated_at = None
        for el in soup.select(".v-list-item__subtitle"):
            txt = el.get_text(" ", strip=True)
            m = re.search(r'(\d{4})/(\d{2})/(\d{2})', txt)
            if m:
                updated_at = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
                break

        return {
            'title': title,
            'cover': cover,
            'description': description,
            'status': status,
            'tags': [],
            'updatedAt': updated_at
        }
    except Exception as e:
        print(f"Rewayat metadata error: {e}")
        return None

def scrape_chapter_rewayat(novel_url, chapter_number):
    """Probe chapters by /{chapter_number}"""
    try:
        url = novel_url.rstrip('/') + f"/{chapter_number}"
        response = requests.get(url, headers=get_headers(referer=novel_url), timeout=15)
        if response.status_code != 200:
            return "", None

        soup = BeautifulSoup(response.content, 'html.parser')

        # Title
        h = soup.find('h1')
        chap_title = h.get_text(strip=True) if h else f"Chapter {chapter_number}"

        # content
        content_el = soup.select_one(".chapter-content") or soup.select_one(".v-card__text")
        if not content_el:
            # fallback: find largest text block
            paras = soup.find_all('p')
            if paras:
                content = "\n".join(p.get_text(strip=True) for p in paras)
            else:
                content = soup.get_text("\n", strip=True)
        else:
            for x in content_el.find_all(['script', 'style']):
                x.decompose()
            content = content_el.get_text("\n", strip=True)

        content = clean_text_keep_lines(content)
        if not content or len(content) < 50:
            return chap_title, None

        return chap_title, content
    except Exception:
        return "", None


def worker_rewayat_probe(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0
    
    # Send initial meta update
    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})

    current_chapter = 1
    errors = 0
    batch = []
    
    while current_chapter < 5000 and errors < 15:
        if current_chapter in existing_chapters:
            current_chapter += 1
            errors = 0
            continue
            
        chap_title, content = scrape_chapter_rewayat(url, current_chapter)
        if content:
            errors = 0
            batch.append({'number': current_chapter, 'title': chap_title, 'content': content})
            print(f"Fetched Ch {current_chapter}")
            if len(batch) >= 5:
                send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
                batch = []
                time.sleep(1)
        else:
            errors += 1
            print(f"Failed Ch {current_chapter} ({errors}/15)")
        current_chapter += 1
        
    if batch:
        send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})

# ==========================================
# 🟢 2. Madara Themes (Ar-Novel & Markaz Riwayat - Updated for NEW DESIGN)
# ==========================================

def get_base_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def clean_madara_title(raw_title):
    cleaned = re.sub(r'^\s*(?:Chapter|الفصل|فصل)?\s*\d+\s*[:\-–]\s*', '', raw_title, flags=re.IGNORECASE).strip()
    return cleaned if cleaned else raw_title 

def fetch_metadata_madara(url):
    try:
        use_cookies = 'markazriwayat.com' in url
        response = requests.get(url, headers=get_headers(use_cookies=use_cookies), timeout=15)
        
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        base_url = get_base_url(url)
        
        # NEW DESIGN: Title
        title_el = soup.select_one('.manga-title') or soup.select_one('h1') or soup.find('meta', property='og:title')
        if hasattr(title_el, 'get_text'):
            title = title_el.get_text(strip=True)
        else:
            title = title_el['content'] if title_el else ''
        
        # NEW DESIGN: Cover
        cover_el = soup.select_one('.summary_image img') or soup.select_one('.summary_image a img') or soup.select_one('meta[property="og:image"]')
        cover = ""
        if cover_el:
            if hasattr(cover_el, 'get'):
                cover = cover_el.get('data-src') or cover_el.get('src') or cover_el.get('content') or ""
            else:
                cover = cover_el['content']
        cover = fix_image_url(cover, base_url)
        
        # NEW DESIGN: Description
        desc_el = soup.select_one('.description-summary') or soup.select_one('.summary__content') or soup.select_one('.summary__content p')
        description = desc_el.get_text("\n", strip=True) if desc_el else ""
        
        # Status
        status = ""
        status_el = soup.select_one('.post-status .summary-content') or soup.select_one('.summary-content')
        if status_el:
            status_text = status_el.get_text(" ", strip=True).lower()
            if 'ongoing' in status_text or 'مستمرة' in status_text:
                status = "Ongoing"
            elif 'completed' in status_text or 'مكتملة' in status_text:
                status = "Completed"
        
        # Tags / Genres
        tags = []
        for a in soup.select('.genres-content a, .tags-content a, .post-content_item .summary-content a'):
            t = a.get_text(strip=True)
            if t and t not in tags:
                tags.append(t)
        
        return {
            'title': title,
            'cover': cover,
            'description': description,
            'status': status,
            'tags': tags,
            'updatedAt': None
        }
    except Exception as e:
        print(f"Madara metadata error: {e}")
        return None

def fetch_metadata_markaz(url):
    # Same as madara but with cookies enabled
    return fetch_metadata_madara(url)

def try_fetch_chapters_via_ajax(novel_url, base_url, use_cookies=False):
    """Try multiple methods for Madara chapter list"""
    # 1) /ajax/chapters/
    try:
        ajax_url = novel_url.rstrip('/') + "/ajax/chapters/"
        r = requests.post(ajax_url, headers=get_headers(use_cookies=use_cookies, referer=novel_url), timeout=15)
        if r.status_code == 200 and len(r.text) > 50:
            soup = BeautifulSoup(r.content, 'html.parser')
            return soup
    except:
        pass
    
    # 2) admin-ajax
    try:
        admin_ajax = base_url.rstrip('/') + "/wp-admin/admin-ajax.php"
        payload = {
            'action': 'manga_get_chapters',
            'manga': novel_url
        }
        r = requests.post(admin_ajax, data=payload, headers=get_headers(use_cookies=use_cookies, referer=novel_url), timeout=15)
        if r.status_code == 200 and len(r.text) > 50:
            soup = BeautifulSoup(r.content, 'html.parser')
            return soup
    except:
        pass
    
    # 3) Fallback fetch full page and parse
    try:
        r = requests.get(novel_url, headers=get_headers(use_cookies=use_cookies), timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            return soup
    except:
        pass
    
    return None

def fetch_chapter_list_madara(url):
    """Return list of chapters with number/title/url for both old and new design."""
    chapters = []
    try:
        base_url = get_base_url(url)
        use_cookies = 'markazriwayat.com' in url
        soup = try_fetch_chapters_via_ajax(url, base_url, use_cookies=use_cookies)
        if not soup:
            return []

        # New design: .ch-list .ch-row
        ch_rows = soup.select('.ch-list .ch-row') or soup.select('.main .ch-row')
        if ch_rows:
            for row in ch_rows:
                a = row.select_one('a')
                if not a: 
                    continue
                href = a.get('href', '')
                raw_title = a.get_text(" ", strip=True)
                # Try to find "Chapter X"
                m = re.search(r'Chapter\s*(\d+)', raw_title, re.IGNORECASE)
                num = None
                if m:
                    num = int(m.group(1))
                else:
                    m2 = re.search(r'(\d+)', raw_title)
                    if m2:
                        num = int(m2.group(1))
                if num is None:
                    continue
                title = clean_madara_title(raw_title)
                chapters.append({'number': num, 'title': title, 'url': href})
        else:
            # Old design: li.wp-manga-chapter
            for li in soup.select('li.wp-manga-chapter'):
                a = li.find('a')
                if not a:
                    continue
                href = a.get('href', '')
                raw_title = a.get_text(" ", strip=True)
                m = re.search(r'Chapter\s*(\d+)', raw_title, re.IGNORECASE)
                num = None
                if m:
                    num = int(m.group(1))
                else:
                    m2 = re.search(r'(\d+)', raw_title)
                    if m2:
                        num = int(m2.group(1))
                if num is None:
                    continue
                title = clean_madara_title(raw_title)
                chapters.append({'number': num, 'title': title, 'url': href})

        # Normalize URLs and sort by number
        for c in chapters:
            c['url'] = urljoin(base_url, c['url'])
            c['title'] = normalize_chapter_title(c['title'])
        
        # Remove duplicates by number
        unique = {}
        for c in chapters:
            unique[c['number']] = c
        
        chapters = list(unique.values())
        chapters.sort(key=lambda x: x['number'])
        return chapters

    except Exception as e:
        print(f"Madara chapter list error: {e}")
        return []

def scrape_chapter_madara(chapter_url, use_cookies=False):
    try:
        response = requests.get(chapter_url, headers=get_headers(use_cookies=use_cookies, referer=chapter_url), timeout=15)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        # Common content containers
        content_el = (
            soup.select_one('.reader-target') or
            soup.select_one('.reading-content') or
            soup.select_one('.entry-content') or
            soup.select_one('.text-left') or
            soup.select_one('#chapter-content') or
            soup.select_one('div.chapter-content') or
            soup.select_one('article') 
        )

        if not content_el:
            return None
        
        # Remove unwanted nodes
        for x in content_el.find_all(['script', 'style', 'noscript']):
            x.decompose()
        for x in content_el.select('.ads, .advertisement, .code-block, .wp-block, .navigation, .navi'):
            x.decompose()

        content = content_el.get_text("\n", strip=True)
        content = clean_text_keep_lines(content)
        return content if content and len(content) > 50 else None
    except Exception:
        return None


def worker_madara_list(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0
    
    # Send initial meta update
    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})

    all_chapters = fetch_chapter_list_madara(url)
    use_cookies = 'markazriwayat.com' in url
    
    batch = []
    for chap in all_chapters:
        if chap['number'] in existing_chapters:
            continue
        print(f"Scraping Madara: Ch {chap['number']}...")
        content = scrape_chapter_madara(chap['url'], use_cookies=use_cookies)
        
        if content:
            batch.append({'number': chap['number'], 'title': chap['title'], 'content': content})
            if len(batch) >= 5:
                send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
                batch = []
                time.sleep(1)
                
    if batch:
        send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})

# ==========================================
# 🔵 3. NovelFire
# ==========================================
def fetch_metadata_novelfire(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Title
        title_el = soup.select_one('h1.novel-title') or soup.find('h1')
        title = title_el.get_text(strip=True) if title_el else ""

        # Cover
        cover = ""
        img = soup.select_one('figure.cover img') or soup.select_one('meta[property="og:image"]')
        if img:
            cover = img.get('src') or img.get('content') or ""
        cover = fix_image_url(cover, base_url='novelfire.net')

        # Description
        desc_el = soup.select_one('meta[itemprop="description"]') or soup.find('meta', attrs={'name': 'description'})
        description = ""
        if desc_el:
            description = desc_el.get('content', '').strip()

        # Status
        status = ""
        st = soup.select_one('.header-stats strong.ongoing') or soup.select_one('.header-stats strong.completed')
        if st:
            status = st.get_text(strip=True)

        # Categories
        tags = []
        for a in soup.select('.categories a.property-item'):
            t = a.get_text(strip=True)
            if t:
                tags.append(t)

        # Updated date
        updated_el = soup.select_one('.chapter-latest-container .update')
        updatedAt = parse_relative_date(updated_el.get_text(strip=True)) if updated_el else None
        
        return {
            'title': title,
            'cover': cover,
            'description': description,
            'status': status,
            'tags': tags,
            'updatedAt': updatedAt
        }
    except Exception as e:
        print(f"NovelFire metadata error: {e}")
        return None

def fetch_chapter_list_novelfire(url):
    chapters = []
    try:
        base_url = get_base_url(url)
        page = 1
        seen = set()

        while True:
            list_url = url.rstrip('/') + f"/chapters?page={page}"
            r = requests.get(list_url, headers=get_headers(referer=url), timeout=15)
            if r.status_code != 200:
                break
            soup = BeautifulSoup(r.content, 'html.parser')
            ch_links = soup.select('ul.chapter-list li a')
            if not ch_links:
                break

            for a in ch_links:
                href = a.get('href', '')
                # Example: /book/title/chapter-1
                m = re.search(r'chapter-(\d+)', href, re.IGNORECASE)
                if not m:
                    continue
                num = int(m.group(1))
                if num in seen:
                    continue
                seen.add(num)

                title = a.get_text(" ", strip=True)
                title = normalize_chapter_title(title)
                chapters.append({
                    'number': num,
                    'title': title,
                    'url': urljoin(base_url, href)
                })

            next_link = soup.select_one('a[rel="next"]')
            if not next_link:
                break
            page += 1
            time.sleep(0.3)

        chapters.sort(key=lambda x: x['number'])
        return chapters
    except Exception as e:
        print(f"NovelFire chapter list error: {e}")
        return []

def scrape_chapter_novelfire(chapter_url):
    try:
        r = requests.get(chapter_url, headers=get_headers(referer=chapter_url), timeout=15)
        if r.status_code != 200: 
            return None
        soup = BeautifulSoup(r.content, 'html.parser')

        content_el = soup.select_one('.chapter-content') or soup.select_one('#chapter-content') or soup.find('article')
        if not content_el:
            return None
        for x in content_el.find_all(['script', 'style', 'noscript']):
            x.decompose()
        text = content_el.get_text("\n", strip=True)
        text = clean_text_keep_lines(text)
        return text if text and len(text) > 50 else None
    except Exception:
        return None

def worker_novelfire_list(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0
    
    # Send initial meta update
    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})

    all_chapters = fetch_chapter_list_novelfire(url)
    
    batch = []
    for chap in all_chapters:
        if chap['number'] in existing_chapters:
            continue
        
        print(f"Scraping NovelFire: Ch {chap['number']}...")
        content = scrape_chapter_novelfire(chap['url'])
        
        if content:
            batch.append({'number': chap['number'], 'title': chap['title'], 'content': content})
            if len(batch) >= 5:
                send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
                batch = []
                time.sleep(1)
                
    if batch:
        send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})


# ==========================================
# 🟠 4. WuxiaBox / WuxiaSpot
# ==========================================
def fetch_metadata_wuxiabox(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        base_url = get_base_url(url)

        title_el = soup.select_one('h1.novel-title') or soup.find('h1')
        title = title_el.get_text(strip=True) if title_el else ""

        cover = ""
        img = soup.select_one('figure.cover img') or soup.select_one('meta[property="og:image"]')
        if img:
            cover = img.get('src') or img.get('data-src') or img.get('content') or ""
        cover = fix_image_url(cover, base_url)

        desc = ""
        desc_el = soup.select_one('.summary .content') or soup.find('meta', attrs={'name': 'description'})
        if desc_el:
            if hasattr(desc_el, 'get_text'):
                desc = desc_el.get_text("\n", strip=True)
            else:
                desc = desc_el.get('content', '').strip()

        status = ""
        st = soup.select_one('.header-stats strong.completed') or soup.select_one('.header-stats strong.ongoing')
        if st:
            status = st.get_text(strip=True)

        tags = []
        for a in soup.select('.tags a.tag'):
            t = a.get_text(strip=True)
            if t:
                tags.append(t)

        return {
            'title': title,
            'cover': cover,
            'description': desc,
            'status': status,
            'tags': tags,
            'updatedAt': None
        }
    except Exception as e:
        print(f"WuxiaBox metadata error: {e}")
        return None

def fetch_chapter_list_wuxiabox(url):
    chapters = []
    try:
        base_url = get_base_url(url)
        page_url = url
        seen = set()

        while True:
            r = requests.get(page_url, headers=get_headers(referer=url), timeout=15)
            if r.status_code != 200:
                break
            soup = BeautifulSoup(r.content, 'html.parser')

            for a in soup.select('ul.chapter-list li a'):
                href = a.get('href', '')
                m = re.search(r'chapter-(\d+)', href, re.IGNORECASE)
                if not m:
                    # some sites might use /123
                    m2 = re.search(r'(\d+)$', href.strip('/'))
                    if m2:
                        num = int(m2.group(1))
                    else:
                        continue
                else:
                    num = int(m.group(1))
                
                if num in seen:
                    continue
                seen.add(num)

                title = a.get_text(" ", strip=True)
                title = normalize_chapter_title(title)
                chapters.append({'number': num, 'title': title, 'url': urljoin(base_url, href)})

            # Pagination next
            next_a = None
            for a in soup.select('a'):
                if a.get_text(strip=True) in ['Next', '>', '»']:
                    next_a = a
                    break
            if not next_a:
                break

            next_href = next_a.get('href', '')
            if not next_href:
                break
            page_url = urljoin(base_url, next_href)
            time.sleep(0.3)

        chapters.sort(key=lambda x: x['number'])
        return chapters
    except Exception as e:
        print(f"WuxiaBox chapter list error: {e}")
        return []

def scrape_chapter_wuxiabox(chapter_url):
    try:
        r = requests.get(chapter_url, headers=get_headers(referer=chapter_url), timeout=15)
        if r.status_code != 200: 
            return None

        soup = BeautifulSoup(r.content, 'html.parser')

        content_el = soup.select_one('.chapter-content') or soup.select_one('#chapter-content') or soup.find('article')
        if not content_el:
            return None

        for x in content_el.find_all(['script', 'style', 'noscript']):
            x.decompose()
        for x in content_el.find_all(['div']):
            # aggressive cleaning of nested divs
            x.unwrap()

        text = content_el.get_text("\n", strip=True)
        text = clean_text_keep_lines(text)
        return text if text and len(text) > 50 else None
    except Exception:
        return None

def worker_wuxiabox_list(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0
    
    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})

    all_chapters = fetch_chapter_list_wuxiabox(url)
    
    batch = []
    for chap in all_chapters:
        if chap['number'] in existing_chapters: continue
        
        print(f"Scraping WuxiaBox: Ch {chap['number']}...")
        content = scrape_chapter_wuxiabox(chap['url'])
        
        if content:
            batch.append({'number': chap['number'], 'title': chap['title'], 'content': content})
            if len(batch) >= 5:
                send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
                batch = []
                time.sleep(1)
                
    if batch:
        send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})


# ==========================================
# 🟡 5. FreeWebNovel
# ==========================================
def fetch_metadata_freewebnovel(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Title
        title_tag = soup.find("meta", property="og:title")
        title = title_tag["content"] if title_tag else soup.select_one('h1.tit').get_text(strip=True)
        
        # Cover
        cover_tag = soup.find("meta", property="og:image")
        cover = cover_tag["content"] if cover_tag else ""
        
        # Description
        desc_el = soup.select_one('.m-desc .txt') or soup.find("meta", attrs={"name":"description"})
        description = desc_el.get_text("\n", strip=True) if hasattr(desc_el, 'get_text') else (desc_el.get('content','') if desc_el else '')
        
        # Status
        status = ""
        status_el = soup.find(string=re.compile("Completed|Ongoing", re.IGNORECASE))
        if status_el:
            status = str(status_el).strip()
        
        # Tags
        tags = []
        for a in soup.select('.m-info a'):
            t = a.get_text(strip=True)
            if t:
                tags.append(t)
        
        return {
            'title': title.strip(),
            'cover': cover.strip(),
            'description': description.strip(),
            'status': status,
            'tags': tags,
            'updatedAt': None
        }
    except Exception as e:
        print(f"FreeWebNovel metadata error: {e}")
        return None

def fetch_chapter_list_freewebnovel(url):
    chapters = []
    try:
        base_url = get_base_url(url)
        r = requests.get(url, headers=get_headers(referer=url), timeout=15)
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.content, 'html.parser')
        
        for a in soup.select('ul#idData li a'):
            href = a.get('href', '')
            text = a.get_text(" ", strip=True)
            # Try to parse chapter number from text
            m = re.search(r'chapter\s*(\d+)', text, re.IGNORECASE)
            num = None
            if m:
                num = int(m.group(1))
            else:
                m2 = re.search(r'(\d+)', text)
                if m2:
                    num = int(m2.group(1))
            if num is None:
                continue
            title = normalize_chapter_title(text)
            chapters.append({'number': num, 'title': title, 'url': urljoin(base_url, href)})
        
        # De-dup and sort
        unique = {}
        for c in chapters:
            unique[c['number']] = c
        chapters = list(unique.values())
        chapters.sort(key=lambda x: x['number'])
        return chapters
    except Exception as e:
        print(f"FreeWebNovel chapters error: {e}")
        return []

def scrape_chapter_freewebnovel(chapter_url):
    try:
        r = requests.get(chapter_url, headers=get_headers(referer=chapter_url), timeout=15)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.content, 'html.parser')
        
        content_el = soup.select_one('.m-read .txt') or soup.select_one('#chaptercontent') or soup.find('article')
        if not content_el:
            return None
        
        for x in content_el.find_all(['script', 'style', 'noscript']):
            x.decompose()
        for x in content_el.select('.ads, .advertisement, .code-block'):
            x.decompose()
        
        text = content_el.get_text("\n", strip=True)
        text = clean_text_keep_lines(text)
        return text if text and len(text) > 50 else None
    except Exception:
        return None

def worker_freewebnovel_list(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0
    
    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})

    all_chapters = fetch_chapter_list_freewebnovel(url)
    
    batch = []
    for chap in all_chapters:
        if chap['number'] in existing_chapters: continue
        
        print(f"Scraping Freewebnovel: Ch {chap['number']}...")
        content = scrape_chapter_freewebnovel(chap['url'])
        
        if content:
            batch.append({'number': chap['number'], 'title': chap['title'], 'content': content})
            if len(batch) >= 5:
                send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
                batch = []
                time.sleep(1)
                
    if batch:
        send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})


# ==========================================
# 🟤 6. FanMTL (fanmtl.com)
# ==========================================

def fetch_metadata_fanmtl(url):
    try:
        # Ensure we are on a page that contains the info + chapters (FanMTL usually shows both)
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        base_url = get_base_url(url)

        # Title
        title_el = soup.select_one('h1.novel-title') or soup.select_one('h1[itemprop="name"]') or soup.find('h1')
        title = title_el.get_text(strip=True) if title_el else ''
        if not title:
            og = soup.find('meta', property='og:title')
            title = og.get('content', '').strip() if og else ''

        if not title: 
            return None

        # Cover
        cover = ''
        cover_img = soup.select_one('figure.cover img')
        if cover_img:
            cover = cover_img.get('data-src') or cover_img.get('src') or ''
        if not cover:
            ogi = soup.find('meta', property='og:image')
            cover = ogi.get('content', '').strip() if ogi else ''
        cover = fix_image_url(cover, base_url)

        # Description
        desc = ''
        summary_el = soup.select_one('div.summary div.content') or soup.select_one('section#info div.summary div.content')
        if summary_el:
            desc = summary_el.get_text("\n", strip=True)
        if not desc:
            md = soup.find('meta', attrs={'name': 'description'})
            desc = md.get('content', '').strip() if md else ''

        # Status
        status = ''
        # Usually appears like: <strong class="">Ongoing</strong> <small>Status</small>
        status_el = None
        header_stats = soup.select_one('.header-stats')
        if header_stats:
            for st in header_stats.select('strong'):
                txt = st.get_text(strip=True)
                if txt and not re.search(r'\d', txt):
                    status_el = st
                    break
        status = status_el.get_text(strip=True) if status_el else ''

        # Tags
        tags = []
        for a in soup.select('a.tag'):
            t = a.get_text(strip=True)
            if t:
                tags.append(t)
        if not tags:
            # Fallback: categories list can include tag-like entries
            for a in soup.select('.categories a.property-item'):
                t = a.get_text(strip=True)
                if t:
                    tags.append(t)

        # Last updated (from first chapter time if available)
        last_updated = None
        time_el = soup.select_one('ul.chapter-list li time.chapter-update')
        if time_el:
            last_updated = parse_relative_date(time_el.get_text(strip=True))

        return {
            'title': title,
            'cover': cover,
            'description': desc,
            'status': status,
            'tags': tags,
            'updatedAt': last_updated
        }
    except Exception as e:
        print(f"FanMTL metadata error: {e}")
        return None

def _extract_chapters_from_fanmtl_soup(soup, base_url):
    chapters = []
    for a in soup.select('ul.chapter-list li a'):
        href = a.get('href', '').strip()
        if not href: 
            continue

        num = None
        num_el = a.select_one('span.chapter-no')
        if num_el:
            try:
                num = int(re.sub(r'[^0-9]', '', num_el.get_text(strip=True)))
            except:
                num = None

        title = ''
        title_el = a.select_one('strong.chapter-title')
        if title_el:
            title = title_el.get_text(strip=True)

        if num is None:
            # Fallback: try to parse from URL pattern ..._123.html
            m = re.search(r'_(\d+)\.html', href)
            if m:
                num = int(m.group(1))

        if num is None:
            continue

        if not title:
            title = f"Chapter {num}"

        chapters.append({
            'number': num,
            'title': title,
            'url': urljoin(base_url, href)
        })
    return chapters

def fetch_chapter_list_fanmtl(url):
    try:
        base_url = get_base_url(url)

        # Ensure we see the chapters tab if supported
        chapters_url = url
        if 'tab=chapters' not in chapters_url:
            chapters_url = chapters_url + ('&' if '?' in chapters_url else '?') + 'tab=chapters'

        response = requests.get(chapters_url, headers=get_headers(), timeout=15)
        if response.status_code != 200: 
            return []

        soup = BeautifulSoup(response.content, 'html.parser')

        chapter_map = {}
        for c in _extract_chapters_from_fanmtl_soup(soup, base_url):
            chapter_map[c['number']] = c

        # Pagination pages (FanMTL uses /e/extend/fy.php?page=N&wjm=...)
        page_urls = set()
        for a in soup.select('ul.pagination a[href*="fy.php"]'):
            href = a.get('href', '').strip()
            if href:
                page_urls.add(urljoin(base_url, href))

        for page_url in sorted(page_urls):
            try:
                r = requests.get(page_url, headers=get_headers(referer=chapters_url), timeout=15)
                if r.status_code != 200:
                    continue
                psoup = BeautifulSoup(r.content, 'html.parser')
                for c in _extract_chapters_from_fanmtl_soup(psoup, base_url):
                    chapter_map[c['number']] = c
                time.sleep(0.3)
            except:
                continue

        chapters = list(chapter_map.values())
        chapters.sort(key=lambda x: x['number'])
        return chapters
    except Exception as e:
        print(f"FanMTL chapters error: {e}")
        return []

def scrape_chapter_fanmtl(chapter_url):
    try:
        response = requests.get(chapter_url, headers=get_headers(referer=chapter_url), timeout=15)
        if response.status_code != 200: return None

        soup = BeautifulSoup(response.content, 'html.parser')

        # Try common containers
        container = (
            soup.select_one('article#chapter') or
            soup.select_one('article') or
            soup.select_one('#chapter') or
            soup.select_one('.chapter-content') or
            soup.select_one('#chapter-content') or
            soup.select_one('.read-content') or
            soup.select_one('#read-content') or
            soup.select_one('main')
        )

        if not container:
            container = soup

        # Remove noise
        for tag in container.find_all(['script', 'style', 'noscript', 'svg', 'form', 'button']):
            tag.decompose()

        for noisy in container.select('.related, .sidebar-wrapper, header, footer, nav, .navbar-breadcrumb, .alertbox, #toast-container, .ajax_waiting'):
            noisy.decompose()

        text = container.get_text("\n", strip=True)

        # Clean common non-content lines
        # Remove the header lines that repeat site navigation
        text = re.sub(r'^Your Fan-Fiction Stories Hub\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'chevron_left\s*Prev.*?nights_stay\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'chevron_left\s*Prev\s*home\s*Index\s*.*$', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'Tap the screen to use advanced tools.*$', '', text, flags=re.IGNORECASE | re.DOTALL)

        # Normalize extra blank lines
        lines = [ln.strip() for ln in text.splitlines()]
        lines = [ln for ln in lines if ln]
        cleaned = "\n".join(lines).strip()

        return cleaned if cleaned else None
    except Exception as e:
        print(f"FanMTL chapter error: {e}")
        return None

def worker_fanmtl_list(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0
    
    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})

    all_chapters = fetch_chapter_list_fanmtl(url)
    
    batch = []
    for chap in all_chapters:
        if chap['number'] in existing_chapters: 
            continue
        
        print(f"Scraping FanMTL: Ch {chap['number']}...")
        content = scrape_chapter_fanmtl(chap['url'])
        
        if content:
            batch.append({'number': chap['number'], 'title': chap['title'], 'content': content})
            if len(batch) >= 5:
                send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
                batch = []
                time.sleep(1)
                
    if batch:
        send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})


# ==========================================
# ⚪ 7. NovelBin (novelbin.com)
# ==========================================

def fetch_metadata_novelbin(url):
    """
    استخراج البيانات التعريفية للرواية من novelbin.com
    """
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        base_url = get_base_url(url)

        # العنوان
        title_el = soup.select_one('li.active h1 a')
        if not title_el:
            title_el = soup.select_one('h3.title[itemprop="name"]')
        title = title_el.get_text(strip=True) if title_el else ''

        # الغلاف
        cover = ''
        cover_img = soup.select_one('.book img.lazy')
        if cover_img:
            cover = cover_img.get('data-src') or cover_img.get('src') or ''
        if not cover:
            og_img = soup.find('meta', property='og:image')
            if og_img:
                cover = og_img.get('content', '')
        cover = fix_image_url(cover, base_url)

        # الوصف
        desc_el = soup.select_one('.desc-text[itemprop="description"]')
        description = desc_el.get_text("\n", strip=True) if desc_el else ''

        # الحالة
        status = ''
        status_link = soup.select_one('ul.info-meta li a.text-primary')
        if status_link:
            status_text = status_link.get_text(strip=True).lower()
            if 'completed' in status_text:
                status = 'Completed'
            elif 'ongoing' in status_text:
                status = 'Ongoing'
        if not status:
            # محاولة من النص المباشر
            status_li = soup.find('li', string=re.compile(r'Status', re.I))
            if status_li:
                status_a = status_li.find('a')
                if status_a:
                    status = status_a.get_text(strip=True)

        # التصنيفات
        tags = []
        tag_container = soup.select_one('.tag-container')
        if tag_container:
            for a in tag_container.select('a'):
                t = a.get_text(strip=True)
                if t and t not in tags:
                    tags.append(t)

        # آخر تحديث
        updated_at = None
        meta_time = soup.find('meta', property='og:novel:update_time')
        if meta_time and meta_time.get('content'):
            updated_at = meta_time['content']
        else:
            # محاولة من النص النسبي
            time_elem = soup.select_one('.l-chapter .item-time')
            if time_elem:
                updated_at = parse_relative_date(time_elem.get_text(strip=True))

        return {
            'title': title,
            'cover': cover,
            'description': description,
            'status': status,
            'tags': tags,
            'updatedAt': updated_at
        }
    except Exception as e:
        print(f"NovelBin metadata error: {e}")
        return None


def fetch_chapter_list_novelbin(url):
    """
    جلب قائمة الفصول من صفحة الرواية الرئيسية (tab chapters)
    """
    chapters = []
    try:
        base_url = get_base_url(url)
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200:
            return chapters

        soup = BeautifulSoup(response.content, 'html.parser')
        # البحث عن تبويبة الفصول
        chapters_tab = soup.select_one('#tab-chapters')
        if not chapters_tab:
            return chapters

        # الفصول موجودة في عدة أعمدة، كل عمود به ul.list-chapter
        for ul in chapters_tab.select('ul.list-chapter'):
            for li in ul.find_all('li'):
                a = li.find('a')
                if not a:
                    continue
                href = a.get('href', '').strip()
                if not href:
                    continue

                # استخراج رقم الفصل من الرابط (عادة chapter-(\d+))
                num = None
                m = re.search(r'chapter-(\d+)', href, re.IGNORECASE)
                if m:
                    num = int(m.group(1))
                else:
                    # إذا لم نجد في الرابط، نحاول من عنوان الفصل
                    title_text = a.get_text(strip=True)
                    m2 = re.search(r'Chapter\s*(\d+)', title_text, re.IGNORECASE)
                    if m2:
                        num = int(m2.group(1))

                if num is None:
                    continue

                # تنظيف العنوان
                title = normalize_chapter_title(a.get_text(strip=True))

                chapters.append({
                    'number': num,
                    'title': title,
                    'url': urljoin(base_url, href)
                })

        # إزالة التكرار وترتيب
        unique = {}
        for c in chapters:
            if c['number'] not in unique:
                unique[c['number']] = c
        chapters = list(unique.values())
        chapters.sort(key=lambda x: x['number'])
        return chapters

    except Exception as e:
        print(f"NovelBin chapter list error: {e}")
        return chapters


def scrape_chapter_novelbin(chapter_url):
    """
    جلب محتوى فصل معين من novelbin
    """
    try:
        response = requests.get(chapter_url, headers=get_headers(referer=chapter_url), timeout=15)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        content_div = soup.select_one('#chr-content')
        if not content_div:
            return None

        # إزالة العناصر غير المرغوب فيها
        for tag in content_div.find_all(['script', 'style', 'noscript', 'iframe', 'ins']):
            tag.decompose()

        # إزالة الإعلانات التي تأتي في divs خاصة
        for ad in content_div.select('div[id^="pf-"], div[class*="ads"], div[class*="advertisement"]'):
            ad.decompose()

        # الحصول على النص
        text = content_div.get_text("\n", strip=True)

        # تنظيف الأسطر الفارغة المتكررة
        lines = [ln.strip() for ln in text.splitlines()]
        lines = [ln for ln in lines if ln and not ln.startswith(('if', 'function', 'var', 'window.'))]  # إزالة بقايا JS
        cleaned = "\n".join(lines).strip()

        return cleaned if cleaned else None
    except Exception as e:
        print(f"NovelBin chapter scrape error: {e}")
        return None


def worker_novelbin_list(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0

    # إرسال البيانات التعريفية الأولية
    send_data_to_backend({
        'adminEmail': admin_email,
        'novelData': metadata,
        'chapters': [],
        'skipMetadataUpdate': skip_meta
    })

    all_chapters = fetch_chapter_list_novelbin(url)

    batch = []
    for chap in all_chapters:
        if chap['number'] in existing_chapters:
            continue

        print(f"Scraping NovelBin: Ch {chap['number']}...")
        content = scrape_chapter_novelbin(chap['url'])

        if content:
            batch.append({
                'number': chap['number'],
                'title': chap['title'],
                'content': content
            })
            if len(batch) >= 5:
                send_data_to_backend({
                    'adminEmail': admin_email,
                    'novelData': metadata,
                    'chapters': batch,
                    'skipMetadataUpdate': True
                })
                batch = []
                time.sleep(1)

    if batch:
        send_data_to_backend({
            'adminEmail': admin_email,
            'novelData': metadata,
            'chapters': batch,
            'skipMetadataUpdate': True
        })


# ==========================================
# Main Orchestrator
# ==========================================

@app.route('/', methods=['GET'])
def health_check():
    return "ZEUS Scraper Service is Running", 200

@app.route('/scheduler/config', methods=['POST'])
def configure_scheduler():
    auth_header = request.headers.get('Authorization')
    if auth_header != API_SECRET: return jsonify({'message': 'Unauthorized'}), 401
    
    data = request.json
    SCHEDULER_CONFIG['active'] = data.get('active', False)
    SCHEDULER_CONFIG['interval_seconds'] = int(data.get('interval', 86400))
    SCHEDULER_CONFIG['admin_email'] = data.get('adminEmail', 'system@auto')
    
    # If activating, set next run immediately if not set
    if SCHEDULER_CONFIG['active'] and SCHEDULER_CONFIG['next_run'] < time.time():
        SCHEDULER_CONFIG['next_run'] = time.time() + 5 # Run in 5 seconds
        
    return jsonify({
        'message': 'Scheduler Updated',
        'config': SCHEDULER_CONFIG
    })

@app.route('/scheduler/status', methods=['GET'])
def get_scheduler_status():
    return jsonify(SCHEDULER_CONFIG)

@app.route('/scrape', methods=['POST'])
def trigger_scrape():
    auth_header = request.headers.get('Authorization')
    if auth_header != API_SECRET: return jsonify({'message': 'Unauthorized'}), 401

    try:
        data = request.json
        url = data.get('url', '').strip()
        admin_email = data.get('adminEmail')
        
        if not url: return jsonify({'message': 'No URL provided'}), 400

        # Ensure URL is clean
        if 'rewayat.club' in url:
            meta = fetch_metadata_rewayat(url)
            if not meta: return jsonify({'message': 'Failed metadata'}), 400
            thread = threading.Thread(target=worker_rewayat_probe, args=(url, admin_email, meta))
            thread.start()
            return jsonify({'message': 'Scraping started (Rewayat Club).'}), 200
            
        elif 'ar-no.com' in url:
            meta = fetch_metadata_madara(url)
            if not meta: return jsonify({'message': 'Failed metadata'}), 400
            thread = threading.Thread(target=worker_madara_list, args=(url, admin_email, meta))
            thread.start()
            return jsonify({'message': 'Scraping started (Ar-Novel).'}), 200

        elif 'markazriwayat.com' in url:
            meta = fetch_metadata_markaz(url)
            if not meta: return jsonify({'message': 'Failed metadata'}), 400
            thread = threading.Thread(target=worker_madara_list, args=(url, admin_email, meta))
            thread.start()
            return jsonify({'message': 'Scraping started (Markaz Riwayat).'}), 200

        elif 'novelfire.net' in url:
            meta = fetch_metadata_novelfire(url)
            if not meta: return jsonify({'message': 'Failed metadata'}), 400
            thread = threading.Thread(target=worker_novelfire_list, args=(url, admin_email, meta))
            thread.start()
            return jsonify({'message': 'Scraping started (Novel Fire).'}), 200

        elif 'wuxiabox.com' in url or 'wuxiaspot.com' in url:
            meta = fetch_metadata_wuxiabox(url)
            if not meta: return jsonify({'message': 'Failed metadata'}), 400
            thread = threading.Thread(target=worker_wuxiabox_list, args=(url, admin_email, meta))
            thread.start()
            return jsonify({'message': 'Scraping started (WuxiaBox/Spot).'}), 200

        elif 'freewebnovel.com' in url:
            meta = fetch_metadata_freewebnovel(url)
            if not meta: return jsonify({'message': 'Failed metadata'}), 400
            thread = threading.Thread(target=worker_freewebnovel_list, args=(url, admin_email, meta))
            thread.start()
            return jsonify({'message': 'Scraping started (FreeWebNovel).'}), 200

        elif 'fanmtl.com' in url:
            meta = fetch_metadata_fanmtl(url)
            if not meta: return jsonify({'message': 'Failed metadata'}), 400
            thread = threading.Thread(target=worker_fanmtl_list, args=(url, admin_email, meta))
            thread.start()
            return jsonify({'message': 'Scraping started (FanMTL).'}), 200

        elif 'novelbin.com' in url:
            meta = fetch_metadata_novelbin(url)
            if not meta: return jsonify({'message': 'Failed metadata'}), 400
            thread = threading.Thread(target=worker_novelbin_list, args=(url, admin_email, meta))
            thread.start()
            return jsonify({'message': 'Scraping started (NovelBin).'}), 200

        else:
            return jsonify({'message': 'Unsupported Domain'}), 400
            
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Server Error: {error_trace}")
        return jsonify({'message': 'Internal Server Error', 'details': str(e), 'trace': error_trace}), 500

# ==========================================
# 🔄 MAIN AUTOMATIC SCHEDULER LOGIC
# ==========================================

def perform_single_scrape(url, admin_email):
    try:
        if not url:
            return False

        if 'rewayat.club' in url:
            meta = fetch_metadata_rewayat(url)
            if not meta: return False
            worker_rewayat_probe(url, admin_email, meta)
            return True

        elif 'ar-no.com' in url:
            meta = fetch_metadata_madara(url)
            if not meta: return False
            worker_madara_list(url, admin_email, meta)
            return True

        elif 'markazriwayat.com' in url:
            meta = fetch_metadata_markaz(url)
            if not meta: return False
            worker_madara_list(url, admin_email, meta)
            return True

        elif 'novelfire.net' in url:
            meta = fetch_metadata_novelfire(url)
            if not meta: return False
            worker_novelfire_list(url, admin_email, meta)
            return True

        elif 'wuxiabox.com' in url or 'wuxiaspot.com' in url:
            meta = fetch_metadata_wuxiabox(url)
            if not meta: return False
            worker_wuxiabox_list(url, admin_email, meta)
            return True

        elif 'freewebnovel.com' in url:
            meta = fetch_metadata_freewebnovel(url)
            if not meta: return False
            worker_freewebnovel_list(url, admin_email, meta)
            return True

        elif 'fanmtl.com' in url:
            meta = fetch_metadata_fanmtl(url)
            if not meta: return False
            worker_fanmtl_list(url, admin_email, meta)
            return True

        elif 'novelbin.com' in url:
            meta = fetch_metadata_novelbin(url)
            if not meta: return False
            worker_novelbin_list(url, admin_email, meta)
            return True

        return False
    except Exception as e:
        print(f"Error in perform_single_scrape: {e}")
        return False

def fetch_watchlist():
    try:
        url = f"{NODE_BACKEND_URL}/api/admin/watchlist"
        headers = {'x-api-secret': API_SECRET}
        response = requests.get(url, headers=headers, timeout=25)
        if response.status_code != 200:
            print(f"Failed to fetch watchlist: {response.status_code}")
            return []
        return response.json().get('data', [])
    except Exception as e:
        print(f"Watchlist fetch error: {e}")
        return []

def scheduler_loop():
    while True:
        try:
            if not SCHEDULER_CONFIG['active']:
                time.sleep(5)
                continue
            
            now = time.time()
            if now >= SCHEDULER_CONFIG['next_run']:
                SCHEDULER_CONFIG['status'] = 'running'
                SCHEDULER_CONFIG['last_run'] = datetime.now().isoformat()
                
                watchlist = fetch_watchlist()
                print(f"Scheduler: fetched watchlist {len(watchlist)} items")
                
                ongoing = [x for x in watchlist if str(x.get('status','')).lower() == 'ongoing' and x.get('sourceUrl')]
                
                for item in ongoing:
                    novel_url = item.get('sourceUrl')
                    print(f"Scheduler scraping: {novel_url}")
                    perform_single_scrape(novel_url, SCHEDULER_CONFIG['admin_email'])
                    time.sleep(2)
                
                # Schedule next run
                SCHEDULER_CONFIG['next_run'] = time.time() + SCHEDULER_CONFIG['interval_seconds']
                SCHEDULER_CONFIG['status'] = 'idle'
            
            time.sleep(5)
        except Exception as e:
            print(f"Scheduler error: {e}")
            time.sleep(10)

# Start scheduler in background
threading.Thread(target=scheduler_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)