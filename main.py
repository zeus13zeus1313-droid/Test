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

# مفتاح سري لحماية الرابط
API_SECRET = os.environ.get('API_SECRET', 'Zeusndndjddnejdjdjdejekk29393838msmskxcm9239484jdndjdnddjj99292938338zeuslojdnejxxmejj82283849')

# رابط الخادم الرئيسي (Node.js)
NODE_BACKEND_URL = os.environ.get('NODE_BACKEND_URL', 'https://c-production-fba1.up.railway.app')

# ==========================================
# 🍪 إعدادات الكوكيز (تجاوز حماية تسجيل الدخول)
# ==========================================
# تم تحديث الكوكيز بناءً على طلبك لمركز الروايات
MARKAZ_COOKIES = 'wordpress_sec_198f6e9e82ba200a53325105f201ddc5=mikey%7C1771590380%7CKJphcZkhBFCpXyLUDrDcGPi9XmNOC47IPCSEHAPyfXS%7C5e8e596c5389b65f91a30668be6f16c7134b98b3ae55a007ed360594dd035527; cf_clearance=qYXkJIaj1IiaBKgi561_IQ.9oWgJ3fx10itfVR20lXY-1765278736-1.2.1.1-soYoRwUhDSq_.2cCoaJ22MPadmCmaQ0cW3AkfA1L97BJIbxQQro5hvpmuJxhQaT57TxfEW10l9gQYsmy5QgrwLsiWHScUWVvqYzZufRRYs9LIDPAhyxiOnL2Byevi12fb8iAZWttVNlqYWeKjH06tTp8bNhPx4dsmudPpIh0qzijEZhRk8lK6nWip1SeDFO2Of35W2rBKDEtjidGFyIj1RU3B7Xt.4CVoQbE9pGFaS8gFTMOp.0qmMMiz1UmHoFc; wpmanga-body-contrast=light; wpmanga-reading-history=W3siaWQiOjEyODE3LCJjIjoiMzEzMDgiLCJwIjoxLCJpIjoiIiwidCI6MTc2ODEwMTY3MH1d; sbjs_migrations=1418474375998%3D1; sbjs_current_add=fd%3D2026-02-06%2012%3A25%3A57%7C%7C%7Cep%3Dhttps%3A%2F%2Fmarkazriwayat.com%2F%7C%7C%7Crf%3Dhttps%3A%2F%2Fwww.bing.com%2F; sbjs_first_add=fd%3D2026-02-06%2012%3A25%3A57%7C%7C%7Cep%3Dhttps%3A%2F%2Fmarkazriwayat.com%2F%7C%7C%7Crf%3Dhttps%3A%2F%2Fwww.bing.com%2F; sbjs_current=typ%3Dreferral%7C%7C%7Csrc%3Dbing.com%7C%7C%7Cmdm%3Dreferral%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%2F%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29; sbjs_first=typ%3Dreferral%7C%7C%7Csrc%3Dbing.com%7C%7C%7Cmdm%3Dreferral%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%2F%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29; sbjs_udata=vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%206.2%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F109.0.0.0%20Safari%2F537.36%20Edg%2F109.0.1518.140; wordpress_test_cookie=WP%20Cookie%20check; _lscache_vary=8d8d3777c370b0211addc5b0a9411cd9; wordpress_logged_in_198f6e9e82ba200a53325105f201ddc5=mikey%7C1771590380%7CKJphcZkhBFCpXyLUDrDcGPi9XmNOC47IPCSEHAPyfXS%7Cb7d906dce3f0b160d5c2f585bfec331fe7d0cc3e4640a74945cc619df837e5c9; sbjs_session=pgs%3D2%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fmarkazriwayat.com%2F%3Fnsl_bypass_cache%3D74d71305203b9ce18787813c87e33f8c'

# ==========================================
# 🔄 GLOBAL SERVER-SIDE SCHEDULER STATE
# ==========================================
SCHEDULER_CONFIG = {
    'active': False,
    'interval_seconds': 86400, # Default 24h
    'next_run': 0,
    'last_run': 0,
    'status': 'idle',
    'admin_email': 'system@auto'
}

# ==========================================
# أدوات السحب المشتركة (Shared Scraper Tools)
# ==========================================

def get_headers(referer=None, use_cookies=False):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
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
        match = re.search(r'(\d+)\s*(sec|min|hour|day|week|month|year|ثانية|ثواني|دقيقة|دقائق|ساعة|ساعات|يوم|أيام|ايام|أسبوع|اسبوع|أسابيع|اسابيع|شهر|أشهر|اشهر|سنة|سنوات)', text)
        
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            
            delta = timedelta(seconds=0)
            
            # English Units
            if 'sec' in unit: delta = timedelta(seconds=amount)
            elif 'min' in unit: delta = timedelta(minutes=amount)
            elif 'hour' in unit: delta = timedelta(hours=amount)
            elif 'day' in unit: delta = timedelta(days=amount)
            elif 'week' in unit: delta = timedelta(weeks=amount)
            elif 'month' in unit: delta = timedelta(days=amount * 30)
            elif 'year' in unit: delta = timedelta(days=amount * 365)
            
            # Arabic Units
            elif 'ثان' in unit: delta = timedelta(seconds=amount)
            elif 'دقيق' in unit: delta = timedelta(minutes=amount)
            elif 'ساع' in unit: delta = timedelta(hours=amount)
            elif 'يوم' in unit or 'أيام' in unit or 'ايام' in unit: delta = timedelta(days=amount)
            elif 'أسبوع' in unit or 'اسبوع' in unit or 'أسابيع' in unit: delta = timedelta(weeks=amount)
            elif 'شهر' in unit or 'أشهر' in unit: delta = timedelta(days=amount * 30)
            elif 'سنة' in unit or 'سنوات' in unit: delta = timedelta(days=amount * 365)
            
            return (now - delta).isoformat()
            
        # محاولة قراءة تاريخ ثابت (May 20, 2024 / 2025/12/15)
        try:
            for fmt in ['%B %d, %Y', '%Y/%m/%d', '%d/%m/%Y', '%Y-%m-%d']:
                try:
                    dt = datetime.strptime(text, fmt)
                    return dt.isoformat()
                except: continue
        except:
            pass
            
        return None
    except:
        return None

def send_data_to_backend(payload):
    """إرسال البيانات إلى الخادم الرئيسي"""
    try:
        endpoint = f"{NODE_BACKEND_URL}/api/scraper/receive"
        headers = { 'Content-Type': 'application/json', 'Authorization': API_SECRET, 'x-api-secret': API_SECRET }
        response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Failed to send data: {e}")
        return False

def check_existing_chapters(title):
    """التحقق من الفصول الموجودة في الباك إند لمنع التكرار"""
    try:
        endpoint = f"{NODE_BACKEND_URL}/api/scraper/check-chapters"
        headers = { 'Content-Type': 'application/json', 'Authorization': API_SECRET, 'x-api-secret': API_SECRET }
        response = requests.post(endpoint, json={'title': title}, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('exists'):
                return data['chapters']
            else:
                return []
        return []
    except Exception as e:
        print(f"❌ Error checking existence: {e}")
        return []

# ==========================================
# 🟣 1. Rewayat Club (Nuxt) Logic
# ==========================================

def extract_from_nuxt(soup):
    try:
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'window.__NUXT__' in script.string:
                content = script.string
                # Extract poster
                match = re.search(r'poster_url:"(.*?)"', content)
                if not match: match = re.search(r'poster:"(.*?)"', content)
                if match:
                    raw_url = match.group(1)
                    return raw_url.encode('utf-8').decode('unicode_escape')
    except: pass
    return None

def fetch_metadata_rewayat(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
        
        cover_url = extract_from_nuxt(soup) or ""
        if not cover_url:
            og_image = soup.find("meta", property="og:image")
            if og_image: cover_url = og_image["content"]
        cover_url = fix_image_url(cover_url)

        desc_div = soup.find(class_='text-pre-line') or soup.find('div', class_='v-card__text')
        description = desc_div.get_text(separator="\n\n", strip=True) if desc_div else ""
        
        # 🔥🔥 STATUS CHECK - REWAYAT CLUB SPECIFIC 🔥🔥
        status = "مستمرة"
        # 1. Check for specific status badges in Vuetify chips
        chips = soup.find_all(class_='v-chip__content')
        for chip in chips:
            txt = chip.get_text(strip=True)
            if "مكتملة" in txt or "Completed" in txt:
                status = "مكتملة"
                break
        
        # 2. Fallback: Search in full text if not found
        if status == "مستمرة":
            if "مكتملة" in soup.get_text():
                status = "مكتملة"

        # 🔥 EXTRACT REAL LAST UPDATE DATE (NUXT/Vue Logic) 🔥
        last_update = None
        
        # Method 1: Regex search in subtitles
        subtitles = soup.find_all(class_='v-list-item__subtitle')
        for sub in subtitles:
            txt = sub.get_text(strip=True)
            # Match date YYYY/MM/DD
            date_match = re.search(r'(\d{4}/\d{1,2}/\d{1,2})', txt)
            if date_match:
                last_update = parse_relative_date(date_match.group(1))
                if last_update: break 
        
        return {
            'title': title, 'description': description, 'cover': cover_url,
            'status': status, 'category': 'عام', 'tags': [],
            'sourceUrl': url, 'lastUpdate': last_update
        }
    except Exception as e:
        print(f"Error Rewayat Meta: {e}")
        return None

def scrape_chapter_rewayat(base_url, chapter_number):
    url = f"{base_url.rstrip('/')}/chapters/{chapter_number}"
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None, None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        content_div = soup.find(class_='text-pre-line') or soup.find('div', class_='v-card__text')
        if not content_div: return None, None
        
        text = content_div.get_text(separator="\n\n", strip=True)
        if len(text) < 50: return None, None
        
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else f"الفصل {chapter_number}"
        
        return title, text
    except:
        return None, None

def worker_rewayat(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0
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
# 🟠 2. Madara (ar-novel / markazriwayat) Logic
# ==========================================

def get_base_url(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"

def clean_madara_title(title):
    title = re.sub(r'[\n\r\t]+', ' ', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def fetch_metadata_madara(url):
    try:
        use_cookies = 'markazriwayat.com' in url
        response = requests.get(url, headers=get_headers(use_cookies=use_cookies), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')

        title = "Unknown Title"
        title_tag = soup.find('div', class_='post-title')
        if title_tag:
            h1 = title_tag.find('h1')
            if h1: title = h1.get_text(strip=True)
            else: title = title_tag.get_text(strip=True)

        description = ""
        desc_div = soup.find('div', class_='summary__content')
        if desc_div:
            description = desc_div.get_text(separator="\n\n", strip=True)

        cover = ""
        img_container = soup.find('div', class_='summary_image')
        if img_container:
            img_tag = img_container.find('img')
            if img_tag:
                cover = img_tag.get('data-src') or img_tag.get('src') or img_tag.get('srcset', '').split(' ')[0]
                cover = fix_image_url(cover)

        novel_id = None
        shortlink = soup.find("link", rel="shortlink")
        if shortlink:
            match = re.search(r'p=(\d+)', shortlink.get('href', ''))
            if match: novel_id = match.group(1)
        if not novel_id:
            id_input = soup.find('input', class_='rating-post-id')
            if id_input: novel_id = id_input.get('value')

        status = "مستمرة"
        status_divs = soup.find_all('div', class_='post-status')
        for div in status_divs:
            if 'مكتمل' in div.get_text() or 'Completed' in div.get_text():
                status = "مكتملة"
                break

        last_update = None
        date_div = soup.find('div', class_='post-content_item')
        if date_div:
            date_text = date_div.get_text(strip=True)
            last_update = parse_relative_date(date_text)

        return {
            'title': title, 'description': description, 'cover': cover,
            'status': status, 'category': 'عام', 'tags': [],
            'sourceUrl': url, 'lastUpdate': last_update, 'novel_id': novel_id
        }
    except Exception as e:
        print(f"Error Madara Meta: {e}")
        return None

def fetch_chapter_list_madara(novel_id, novel_url):
    chapters = []
    base_url = get_base_url(novel_url)
    use_cookies = 'markazriwayat.com' in novel_url

    if novel_url:
        try:
            res = requests.get(novel_url, headers=get_headers(use_cookies=use_cookies), timeout=15)
            soup = BeautifulSoup(res.content, 'html.parser')
            items = soup.select('li.wp-manga-chapter a')
            for a in items:
                link = a.get('href')
                raw_title = a.get_text(strip=True)
                num_match = re.search(r'(\d+)', raw_title)
                number = int(num_match.group(1)) if num_match else 0
                clean_title = clean_madara_title(raw_title)
                if number > 0:
                    chapters.append({'number': number, 'url': link, 'title': clean_title})
            if chapters: return chapters
        except: pass

    if not novel_id: return []
    
    ajax_url = f"{base_url}/wp-admin/admin-ajax.php"
    payload = {'action': 'manga_get_chapters', 'manga': novel_id}
    try:
        response = requests.post(ajax_url, data=payload, headers=get_headers(referer=novel_url, use_cookies=use_cookies), timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.select('li.wp-manga-chapter a')
            for a in items:
                link = a.get('href')
                raw_title = a.get_text(strip=True)
                num_match = re.search(r'(\d+)', raw_title)
                number = int(num_match.group(1)) if num_match else 0
                clean_title = clean_madara_title(raw_title)
                if number > 0:
                    chapters.append({'number': number, 'url': link, 'title': clean_title})
    except: pass
    return chapters

def scrape_chapter_madara(url):
    try:
        use_cookies = 'markazriwayat.com' in url
        response = requests.get(url, headers=get_headers(use_cookies=use_cookies), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        content_div = soup.find('div', class_='reading-content')
        if not content_div: return None
        
        for p in content_div.find_all('p'):
            if p.get_text(strip=True) == '': p.decompose()
            
        text = content_div.get_text(separator="\n\n", strip=True)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.replace('اكمال القراءة', '').replace('إعدادات القراءة', '')
        
        if len(text) < 200 and 'سجل' in text:
            print("⚠️ Warning: Chapter content seems blocked by login wall.")
            return text
            
        return None if len(text) < 50 else text
    except:
        return None

def worker_madara_list(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0
    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})
    
    all_chapters = fetch_chapter_list_madara(metadata.get('novel_id'), url)
    if not all_chapters:
        print(f"No chapters found for {metadata['title']}")
        return
        
    all_chapters.sort(key=lambda x: x['number'])
    batch = []
    
    for chap in all_chapters:
        if chap['number'] in existing_chapters: continue
            
        print(f"Scraping Madara: Ch {chap['number']}...")
        content = scrape_chapter_madara(chap['url'])
        
        if content:
            batch.append({'number': chap['number'], 'title': chap['title'], 'content': content})
            
        if len(batch) >= 5:
            send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
            batch = []
            time.sleep(1.5)
            
    if batch:
        send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})


# ==========================================
# 🟢 3. NovelFire Logic
# ==========================================

def fetch_metadata_novelfire(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown"
        
        cover = ""
        img_tag = soup.select_one('.novel-cover img')
        if img_tag: cover = img_tag.get('data-src') or img_tag.get('src')
        cover = fix_image_url(cover, 'https://novelfire.net')
        
        desc_div = soup.select_one('.summary .content')
        description = desc_div.get_text(separator="\n\n", strip=True) if desc_div else ""
        
        status = "مستمرة"
        status_tag = soup.select_one('.header-stats strong')
        if status_tag and 'completed' in status_tag.get_text().lower():
            status = "مكتملة"
            
        tags = [a.get_text(strip=True) for a in soup.select('.categories a')]
        category = tags[0] if tags else "عام"
        
        last_update = None
        
        return {
            'title': title, 'description': description, 'cover': cover,
            'status': status, 'category': category, 'tags': tags,
            'sourceUrl': url, 'lastUpdate': last_update
        }
    except Exception as e:
        print(f"Error NovelFire Meta: {e}")
        return None

def fetch_chapter_list_novelfire(novel_url):
    chapters = []
    if not novel_url.rstrip('/').endswith('/chapters'):
        list_url = novel_url.rstrip('/') + '/chapters'
    else:
        list_url = novel_url
        
    try:
        current_page = 1
        while True:
            page_url = f"{list_url}?page={current_page}"
            res = requests.get(page_url, headers=get_headers(), timeout=15)
            if res.status_code != 200: break
            
            soup = BeautifulSoup(res.content, 'html.parser')
            items = soup.select('ul.chapter-list li a')
            if not items: break
            
            for a in items:
                href = a.get('href')
                full_link = urljoin('https://novelfire.net', href)
                title = a.get('title') or a.get_text(strip=True)
                match = re.search(r'chapter-(\d+)', href)
                if not match: match = re.search(r'(\d+)', title)
                num = int(match.group(1)) if match else 0
                if num > 0:
                    chapters.append({'number': num, 'url': full_link, 'title': title})
                    
            next_btn = soup.select_one('ul.pagination a[rel="next"]')
            if next_btn: current_page += 1
            else: break
            
        unique = {c['number']: c for c in chapters}.values()
        chapters = list(unique)
        chapters.sort(key=lambda x: x['number'])
        return chapters
    except Exception as e:
        print(f"Error NovelFire List: {e}")
        return []

def scrape_chapter_novelfire(url):
    try:
        res = requests.get(url, headers=get_headers(), timeout=15)
        if res.status_code != 200: return None
        soup = BeautifulSoup(res.content, 'html.parser')
        
        content_div = soup.find('div', id='chapter-content')
        if not content_div: return None
        
        paragraphs = content_div.find_all('p')
        text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        return text if len(text) > 50 else None
    except: return None

def worker_novelfire_list(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0
    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})
    
    all_chapters = fetch_chapter_list_novelfire(url)
    batch = []
    
    for chap in all_chapters:
        if chap['number'] in existing_chapters: continue
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
# 🔵 4. WuxiaBox / WuxiaSpot Logic
# ==========================================

def fetch_metadata_wuxiabox(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown"
        
        cover = ""
        img_tag = soup.select_one('.novel-cover img')
        if img_tag: cover = img_tag.get('src')
        cover = fix_image_url(cover, get_base_url(url))
        
        desc_div = soup.select_one('.summary .content')
        description = desc_div.get_text(separator="\n\n", strip=True) if desc_div else ""
        
        status = "مستمرة"
        status_tag = soup.select_one('.header-stats strong')
        if status_tag and 'completed' in status_tag.get_text().lower():
            status = "مكتملة"
            
        tags = [a.get_text(strip=True) for a in soup.select('.categories a')]
        category = tags[0] if tags else "عام"
        
        return {
            'title': title, 'description': description, 'cover': cover,
            'status': status, 'category': category, 'tags': tags,
            'sourceUrl': url, 'lastUpdate': None
        }
    except Exception as e:
        print(f"Error WuxiaBox Meta: {e}")
        return None

def fetch_chapter_list_wuxiabox(url):
    chapters = []
    base_url = get_base_url(url)
    try:
        current_url = url
        while current_url:
            res = requests.get(current_url, headers=get_headers(), timeout=15)
            if res.status_code != 200: break
            
            soup = BeautifulSoup(res.content, 'html.parser')
            items = soup.select('ul.chapter-list li a')
            if not items: break
            
            for a in items:
                href = a.get('href')
                full_link = urljoin(base_url, href)
                title = a.get('title') or a.get_text(strip=True)
                match = re.search(r'chapter-(\d+)', href)
                if not match: match = re.search(r'(\d+)', title)
                num = int(match.group(1)) if match else 0
                if num > 0:
                    chapters.append({'number': num, 'url': full_link, 'title': title})
                    
            next_btn = None
            pagination_links = soup.select('ul.pagination li a')
            for link in pagination_links:
                if '>' in link.get_text() or 'Next' in link.get_text():
                    next_btn = link
                    break
                    
            if next_btn:
                next_href = next_btn.get('href')
                current_url = urljoin(base_url, next_href)
                time.sleep(0.5)
            else: break
            
        unique_chapters = {c['number']: c for c in chapters}.values()
        chapters = list(unique_chapters)
        chapters.sort(key=lambda x: x['number'])
        return chapters
    except Exception as e:
        print(f"Error WuxiaBox List: {e}")
        return []

def scrape_chapter_wuxiabox(url):
    try:
        res = requests.get(url, headers=get_headers(), timeout=15)
        if res.status_code != 200: return None
        soup = BeautifulSoup(res.content, 'html.parser')
        
        content_div = soup.select_one('.chapter-content')
        if not content_div: return None
        
        paragraphs = content_div.find_all('p')
        text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        return text if len(text) > 50 else None
    except: return None

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
# 🟡 5. Freewebnovel Logic
# ==========================================

def fetch_metadata_freewebnovel(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown"
        
        cover = ""
        img_tag = soup.select_one('.pic img')
        if img_tag: cover = img_tag.get('src')
        cover = fix_image_url(cover, 'https://freewebnovel.com')
        
        desc_div = soup.select_one('.m-desc')
        description = desc_div.get_text(separator="\n\n", strip=True) if desc_div else ""
        
        status = "مستمرة"
        if 'completed' in soup.get_text().lower(): status = "مكتملة"
            
        tags = []
        category = "عام"
        
        return {
            'title': title, 'description': description, 'cover': cover,
            'status': status, 'category': category, 'tags': tags,
            'sourceUrl': url, 'lastUpdate': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error Freewebnovel Meta: {e}")
        return None

def fetch_chapter_list_freewebnovel(url):
    chapters = []
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return []
        soup = BeautifulSoup(response.content, 'html.parser')
        
        items = soup.select('ul#idData li a')
        for a in items:
            href = a.get('href')
            full_link = urljoin('https://freewebnovel.com', href)
            title = a.get('title') or a.get_text(strip=True)
            match = re.search(r'Chapter\s+(\d+)', title, re.IGNORECASE)
            num = int(match.group(1)) if match else 0
            if num > 0:
                chapters.append({'number': num, 'url': full_link, 'title': title})
                
        unique = {c['number']: c for c in chapters}.values()
        chapters = list(unique)
        chapters.sort(key=lambda x: x['number'])
        return chapters
    except Exception as e:
        print(f"Error Freewebnovel List: {e}")
        return []

def scrape_chapter_freewebnovel(url):
    try:
        res = requests.get(url, headers=get_headers(), timeout=15)
        if res.status_code != 200: return None
        soup = BeautifulSoup(res.content, 'html.parser')
        
        content_div = soup.find('div', class_='txt')
        if not content_div: return None
        
        paragraphs = content_div.find_all('p')
        text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        return text if len(text) > 50 else None
    except: return None

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
# 🟢 6. FanMTL Logic
# ==========================================

def fetch_metadata_fanmtl(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Unknown"
        
        cover = ""
        img_tag = soup.select_one('.novel-cover img')
        if img_tag: cover = img_tag.get('src') or img_tag.get('data-src')
        cover = fix_image_url(cover, 'https://fanmtl.com')
        
        desc_div = soup.select_one('.summary .content')
        if not desc_div:
            desc_div = soup.find('div', class_='summary')
        description = desc_div.get_text(separator="\n\n", strip=True) if desc_div else ""
        
        status = "مستمرة"
        status_span = soup.select_one('.header-stats strong')
        if status_span:
            status_text = status_span.get_text(strip=True).lower()
            if 'ongoing' not in status_text and 'completed' in status_text:
                status = "مكتملة"
        else:
            if "completed" in soup.get_text().lower() or "مكتملة" in soup.get_text():
                status = "مكتملة"
                
        tags = [a.get_text(strip=True) for a in soup.select('.categories a')]
        category = tags[0] if tags else "عام"
        
        return {
            'title': title, 'description': description, 'cover': cover,
            'status': status, 'category': category, 'tags': tags,
            'sourceUrl': url, 'lastUpdate': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error FanMTL Meta: {e}")
        return None

def fetch_chapter_list_fanmtl(novel_url):
    chapters = []
    list_url = novel_url.rstrip('/') + '/chapters' if not novel_url.rstrip('/').endswith('/chapters') else novel_url
        
    try:
        page_num = 1
        while True:
            page_url = f"{list_url}?page={page_num}"
            res = requests.get(page_url, headers=get_headers(), timeout=15)
            if res.status_code != 200: break
            
            soup = BeautifulSoup(res.content, 'html.parser')
            items = soup.select('ul.chapter-list li a')
            if not items: break
            
            for a in items:
                href = a.get('href')
                full_link = urljoin('https://fanmtl.com', href)
                title = a.get('title') or a.get_text(strip=True)
                match = re.search(r'chapter-(\d+)', href, re.IGNORECASE)
                if not match: match = re.search(r'(\d+)', title)
                num = int(match.group(1)) if match else 0
                if num > 0:
                    chapters.append({'number': num, 'url': full_link, 'title': title})
                    
            next_btn = soup.select_one('ul.pagination a[rel="next"]')
            if not next_btn:
                pagination_links = soup.select('ul.pagination li a')
                for link in pagination_links:
                    if '>' in link.get_text() or 'Next' in link.get_text():
                        next_btn = link
                        break
                        
            if next_btn:
                page_num += 1
                time.sleep(0.5)
            else: break
            
        unique = {c['number']: c for c in chapters}.values()
        chapters = list(unique)
        chapters.sort(key=lambda x: x['number'])
        print(f"✅ Total FanMTL chapters: {len(chapters)}")
        return chapters
    except Exception as e:
        print(f"Error fetching FanMTL chapter list: {e}")
        return []

def scrape_chapter_fanmtl(url):
    try:
        res = requests.get(url, headers=get_headers(), timeout=15)
        if res.status_code != 200: return None
        soup = BeautifulSoup(res.content, 'html.parser')
        
        content_div = soup.find('div', id='chapter-content')
        if not content_div: return None
        
        paragraphs = content_div.find_all('p')
        text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        return text if len(text) > 50 else None
    except: return None

def worker_fanmtl_list(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0
    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})
    
    all_chapters = fetch_chapter_list_fanmtl(url)
    batch = []
    
    for chap in all_chapters:
        if chap['number'] in existing_chapters: continue
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
# 🟣 7. NovelBin Logic (تمت الإضافة بناءً على طلبك)
# ==========================================

def fetch_metadata_novelbin(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title_tag = soup.find('meta', property='og:title')
        title = title_tag['content'].split(' Novel -')[0].strip() if title_tag else "Unknown"
        
        cover = ""
        og_img = soup.find('meta', property='og:image')
        if og_img: cover = og_img['content']
        cover = fix_image_url(cover)
        
        desc_tag = soup.find('div', class_='desc-text')
        if not desc_tag:
            desc_tag = soup.find('div', itemprop='description')
        description = desc_tag.get_text(separator="\n\n", strip=True) if desc_tag else ""
        if not description:
            meta_desc = soup.find('meta', property='og:description')
            description = meta_desc['content'] if meta_desc else ""
        
        status = "مستمرة"
        status_tag = soup.find('meta', property='og:novel:status')
        if status_tag and status_tag['content'].lower() == 'completed':
            status = "مكتملة"
            
        tags = []
        genre_tag = soup.find('meta', property='og:novel:genre')
        if genre_tag:
            tags = [g.strip().capitalize() for g in genre_tag['content'].split(',')]
        category = tags[0] if tags else "عام"
        
        last_update = None
        update_tag = soup.find('meta', property='og:novel:update_time')
        if update_tag:
            try:
                dt = datetime.fromisoformat(update_tag['content'].replace('Z', '+00:00'))
                last_update = dt.isoformat()
            except: pass
            
        return {
            'title': title, 'description': description, 'cover': cover,
            'status': status, 'category': category, 'tags': tags,
            'sourceUrl': url, 'lastUpdate': last_update
        }
    except Exception as e:
        print(f"Error NovelBin Meta: {e}")
        return None

def fetch_chapter_list_novelbin(url):
    chapters = []
    try:
        slug = url.rstrip('/').split('/')[-1]
        ajax_url = f"https://novelbin.com/ajax/chapter-archive?novelId={slug}"
        response = requests.get(ajax_url, headers=get_headers(), timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.select('ul.list-chapter li a')
            for a in items:
                href = a.get('href', '')
                if href.startswith('/'):
                    href = 'https://novelbin.com' + href
                title = a.get('title') or a.get_text(strip=True)
                
                match = re.search(r'chapter-(\d+)', href, re.IGNORECASE)
                if not match:
                    match = re.search(r'(\d+)', title)
                num = int(match.group(1)) if match else 0
                
                if num > 0:
                    chapters.append({'number': num, 'url': href, 'title': title})
        
        # في حال لم ينجح الأجاكس، يتم المحاولة من الصفحة الرئيسية
        if not chapters:
            response = requests.get(url, headers=get_headers(), timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.select('ul.list-chapter li a')
            for a in items:
                href = a.get('href', '')
                if href.startswith('/'):
                    href = 'https://novelbin.com' + href
                title = a.get('title') or a.get_text(strip=True)
                
                match = re.search(r'chapter-(\d+)', href, re.IGNORECASE)
                if not match:
                    match = re.search(r'(\d+)', title)
                num = int(match.group(1)) if match else 0
                
                if num > 0:
                    chapters.append({'number': num, 'url': href, 'title': title})

        unique = {c['number']: c for c in chapters}.values()
        chapters = list(unique)
        chapters.sort(key=lambda x: x['number'])
        return chapters
    except Exception as e:
        print(f"Error NovelBin List: {e}")
        return []

def scrape_chapter_novelbin(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        content_div = soup.find('div', id='chr-content')
        if not content_div: return None
        
        # تنظيف الإعلانات والسكربتات
        for bad in content_div.find_all(['script', 'style', 'div', 'iframe']):
            bad.decompose()
            
        paragraphs = content_div.find_all('p')
        if paragraphs:
            text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        else:
            text = content_div.get_text(separator="\n\n", strip=True)
            
        return text if len(text) > 50 else None
    except Exception as e:
        print(f"Error scraping NovelBin chapter: {e}")
        return None

def worker_novelbin_list(url, admin_email, metadata):
    existing_chapters = check_existing_chapters(metadata['title'])
    skip_meta = len(existing_chapters) > 0
    send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': [], 'skipMetadataUpdate': skip_meta})
    
    all_chapters = fetch_chapter_list_novelbin(url)
    if not all_chapters:
        print("No chapters found for NovelBin")
        return
        
    batch = []
    scraped_this_minute = 0
    
    for chap in all_chapters:
        if chap['number'] in existing_chapters: continue
            
        print(f"Scraping NovelBin: Ch {chap['number']}...")
        content = scrape_chapter_novelbin(chap['url'])
        
        if content:
            batch.append({'number': chap['number'], 'title': chap['title'], 'content': content})
            scraped_this_minute += 1  # زيادة عداد الفصول المسحوبة
            
        if len(batch) >= 5:
            send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
            batch = []
            
        # إضافة شرط التوقف بعد سحب 15 فصل لمدة 60 ثانية لحماية الخادم
        if scraped_this_minute >= 15:
            if batch: # إرسال أي بيانات متبقية قبل النوم
                send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})
                batch = []
            print("⏳ Scraped 15 chapters from NovelBin, sleeping for 60 seconds to avoid ban...")
            time.sleep(60)
            scraped_this_minute = 0
            
    if batch:
        send_data_to_backend({'adminEmail': admin_email, 'novelData': metadata, 'chapters': batch, 'skipMetadataUpdate': True})


# ==========================================
# Main Orchestrator
# ==========================================

@app.route('/', methods=['GET'])
def health_check():
    return "ZEUS Scraper Service is Running", 200

@app.route('/scheduler/config', methods=['POST'])
def configure_scheduler():
    auth_header = request.headers.get('Authorization')
    if auth_header != API_SECRET and request.headers.get('x-api-secret') != API_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    if not data: return jsonify({'error': 'No data'}), 400
    
    if 'active' in data: SCHEDULER_CONFIG['active'] = data['active']
    if 'interval_seconds' in data: SCHEDULER_CONFIG['interval_seconds'] = data['interval_seconds']
    if 'admin_email' in data: SCHEDULER_CONFIG['admin_email'] = data['admin_email']
    
    return jsonify({'message': 'Scheduler updated', 'config': SCHEDULER_CONFIG})

@app.route('/scrape', methods=['POST'])
def start_scraping():
    auth_header = request.headers.get('Authorization')
    if auth_header != API_SECRET and request.headers.get('x-api-secret') != API_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    url = data.get('url')
    admin_email = data.get('adminEmail')
    
    if not url or not admin_email:
        return jsonify({'error': 'Missing URL or Admin Email'}), 400
        
    print(f"🚀 Received Scraping Request for: {url}")

    if 'rewayat.club' in url:
        meta = fetch_metadata_rewayat(url)
        if meta:
            threading.Thread(target=worker_rewayat, args=(url, admin_email, meta)).start()
            return jsonify({'message': 'Scraping started (Rewayat)'}), 200
            
    elif 'markazriwayat.com' in url or 'ar-novel.com' in url:
        meta = fetch_metadata_madara(url)
        if meta:
            threading.Thread(target=worker_madara_list, args=(url, admin_email, meta)).start()
            return jsonify({'message': 'Scraping started (Madara)'}), 200
            
    elif 'novelfire.net' in url or 'novelfire.docs' in url:
        meta = fetch_metadata_novelfire(url)
        if meta:
            threading.Thread(target=worker_novelfire_list, args=(url, admin_email, meta)).start()
            return jsonify({'message': 'Scraping started (NovelFire)'}), 200
            
    elif 'wuxiabox.com' in url or 'wuxiaspot.com' in url:
        meta = fetch_metadata_wuxiabox(url)
        if meta:
            threading.Thread(target=worker_wuxiabox_list, args=(url, admin_email, meta)).start()
            return jsonify({'message': 'Scraping started (WuxiaBox)'}), 200
            
    elif 'freewebnovel.com' in url:
        meta = fetch_metadata_freewebnovel(url)
        if meta:
            threading.Thread(target=worker_freewebnovel_list, args=(url, admin_email, meta)).start()
            return jsonify({'message': 'Scraping started (Freewebnovel)'}), 200
            
    elif 'fanmtl.com' in url:
        meta = fetch_metadata_fanmtl(url)
        if meta:
            threading.Thread(target=worker_fanmtl_list, args=(url, admin_email, meta)).start()
            return jsonify({'message': 'Scraping started (FanMTL)'}), 200
            
    elif 'novelbin.com' in url:  # إضافة NovelBin لنظام التشغيل المباشر
        meta = fetch_metadata_novelbin(url)
        if meta:
            threading.Thread(target=worker_novelbin_list, args=(url, admin_email, meta)).start()
            return jsonify({'message': 'Scraping started (NovelBin)'}), 200

    return jsonify({'error': 'Unsupported website or failed to fetch metadata.'}), 400

def perform_single_scrape(url, admin_email):
    print(f"⚙️ [Scheduler] Processing: {url}")
    
    if 'rewayat.club' in url:
        meta = fetch_metadata_rewayat(url)
        if meta: worker_rewayat(url, admin_email, meta)
        
    elif 'markazriwayat.com' in url or 'ar-novel.com' in url:
        meta = fetch_metadata_madara(url)
        if meta: worker_madara_list(url, admin_email, meta)
        
    elif 'novelfire.net' in url:
        meta = fetch_metadata_novelfire(url)
        if meta: worker_novelfire_list(url, admin_email, meta)
        
    elif 'wuxiabox.com' in url or 'wuxiaspot.com' in url:
        meta = fetch_metadata_wuxiabox(url)
        if meta: worker_wuxiabox_list(url, admin_email, meta)
        
    elif 'freewebnovel.com' in url:
        meta = fetch_metadata_freewebnovel(url)
        if meta: worker_freewebnovel_list(url, admin_email, meta)
        
    elif 'fanmtl.com' in url:
        meta = fetch_metadata_fanmtl(url)
        if meta: worker_fanmtl_list(url, admin_email, meta)
        
    elif 'novelbin.com' in url: # إضافة NovelBin للمجدول (Scheduler)
        meta = fetch_metadata_novelbin(url)
        if meta: worker_novelbin_list(url, admin_email, meta)

def scheduler_loop():
    print("⏳ Scheduler Thread Started...")
    while True:
        try:
            now = time.time()
            if SCHEDULER_CONFIG['active'] and now >= SCHEDULER_CONFIG['next_run']:
                print("🔄 [Scheduler] Triggering scheduled task...")
                SCHEDULER_CONFIG['status'] = 'running'
                
                try:
                    endpoint = f"{NODE_BACKEND_URL}/api/scraper/watchlist"
                    headers = { 'Authorization': API_SECRET, 'x-api-secret': API_SECRET }
                    res = requests.get(endpoint, headers=headers, timeout=30)
                    
                    if res.status_code == 200:
                        watchlist = res.json()
                        print(f"📋 [Scheduler] Found {len(watchlist)} novels.")
                        
                        for item in watchlist:
                            if item.get('sourceUrl') and item.get('status') == 'ongoing':
                                perform_single_scrape(item['sourceUrl'], SCHEDULER_CONFIG['admin_email'])
                                time.sleep(2) # Politeness delay
                        
                        print("✅ [Scheduler] Job Completed.")
                    else:
                        print(f"❌ [Scheduler] Failed to fetch watchlist: HTTP {res.status_code}")
                except Exception as req_err:
                    print(f"❌ [Scheduler] Connection Error: {req_err}")

                # Update next run time
                SCHEDULER_CONFIG['last_run'] = now
                SCHEDULER_CONFIG['next_run'] = now + SCHEDULER_CONFIG['interval_seconds']
                SCHEDULER_CONFIG['status'] = 'idle'
            
            time.sleep(5) # Check every 5 seconds
        except Exception as e:
            print(f"🔥 [Scheduler] Critical Loop Error: {e}")
            time.sleep(60)

# Start Scheduler Thread immediately
scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
scheduler_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)