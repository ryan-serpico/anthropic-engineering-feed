# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a GitHub Actions-powered web scraper that converts Anthropic's engineering blog (https://www.anthropic.com/engineering) into Atom feeds. It uses GitHub Pages for free CDN-backed hosting and runs automatically every 6 hours.

**Architecture Pattern**: Scraper → Static Feed Generator → Git-based Storage → GitHub Pages CDN

Inspired by simonw/ollama-models-atom-feed.

## Key Architecture Decisions

### Dual Feed Generation
The scraper generates two feeds from a single parse:
- `atom.xml` - Full feed with all articles
- `atom-recent-20.xml` - Recent 20 articles only

This is accomplished via the **deep copy pattern** in `save_atom_feed()` (line 119 in scrape_anthropic_blog.py) which allows reusing the base feed structure without mutation.

### HTML Scraping Selectors
Target CSS classes specific to Anthropic's blog structure:
- Articles: `article.ArticleList_article__LIMds`
- Titles: `h2` or `h3` with class `bold`
- Dates: `div.ArticleList_date__2VTRg` (format: "Sep 29, 2025")
- Summary: `p.ArticleList_summary__G96cV`
- Links: `a.ArticleList_cardLink__VWIzl`

If Anthropic changes their CSS classes, update the selectors in `create_base_feed_and_entries()`.

### Date Handling
Dates are parsed from "Sep 29, 2025" format and set to noon UTC for consistency. Articles without dates default to current time. Entries are sorted by date (most recent first) before feed generation.

## Running the Scraper

### With uv (preferred - matches CI)
```bash
uv run --with click --with beautifulsoup4 --with requests --with lxml python scrape_anthropic_blog.py 'https://www.anthropic.com/engineering'
```

### With pip
```bash
pip install -r requirements.txt
python scrape_anthropic_blog.py 'https://www.anthropic.com/engineering'
```

### Test with local HTML
```bash
python scrape_anthropic_blog.py file:///path/to/sample.html
```

The script accepts either HTTP(S) URLs or `file://` paths for local testing.

## GitHub Actions Workflow

Located at `.github/workflows/scrape.yml`

**Schedule**: Every 6 hours at 26 minutes past the hour (0:26, 6:26, 12:26, 18:26 UTC)

**Performance Optimization**: Uses `uv` instead of `pip` for 10-100x faster dependency installation with automatic caching via `astral-sh/setup-uv@v5`.

**Auto-commit Pattern**: Scraper outputs are committed and pushed automatically. Uses `git pull --rebase` before push to handle concurrent runs.

To trigger manually:
```bash
gh workflow run scrape.yml
```

## Modifying the Scraper

If Anthropic's blog HTML structure changes:

1. Download a sample page: `curl https://www.anthropic.com/engineering > sample.html`
2. Update CSS selectors in `create_base_feed_and_entries()` (lines 52-103)
3. Test locally: `python scrape_anthropic_blog.py file://$(pwd)/sample.html`
4. Verify both `atom.xml` and `atom-recent-20.xml` are generated correctly
5. Commit changes - workflow will use updated selectors on next run

## GitHub Pages Deployment

Feeds are published at:
- https://ryan-serpico.github.io/anthropic-engineering-feed/atom.xml
- https://ryan-serpico.github.io/anthropic-engineering-feed/atom-recent-20.xml

GitHub Pages automatically deploys from the `main` branch after each commit. The workflow commits generated XML files which triggers the deployment.

## Dependencies

- **click**: CLI argument parsing
- **beautifulsoup4**: HTML parsing
- **requests**: HTTP fetching
- **lxml**: Fast HTML parser + XML pretty printing

All dependencies are specified in `requirements.txt`.
