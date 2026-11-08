import re
from threading import Timer
from urllib.parse import parse_qs, quote_plus, urlparse
import webbrowser

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request


app = Flask(__name__)
PROVIDERS = {
	"google": {"name": "Google", "url": "https://www.google.com/search", "browser_url": "https://www.google.com/search"},
	"bing": {"name": "Bing", "url": "https://www.bing.com/search", "browser_url": "https://www.bing.com/search"},
	"duckduckgo": {"name": "DuckDuckGo", "url": "https://html.duckduckgo.com/html/", "browser_url": "https://duckduckgo.com/"},
}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"}
SENSITIVE_TERMS = re.compile(r"\b(passwords?|credentials?|access tokens?|api keys?|private accounts?)\b", re.I)


def clean_text(value: str) -> str | None:
	text = " ".join(value.split())
	if re.search(r"[:<>]", text):
		return None
	return text


def normalize_domain(value: str) -> str | None:
	if not value.strip():
		return ""
	raw = value.strip()
	if any(char.isspace() for char in raw):
		return None
	parsed = urlparse(raw if "://" in raw else f"https://{raw}")
	host = (parsed.hostname or "").lower().rstrip(".")
	if not host or "." not in host or not re.fullmatch(r"[a-z0-9.-]+", host):
		return None
	if ".." in host or host.startswith(".") or host.endswith("."):
		return None
	return host


def build_query(target: str, condition: str, domain: str) -> str:
	parts = [target]
	if condition:
		parts.append(f'"{condition}"')
	if domain:
		parts.append(f"site:{domain}")
	return " ".join(parts)


def _public_result_url(href: str) -> str | None:
	if href.startswith("//"):
		href = f"https:{href}"
	parsed = urlparse(href)
	if parsed.hostname and parsed.hostname.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
		destinations = parse_qs(parsed.query).get("uddg", [])
		if destinations:
			href = destinations[0]
	parsed = urlparse(href)
	if parsed.scheme not in {"http", "https"} or not parsed.hostname:
		return None
	return href


def _extract_google(soup: BeautifulSoup) -> list[dict[str, str]]:
	blocks = soup.select("div.MjjYud")
	results = []
	for block in blocks:
		heading = block.find("h3")
		link = heading.find_parent("a") if heading else None
		url = _public_result_url(link.get("href", "")) if link else None
		if not heading or not url:
			continue
		snippet = block.select_one(".VwiC3b, .yXK7lf")
		results.append({"title": heading.get_text(" ", strip=True), "url": url, "snippet": snippet.get_text(" ", strip=True) if snippet else ""})
	return results


def _extract_bing(soup: BeautifulSoup) -> list[dict[str, str]]:
	results = []
	for block in soup.select("li.b_algo"):
		link = block.select_one("h2 a")
		url = _public_result_url(link.get("href", "")) if link else None
		if not link or not url:
			continue
		snippet = block.select_one(".b_caption p")
		results.append({"title": link.get_text(" ", strip=True), "url": url, "snippet": snippet.get_text(" ", strip=True) if snippet else ""})
	return results


def _extract_duckduckgo(soup: BeautifulSoup) -> list[dict[str, str]]:
	results = []
	for block in soup.select(".result"):
		link = block.select_one("a.result__a")
		url = _public_result_url(link.get("href", "")) if link else None
		if not link or not url:
			continue
		snippet = block.select_one(".result__snippet")
		results.append({"title": link.get_text(" ", strip=True), "url": url, "snippet": snippet.get_text(" ", strip=True) if snippet else ""})
	return results


def search_public_results(provider_id: str, query: str, target: str, condition: str) -> list[dict[str, str]]:
	provider = PROVIDERS[provider_id]
	response = requests.get(provider["url"], params={"q": query}, headers=HEADERS, timeout=12)
	response.raise_for_status()
	soup = BeautifulSoup(response.text, "html.parser")
	extractors = {"google": _extract_google, "bing": _extract_bing, "duckduckgo": _extract_duckduckgo}
	results = extractors[provider_id](soup)
	target_words = {word.lower() for word in re.findall(r"[a-z0-9]+", target.lower()) if len(word) > 2}
	condition_words = {word.lower() for word in re.findall(r"[a-z0-9]+", condition.lower()) if len(word) > 2}
	filtered = []
	for result in results:
		content = f"{result['title']} {result['snippet']} {result['url']}".lower()
		if target_words and not any(word in content for word in target_words):
			continue
		if condition_words and not any(word in content for word in condition_words):
			continue
		filtered.append(result)
	return filtered[:10]


def search_with_fallback(provider_id: str, query: str, target: str, condition: str) -> tuple[list[dict[str, str]], str | None]:
	providers = [provider_id]
	if provider_id != "duckduckgo":
		providers.append("duckduckgo")
	for candidate in providers:
		try:
			results = search_public_results(candidate, query, target, condition)
		except requests.RequestException:
			continue
		if results:
			return results, candidate
	return [], None


def render_page(**context):
	defaults = {
		"providers": PROVIDERS,
		"selected_provider": "google",
		"raw_query": "",
		"target": "",
		"condition": "",
		"domain": "",
		"search_query": None,
		"search_url": None,
		"provider_name": "",
		"results": [],
		"error": None,
	}
	defaults.update(context)
	return render_template("index.html", **defaults)


@app.get("/")
def home():
	return render_page()


@app.post("/search")
def search():
	target = clean_text(request.form.get("target", ""))
	condition = clean_text(request.form.get("condition", ""))
	domain = normalize_domain(request.form.get("domain", ""))
	provider_id = request.form.get("provider", "google")
	error = None
	search_query = None
	results = []

	if provider_id not in PROVIDERS:
		provider_id = "google"
	requested_provider_id = provider_id
	search_url = None
	if not target or target is None or condition is None or domain is None:
		error = "Enter a target and plain-text conditions, with an optional valid domain."
	elif SENSITIVE_TERMS.search(f"{target} {condition}"):
		error = "Searches for credentials or private account access are not supported."
	else:
		search_query = build_query(target, condition, domain)
		search_url = f"{PROVIDERS[requested_provider_id]['browser_url']}?q={quote_plus(search_query)}"
		results, result_provider = search_with_fallback(provider_id, search_query, target, condition)
		if result_provider is None:
			error = "Search providers returned no readable public results. Try another provider or search again later."
		elif result_provider != provider_id:
			provider_id = result_provider
			error = f"Showing {PROVIDERS[result_provider]['name']} results because the selected provider did not return readable results."

	return render_page(
		target=request.form.get("target", ""),
		condition=request.form.get("condition", ""),
		domain=request.form.get("domain", ""),
		raw_query=request.form.get("target", ""),
		selected_provider=requested_provider_id,
		provider_name=PROVIDERS[provider_id]["name"],
		search_query=search_query,
		search_url=search_url,
		results=results,
		error=error,
	)


def main() -> None:
	url = "http://127.0.0.1:5000"
	Timer(1, lambda: webbrowser.open_new_tab(url)).start()
	app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
	main()
