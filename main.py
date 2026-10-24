import os
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

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

        repos.append({
            "name": repo_name,
            "url": repo_url,
            "desc": repo_desc,
            "stars": stars_text
        })

    return repos

def evaluate_with_jev(repo_text):
    """Interroge Jev via OpenRouter pour scorer le repo"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    Analyse ce projet GitHub et réponds par un score de pertinence entre 0 et 100 pour un business spécialisé en IA, automatisation, SaaS et API.
    Projet : {repo_text}
    Donne uniquement le score numérique (ex: 95).
    """
    
    payload = {
        "model": "typesafe/jev-1.14",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        res_json = response.json()
        print(f"Réponse brute OpenRouter/Jev : {res_json}") # <-- DEBUG ICI
        
        score_text = res_json['choices'][0]['message']['content'].strip()
        score = int(''.join(filter(str.isdigit, score_text)))
        return score
    except Exception as e:
        print(f"Erreur Jev/OpenRouter: {e} - Réponse complète : {response.text}")
        return 0  # On met 0 pour voir s'il y a une erreur

def main():
    print("Recherche et analyse des pépites avec Jev...")
    repos = get_github_trending()
    
    scored_repos = []
    for repo in repos:
        combined_text = f"{repo['name']} : {repo['desc']}"
        score = evaluate_with_jev(combined_text)
        repo['score'] = score
        # On ne garde que ceux qui ont un score supérieur à 60 par exemple
        if score >= 60:
            scored_repos.append(repo)

    # Tri par score du plus haut au plus bas
    scored_repos = sorted(scored_repos, key=lambda x: x['score'], reverse=True)

    if not scored_repos:
        message = "🔍 *GitHub Business Gems (Jev)* \nAucun repo pertinent trouvé pour ce run."
    else:
        message = "🔥 *GitHub Business Gems (Noté par Jev)*\n\n"
        for i, repo in enumerate(scored_repos[:12], 1):
            message += f"*{i}. {repo['name']}* (Score Jev: {repo['score']}/100 - {repo['stars']})\n"
            message += f"{repo['desc']}\n"
            message += f"👉 {repo['url']}\n\n"

    send_telegram_message(message)

if __name__ == "__main__":
    main()
