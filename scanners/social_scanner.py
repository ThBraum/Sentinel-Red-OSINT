import aiohttp
from bs4 import BeautifulSoup
import re
import json


def _meta_content(soup: BeautifulSoup, *, name: str | None = None, prop: str | None = None) -> str | None:
    if name is not None:
        tag = soup.find("meta", {"name": name})
        if tag and tag.get("content"):
            return str(tag.get("content")).strip()
    if prop is not None:
        tag = soup.find("meta", property=prop)
        if tag and tag.get("content"):
            return str(tag.get("content")).strip()
    return None


def _looks_generic(display_name: str, *, platform: str, username: str) -> bool:
    s = (display_name or "").strip()
    if not s:
        return True

    s_low = s.lower()
    user = username.strip().lstrip("@").strip()
    handle_low = f"@{user}".lower()

    # Se já é o handle, não é genérico.
    if s_low == user.lower() or s_low == handle_low:
        return False

    # Títulos/strings claramente genéricas (home/login/taglines).
    generic_exact = {
        "instagram",
        "tiktok",
        "facebook",
        "reddit",
        "github",
        "log in",
        "login",
        "sign up",
        "make your day",
        "tiktok - make your day",
        "reddit - the heart of the internet",
        "reddit: the heart of the internet",
    }
    if s_low in generic_exact:
        return True

    # Páginas de login/bloqueio costumam conter essas palavras.
    if any(k in s_low for k in ["log in", "login", "sign up", "entre", "entrar", "cadastre", "crie uma conta"]):
        return True

    # Alguns meta/titles incluem o nome da plataforma junto, mas isso não deveria invalidar um nome real.
    # Consideramos genérico se a string é curta e contém só branding.
    branding = platform.lower()
    if branding in s_low and len(s_low) <= max(18, len(branding) + 5):
        return True

    return False

async def scan_social_real(username: str):
    sites = {
        "Instagram": f"https://www.instagram.com/{username}/",
        "TikTok": f"https://www.tiktok.com/@{username}",
        "GitHub": f"https://github.com/{username}",
        "Facebook": f"https://www.facebook.com/{username}",
        "Reddit": f"https://www.reddit.com/user/{username}",
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8"
    }
    
    found_socials = []
    
    async with aiohttp.ClientSession(headers=headers) as session:
        for name, url in sites.items():
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Fallback: usar o handle (evita títulos genéricos do site)
                        clean_user = username.strip().lstrip("@").strip()
                        display_name = f"@{clean_user}" if clean_user else username

                        # 1) Preferir metatags de título (og/twitter) quando disponíveis
                        og_title = _meta_content(soup, prop="og:title")
                        tw_title = _meta_content(soup, name="twitter:title")
                        page_title = (soup.title.string.strip() if soup.title and soup.title.string else None)
                        candidate_title = next((t for t in [og_title, tw_title, page_title] if t and t.strip()), None)

                        # 2) Preferir descrição (onde plataformas frequentemente expõem nome/handle)
                        meta_desc = _meta_content(soup, name="description") or _meta_content(soup, prop="og:description")
                        content = meta_desc or ""

                        # Extrações por plataforma
                        if name == "Instagram" and content:
                            # Ex: "Alisson Foratto (@alisson) • Instagram photos" -> Alisson Foratto
                            match = re.search(r"^(.*?)\s*\(@", content)
                            if match and match.group(1).strip():
                                display_name = match.group(1).strip()

                        elif name == "TikTok" and content:
                            # Ex: "Assista ao vídeo mais recente de Alisson (@alisson)" -> Alisson
                            match = re.search(r"(?:de |from )(.*?)\s*\(@", content, flags=re.IGNORECASE)
                            if match and match.group(1).strip():
                                display_name = match.group(1).strip()

                        elif name == "Facebook" and content:
                            # Ex: "Alisson Foratto está no Facebook" -> Alisson Foratto
                            display_name = content.split(" está no ")[0].split(" is on ")[0].strip() or display_name

                        elif name == "Reddit":
                            # Muitas páginas retornam título/descrição genéricos; ao menos preservamos o handle.
                            # Se houver referência do tipo u/XYZ, usamos isso como handle.
                            blob = " ".join([c for c in [content, candidate_title] if c])
                            match = re.search(r"\bu/([A-Za-z0-9_-]{2,32})\b", blob)
                            if match:
                                display_name = f"@{match.group(1)}"

                        # 3) Se a extração ficou genérica, tente limpar o título; senão, caia no handle
                        if _looks_generic(display_name, platform=name, username=clean_user) and candidate_title:
                            t = candidate_title
                            # Limpezas comuns
                            t = re.sub(r"\s*[•|\-|–].*$", "", t).strip()
                            t = re.sub(r"\s*\(@[^)]+\)\s*", " ", t).strip()
                            t = re.sub(r"\s+on\s+TikTok\b.*$", "", t, flags=re.IGNORECASE).strip()
                            if t and not _looks_generic(t, platform=name, username=clean_user):
                                display_name = t

                        if _looks_generic(display_name, platform=name, username=clean_user):
                            display_name = f"@{clean_user}" if clean_user else username

                        found_socials.append({
                            "platform": name,
                            "url": str(response.url),
                            "profile_name": display_name
                        })
            except:
                continue
    return found_socials