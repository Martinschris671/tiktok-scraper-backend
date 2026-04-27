import requests
import re
import urllib.parse
import os
from bs4 import BeautifulSoup

# --- FLASK IMPORTS ---
from flask import Flask, request, jsonify
from flask_cors import CORS

# =================================================================
# === CORE SCRAPING FUNCTION (ORIGINAL HEADERS RESTORED)
# =================================================================

def get_user_info(identifier, by_id=False):
    if by_id:
        url = f"https://www.tiktok.com/@{identifier}"
    else:
        if identifier.startswith('@'):
            identifier = identifier[1:]
        url = f"https://www.tiktok.com/@{identifier}"

    # REVERTED TO YOUR EXACT ORIGINAL HEADERS
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
    except requests.exceptions.RequestException:
        return None

    if response.status_code == 200:
        html_content = response.text
        
        try:
            soup = BeautifulSoup(html_content, 'lxml')
        except:
            soup = BeautifulSoup(html_content, 'html.parser')
        
        patterns = {
            'user_id': r'"webapp.user-detail":{"userInfo":{"user":{"id":"(\d+)"',
            'unique_id': r'"uniqueId":"(.*?)"',
            'nickname': r'"nickname":"(.*?)"',
            'followers': r'"followerCount":(\d+)',
            'following': r'"followingCount":(\d+)',
            'likes': r'"heartCount":(\d+)',
            'videos': r'"videoCount":(\d+)',
            'signature': r'"signature":"(.*?)"',
            'verified': r'"verified":(true|false)',
            'secUid': r'"secUid":"(.*?)"',
            'commentSetting': r'"commentSetting":(\d+)',
            'privateAccount': r'"privateAccount":(true|false)',
            'region': r'"ttSeller":false,"region":"([^"]*)"',
            'heart': r'"heart":(\d+)',
            'diggCount': r'"diggCount":(\d+)',
            'friendCount': r'"friendCount":(\d+)',
            'profile_pic': r'"avatarLarger":"(.*?)"'
        }
        
        info = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, html_content)
            info[key] = match.group(1) if match else f"No {key} found"
        
        if "profile_pic" in info:
            info['profile_pic'] = info['profile_pic'].replace('\\u002F', '/')
        
        social_links =[]
        bio = info.get('signature', "")
        
        link_urls = re.findall(r'href="(https://www\.tiktok\.com/link/v2\?[^"]*?scene=bio_url[^"]*?target=([^"&]+))"', html_content)
        for full_url, target in link_urls:
            target_decoded = urllib.parse.unquote(target)
            text_pattern = rf'href="{re.escape(full_url)}"[^>]*>.*?<span[^>]*SpanLink[^>]*>([^<]+)</span>'
            text_match = re.search(text_pattern, html_content, re.DOTALL)
            if text_match:
                link_text = text_match.group(1)
            else:
                link_text = target_decoded
                
            if not any(target_decoded in s for s in social_links):
                social_links.append(f"Link: {link_text} - {target_decoded}")
            
        span_links = re.findall(r'<span[^>]*class="[^"]*SpanLink[^"]*">([^<]+)</span>', html_content)
        for span_text in span_links:
            if '.' in span_text and ' ' not in span_text and not any(span_text in s for s in social_links):
                social_links.append(f"Link: {span_text} - {span_text}")
        
        all_targets = re.findall(r'scene=bio_url[^"]*?target=([^"&]+)', html_content)
        for target in all_targets:
            target_decoded = urllib.parse.unquote(target)
            if not any(target_decoded in s for s in social_links):
                text_pattern = rf'target={re.escape(target)}[^>]*>.*?<span[^>]*>([^<]+)</span>'
                text_match = re.search(text_pattern, html_content, re.DOTALL)
                if text_match:
                    link_text = text_match.group(1)
                else:
                    link_text = target_decoded
                
                social_links.append(f"Link: {link_text} - {target_decoded}")
        
        bio_link_pattern = r'"bioLink":{"link":"([^"]+)","risk":(\d+)}'
        bio_links_matches = re.findall(bio_link_pattern, html_content)

        for link, risk in bio_links_matches:
            clean_link = link.replace('\\u002F', '/')
            if not any(clean_link in s for s in social_links):
                social_links.append(f"💎 **{clean_link}**: `{clean_link}`")

        shared_links_pattern = r'"shareUrl":"([^"]+)"'
        shared_links_matches = re.findall(shared_links_pattern, html_content)

        for shared_url in shared_links_matches:
            clean_url = shared_url.replace('\\u002F', '/')
            if not any(clean_url in s for s in social_links):
                social_links.append(f"💎 **{clean_url}**: `{clean_url}`")

        share_links_div_pattern = re.compile(r'<div[^>]*class="[^"]*DivShareLinks[^"]*"[^>]*>(.*?)</div>', re.DOTALL)
        for div_match in share_links_div_pattern.finditer(html_content):
            div_content = div_match.group(1)
            
            div_links = re.finditer(r'<a[^>]*href="[^"]*scene=bio_url[^"]*target=([^"&]+)"[^>]*>.*?<span[^>]*class="[^"]*SpanLink[^"]*">([^<]+)</span>', div_content, re.DOTALL)
            
            for link_match in div_links:
                target = urllib.parse.unquote(link_match.group(1))
                link_text = link_match.group(2)
                
                if not any(target in s or link_text in s for s in social_links):
                    social_links.append(f"💎 **{link_text}**: `{target}`")
        
        span_matches = re.findall(r'<span[^>]*class="[^"]*SpanLink[^"]*">([^<]+)</span>', html_content)
        for span_text in span_matches:
            if '.' in span_text and not any(span_text in s for s in social_links):
                social_links.append(f"Link: {span_text} - {span_text}")
        
        biolink_matches = re.findall(r'class="[^"]*ABioLink[^"]*"[^>]*>.*?<span[^>]*class="[^"]*SpanLink[^"]*">([^<]+)</span>', html_content, re.DOTALL)
        for span_text in biolink_matches:
            if not any(span_text in s for s in social_links):
                social_links.append(f"Link: {span_text} - {span_text}")
        
        ig_pattern = re.search(r'[iI][gG]:\s*@?([a-zA-Z0-9._]+)', bio)
        if ig_pattern:
            instagram_username = ig_pattern.group(1)
            if not any(f"Instagram: @{instagram_username}" in s for s in social_links):
                social_links.append(f"Instagram: @{instagram_username}")
        
        social_patterns = {
            'snapchat': r'([sS][cC]|[sS]napchat):\s*@?([a-zA-Z0-9._]+)',
            'twitter': r'([tT]witter|[xX]):\s*@?([a-zA-Z0-9._]+)',
            'facebook': r'[fF][bB]:\s*@?([a-zA-Z0-9._]+)',
            'youtube': r'([yY][tT]|[yY]outube):\s*@?([a-zA-Z0-9._]+)',
            'telegram': r'[tT]elegram:\s*@?([a-zA-Z0-9._]+)'
        }
        
        for platform, pattern in social_patterns.items():
            match = re.search(pattern, bio)
            if match:
                username = match.group(2) if len(match.groups()) > 1 else match.group(1)
                if platform == 'snapchat':
                    social_link = f"Snapchat: {username}"
                elif platform == 'twitter':
                    social_link = f"Twitter/X: @{username}"
                elif platform == 'facebook':
                    social_link = f"Facebook: {username}"
                elif platform == 'youtube':
                    social_link = f"YouTube: {username}"
                elif platform == 'telegram':
                    social_link = f"Telegram: @{username}"
                
                if not any(social_link in s for s in social_links):
                    social_links.append(social_link)
        
        email_pattern = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', bio)
        if email_pattern:
            email = email_pattern.group(0)
            if not any(email in s for s in social_links):
                social_links.append(f"Email: {email}")
        
        info['social_links'] = social_links
        
        return info
    else:
        return None

# =================================================================
# === FLASK APPLICATION SETUP
# =================================================================

app = Flask(__name__)
CORS(app) 

@app.route('/', methods=['GET'])
def health_check():
    return "Bot is alive and running!", 200

@app.route('/scrape', methods=['GET'])
def simple_scrape_tiktok():
    identifier = request.args.get('username')
    
    if not identifier:
        return jsonify({
            "status": "error",
            "message": "Missing 'username' query parameter.",
            "code": "MISSING_PARAMETER"
        }), 400

    by_id = identifier.isdigit()

    try:
        user_data = get_user_info(identifier, by_id)
        
        if user_data is None:
            return jsonify({
                "status": "error",
                "message": f"TikTok profile not found for identifier: {identifier}. Or a network error occurred.",
                "code": "PROFILE_NOT_FOUND_OR_NETWORK_ERROR"
            }), 404
        
        cleaned_data = {}
        int_keys =['followers', 'following', 'likes', 'videos', 'commentSetting', 'heart', 'diggCount', 'friendCount']
        
        for key, value in user_data.items():
            if value == 'true':
                cleaned_data[key] = True
            elif value == 'false':
                cleaned_data[key] = False
            elif key in int_keys:
                try:
                    cleaned_data[key] = int(value)
                except ValueError:
                    cleaned_data[key] = value 
            else:
                cleaned_data[key] = value.replace('\\n', '\n') if key == 'signature' else value
        
        return jsonify({
            "status": "success",
            "identifier_used": identifier,
            "data": cleaned_data
        }), 200

    except Exception as e:
        print(f"Internal Server Error: {e}") 
        return jsonify({
            "status": "error",
            "message": "An unexpected internal server error occurred.",
            "code": "INTERNAL_SERVER_ERROR"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)