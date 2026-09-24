# Starter list of tracked sources. Adjust freely -- add/remove brands, and
# fix scrape_config selectors by inspecting each site's actual HTML (they're
# unverified placeholders below, marked with TODO).

SOURCES = [
    {
        "name": "H&M",
        "category": "fashion",
        "website_url": "https://www2.hm.com/en_us/sale/viewall.html",
        "gmail_sender_pattern": "@email.hm.com",
        "scrape_config": {
            # TODO: verify selectors against live HTML -- H&M renders listings
            # client-side, so this will likely need Playwright instead of
            # plain requests+BeautifulSoup.
            "list_selector": "li.product-item",
            "title_selector": ".product-item-headline",
            "url_selector": "a",
            "discount_selector": ".price-value",
            "base_url": "https://www2.hm.com",
        },
    },
    {
        "name": "Oh Polly",
        "category": "fashion",
        "website_url": "https://www.ohpolly.com/collections/sale",
        "gmail_sender_pattern": "@ohpolly.com",
        "scrape_config": {
            # Verified against the live sale page on 2026-09-07.
            "list_selector": "product-card",
            "title_selector": ".prd-Card_Title",
            "url_attr": "data-product-url",
            "discount_attr": "data-product-price",
            "base_url": "https://www.ohpolly.com",
        },
    },
    {
        "name": "The Ordinary",
        "category": "skincare",
        "website_url": "https://theordinary.com/en-us",
        "gmail_sender_pattern": "@theordinary.com",
        "scrape_config": {
            # Verified against the live page on 2026-09-09. Note: each tile
            # has two elements with class "product-link" -- an image link
            # with no text, and a text link inside h2.pdp-link -- so the
            # title/url selector must target the latter specifically or
            # select_one() silently grabs the empty one.
            "list_selector": "div.product-grid-item",
            "title_selector": "h2.pdp-link a",
            "url_selector": "h2.pdp-link a",
            "discount_selector": ".product-prices .value",
            "base_url": "https://theordinary.com",
        },
    },
    {
        "name": "Glossier",
        "category": "skincare",
        "website_url": "https://www.glossier.com/collections/skincare",
        "gmail_sender_pattern": "@glossier.com",
        "scrape_config": {
            # Verified against the live page on 2026-09-09. Note: the
            # obvious ".variant-card" listing is per size/color variant, not
            # per product (e.g. two cards both titled just "177 mL" for the
            # same cleanser) -- the real per-product listing with clean
            # names lives in the shades-picker markup instead.
            "list_selector": "li.collection__shades-item",
            "title_selector": "h4.collection__shades-title",
            "url_selector": ".collection__shades-header a",
            "base_url": "https://www.glossier.com",
        },
    },
    {
        "name": "CeraVe",
        "category": "skincare",
        "website_url": "https://www.cerave.com/skincare/new-products",
        "gmail_sender_pattern": "@cerave.com",
        "scrape_config": {
            # Verified against the live "new products" page on 2026-09-09.
            "list_selector": "li.results-grid__item",
            "title_selector": ".front__title h3",
            "url_selector": "a.results__card-front",
            "base_url": "https://www.cerave.com",
        },
    },
    {
        "name": "Sephora",
        "category": "skincare",
        "website_url": "https://www.sephora.com/shop/skin-care-sale",
        "gmail_sender_pattern": "@sephora.com",
        "scrape_config": {
            # BLOCKED as of 2026-09-09: Sephora returns 403 with
            # `server: AkamaiGHost` on plain requests -- this is Akamai bot
            # detection, not just JS rendering, and plain requests+BS4 can't
            # get past it at all. Seeded as a placeholder for whenever a
            # headless-browser engine (e.g. Playwright, ideally with stealth
            # plugins) is added as a per-source fallback.
            "list_selector": "li.product-item",
            "title_selector": ".product-item__title",
            "url_selector": "a",
            "discount_selector": ".price__sale",
            "base_url": "https://www.sephora.com",
        },
    },
    {
        "name": "Zara",
        "category": "fashion",
        "website_url": "https://www.zara.com/us/en/woman-sale-l1108.html",
        "gmail_sender_pattern": "@zara.com",
        "scrape_config": {
            # BLOCKED as of 2026-09-09: Zara serves an Akamai interstitial
            # proof-of-work JS challenge to plain requests -- needs a real
            # browser (Playwright) to get past it.
            "list_selector": "li.product-item",
            "title_selector": ".product-item__title",
            "url_selector": "a",
            "discount_selector": ".price__sale",
            "base_url": "https://www.zara.com",
        },
    },
    {
        "name": "Shein",
        "category": "fashion",
        "website_url": "https://www.shein.com/Women-Sale-c-2151.html",
        "gmail_sender_pattern": "@shein.com",
        "scrape_config": {
            # BLOCKED as of 2026-09-09: redirects to a CAPTCHA challenge
            # page (risk/challenge) for plain requests.
            "list_selector": "li.product-item",
            "title_selector": ".product-item__title",
            "url_selector": "a",
            "discount_selector": ".price__sale",
            "base_url": "https://www.shein.com",
        },
    },
    {
        "name": "Urban Outfitters",
        "category": "fashion",
        "website_url": "https://www.urbanoutfitters.com/sale-womens-clothing",
        "gmail_sender_pattern": "@urbanoutfitters.com",
        "scrape_config": {
            # BLOCKED as of 2026-09-09: flat 403 on plain requests, even
            # with full browser-like headers.
            "list_selector": "li.product-item",
            "title_selector": ".product-item__title",
            "url_selector": "a",
            "discount_selector": ".price__sale",
            "base_url": "https://www.urbanoutfitters.com",
        },
    },
    {
        "name": "Victoria's Secret",
        "category": "fashion",
        "website_url": "https://www.victoriassecret.com/vs/sale",
        "gmail_sender_pattern": "@victoriassecret.com",
        "scrape_config": {
            # BLOCKED as of 2026-09-09: Cloudflare bot-challenge page
            # ("Attention Required!") on plain requests, even with full
            # browser-like headers -- needs a real browser to get past it.
            "list_selector": "li.product-item",
            "title_selector": ".product-item__title",
            "url_selector": "a",
            "discount_selector": ".price__sale",
            "base_url": "https://www.victoriassecret.com",
        },
    },
]
