# anthropic-engineering-feed

Atom feed for <https://www.anthropic.com/engineering>

Publishes an Atom feed at https://ryan-serpico.github.io/anthropic-engineering-feed/atom.xml

If you just want the most recent 20 items (as opposed to all items) use this feed instead: https://ryan-serpico.github.io/anthropic-engineering-feed/atom-recent-20.xml

## About

This project automatically scrapes Anthropic's engineering blog and converts it to Atom feeds using:

- GitHub Actions for scheduled daily scraping (6:26 AM UTC)
- GitHub Pages for free CDN-backed hosting
- BeautifulSoup + lxml for HTML parsing

Inspired by [simonw/ollama-models-atom-feed](https://github.com/simonw/ollama-models-atom-feed)

## Local Development

### Using uv (recommended - faster)

1. Install [uv](https://docs.astral.sh/uv/):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Run the scraper (uv will automatically handle dependencies):

```bash
uv run --with click --with beautifulsoup4 --with requests --with lxml python scrape_anthropic_blog.py 'https://www.anthropic.com/engineering'
```

Or test with a local HTML file:

```bash
uv run --with click --with beautifulsoup4 --with requests --with lxml python scrape_anthropic_blog.py file:///path/to/saved-page.html
```

### Using pip (traditional)

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the scraper:

```bash
python scrape_anthropic_blog.py 'https://www.anthropic.com/engineering'
```

Or test with a local HTML file:

```bash
python scrape_anthropic_blog.py file:///path/to/saved-page.html
```

## Setup

1. Fork this repository
2. Enable GitHub Pages in Settings → Pages → Source: Deploy from branch (main)
3. Wait for the first GitHub Action to run (or trigger manually)
4. Subscribe to your feeds at:
   - Full feed: `https://[your-username].github.io/anthropic-engineering-feed/atom.xml`
   - Recent 20: `https://[your-username].github.io/anthropic-engineering-feed/atom-recent-20.xml`
