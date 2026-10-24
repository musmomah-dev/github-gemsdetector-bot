import os
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Mots-clés cibles pour ton business et tes compétences
TARGET_KEYWORDS = [
    "ai", "artificial intelligence", "llm", "gpt", "agent", "openai", "claude",
    "automation", "n8n", "make", "workflow", "bot", "scraper", "scraping",
    "api", "tool", "utility", "cli",
    "saas", "boilerplate", "starter", "open-source", "free",
    "crypto", "bitcoin", "trading", "stock", "finance", "bourse", "investment"
]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Erreur Telegram: {response.text}")
    else:
        print("Message envoyé avec succès !")

def get_github_trending():
    url = "https://github.com/trending"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Erreur de scraping GitHub: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    repos = []
    
    for article in soup.select('article.Box-row'):
        title_tag = article.select_one('h2 a')
        if not title_tag:
            continue
        repo_name = title_tag.text.strip().replace('\n', '').replace(' ', '')
        repo_url = "https://github.com" + title_tag['href']

        desc_tag = article.select_one('p')
        repo_desc = desc_tag.text.strip() if desc_tag else "Pas de description"

        stars_tag = article.select_one('span.d-inline-block.float-sm-right')
        stars_text = stars_tag.text.strip() if stars_tag else "0 stars"

        # Filtrage par mots-clés
        text_to_check = (repo_name + " " + repo_desc).lower()
        is_relevant = any(keyword in text_to_check for keyword in TARGET_KEYWORDS)

        if is_relevant:
            repos.append({
                "name": repo_name,
                "url": repo_url,
                "desc": repo_desc,
                "stars": stars_text
            })

    return repos

def main():
    print("Recherche des pépites GitHub ciblées...")
    repos = get_github_trending()

    if not repos:
        message = "🔍 *GitHub Business Gems* \nAujourd'hui, aucun repo tendance ne correspond à tes critères. On retente demain !"
    else:
        message = "🔥 *GitHub Business Gems (Sélection Ciblée)*\n\n"
        for i, repo in enumerate(repos[:5], 1):
            message += f"*{i}. {repo['name']}* ({repo['stars']})\n"
            message += f"{repo['desc']}\n"
            message += f"👉 {repo['url']}\n\n"

    send_telegram_message(message)

if __name__ == "__main__":
    main()
