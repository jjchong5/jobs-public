# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: Built/scaled Greenhouse board scraper (2026-07-03 build + company-list scaling; 2026-07-05 bugfix) -- see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-greenhousepy for full text
# Usage: Greenhouse job-board scraper built, then scaled from an initial company list to 248 boards across multiple discovery passes, plus a 2026-07-05 bug fix and 3-company addition.
# -------------------------------------------------------------------------

"""Greenhouse job board scraper (public per-company JSON API).

Greenhouse exposes a public, unauthenticated JSON API per company at
`https://boards-api.greenhouse.io/v1/boards/<board_token>/jobs` -- no auth, no
anti-bot, one HTTP GET per company. There is no cross-company search, so this
needs a target company list (`BOARD_TOKENS` below), unlike single-board
sources like Built In SF.

`BOARD_TOKENS` is a placeholder list of SF AI/DS/ML companies confirmed live
against the real API (2026-07-02) -- same spirit as the seeded default
preference profile: a reasonable starting set, not an exhaustively curated
"right" list. Don't block on expanding it; add tokens as they come up.

Standalone run:
    python -m pipeline.scrapers.greenhouse
writes raw entries to data/raw/greenhouse.json and prints the count fetched.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests


from pipeline.scrapers.raw_writer import write_raw_output
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BOARDS_API_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"

# Confirmed live (2026-07-02) -- each of these board tokens returned >0 real
# jobs from the public API. Placeholder list, refine later.
BOARD_TOKENS = [
    "anthropic",
    "scaleai",
    "databricks",
    "airtable",
    "figma",
    "brex",
    "gusto",
    "asana",
    "affirm",
    "robinhood",
    "instacart",
    "coinbase",
    "stripe",
    "discord",
    # Added 2026-07-03: AI/ML/DS-native companies, probed live against ~90
    # candidate slugs (job counts confirmed >0 at probe time). This platform
    # has no cross-company search -- unlike VC-portfolio/aijobs.net "fuller
    # fetch" means "more companies", not more pages/keywords per company.
    "abnormalsecurity",  # 63 jobs -- Abnormal Security, AI-based email security
    "arizeai",           # 39 jobs -- Arize AI, ML observability
    "assemblyai",        # 4 jobs  -- AssemblyAI, speech-to-text AI
    "fireworksai",       # 33 jobs -- Fireworks AI, LLM inference platform
    "imbue",             # 3 jobs  -- Imbue, AI agents research
    "inflectionai",      # 5 jobs  -- Inflection AI, foundation models
    "labelbox",          # 14 jobs -- Labelbox, ML data labeling
    "snorkelai",         # 47 jobs -- Snorkel AI, weak-supervision data labeling
    "stabilityai",       # 1 job   -- Stability AI, generative AI
    "togetherai",        # 57 jobs -- Together AI, AI inference/training infra
    "vannevarlabs",      # 31 jobs -- Vannevar Labs, AI/defense-tech
    "xai",               # 214 jobs -- xAI, foundation models
    # Added 2026-07-03 (full-volume pass): probed ~196 more candidate slugs
    # live (foundation-model labs, AI infra/tooling, applied-AI verticals,
    # data/analytics platforms, security, general SF tech), 64 resolved with
    # jobs -- these 41 are the ones not already covered above. Includes some
    # non-AI-native general SF tech (roblox, twitch, lyft, checkr, etc.) on
    # the same "downstream tagger filters relevance" division of labor as the
    # rest of this list -- not newly curated for AI-fit.
    "mongodb",            # 398 jobs
    "coreweave",          # 278 jobs -- GPU cloud infra
    "graphcore",          # 251 jobs -- AI accelerator chips
    "cloudflare",         # 233 jobs
    "roblox",             # 231 jobs
    "airbnb",             # 223 jobs
    "elastic",            # 202 jobs
    "reddit",             # 191 jobs
    "pinterest",          # 187 jobs
    "clickhouse",         # 166 jobs
    "lyft",               # 156 jobs
    "gitlab",             # 145 jobs
    "fivetran",           # 131 jobs
    "tenstorrent",        # 123 jobs -- AI accelerator chips
    "netskope",           # 106 jobs
    "cresta",             # 104 jobs -- applied conversational AI
    "sigmacomputing",     # 70 jobs
    "vercel",             # 66 jobs
    "chime",              # 64 jobs
    "twitch",             # 64 jobs
    "hightouch",          # 63 jobs
    "mercury",            # 54 jobs
    "checkr",             # 52 jobs
    "amplitude",          # 48 jobs
    "singlestore",        # 47 jobs
    "mixpanel",           # 37 jobs
    "cockroachlabs",      # 36 jobs
    "eve",                # 31 jobs -- legal AI
    "isomorphiclabs",     # 22 jobs -- AI drug discovery (Alphabet spinout)
    "heygen",             # 20 jobs -- generative AI video
    "blackforestlabs",    # 15 jobs -- generative AI (Flux image models)
    "observeai",          # 15 jobs -- applied conversational AI
    "generatebiomedicines",  # 14 jobs -- AI drug discovery
    "planetscale",        # 12 jobs
    "galileo",            # 11 jobs -- ML observability
    "invisibletech",      # 10 jobs -- AI-enabled BPO
    "pathai",             # 9 jobs -- AI pathology
    "suki",               # 7 jobs -- AI clinical documentation
    "dremio",             # 6 jobs
    "vectara",            # 6 jobs -- RAG/vector search platform
    "comet",              # 4 jobs -- ML experiment tracking
    # Added 2026-07-03 (company-name discovery pass): rather than continuing
    # to hand-guess candidate slugs, derived candidates from the 436 distinct
    # company names already sitting in the DB from yc_workatastartup and
    # vc_portfolio (name -> slug via lowercase/dash/no-space + common
    # suffix-stripping variants, e.g. "Anduril Industries" ->
    # "andurilindustries"). Closes real company-*coverage* gaps that
    # hand-guessing missed, not just adding more probe attempts. 621
    # candidate slugs probed live, 91 resolved with jobs. Spot-checked
    # generic-word slugs before trusting them (flex/mill/hive/found/future/
    # fal/alloy/verse/paradigm/current) by inspecting real job titles -- all
    # consistent with their expected company. One rejected: "shield" (for
    # Shield AI) resolved to an unrelated GitHub Pages demo board, not a real
    # company board -- excluded.
    "andurilindustries",  # 2170 jobs -- Anduril Industries, defense tech
    "spacex",             # 1829 jobs
    "waymo",              # 384 jobs -- autonomous vehicles
    "verkada",            # 306 jobs
    "toast",              # 288 jobs
    "revolutionmedicines",  # 236 jobs
    "prolific",           # 174 jobs -- AI research participant platform
    "ripple",             # 156 jobs
    "aurorainnovation",   # 144 jobs -- autonomous trucking
    "epicgames",          # 127 jobs
    "helsing",            # 124 jobs -- AI/defense
    "grafanalabs",        # 107 jobs
    "catonetworks",       # 105 jobs
    "nuro",               # 94 jobs -- autonomous vehicles
    "upstart",            # 94 jobs -- AI lending
    "dialpad",            # 79 jobs -- AI-powered comms
    "bloomreach",         # 78 jobs -- AI commerce search
    "securityscorecard",  # 78 jobs
    "neuralink",          # 73 jobs
    "fireblocks",         # 59 jobs
    "cribl",              # 56 jobs
    "lightmatter",        # 56 jobs -- photonic AI chips
    "tanium",             # 53 jobs
    "flex",               # 52 jobs
    "thunes",             # 49 jobs
    "iterativehealth",    # 44 jobs -- AI healthcare
    "earnin",             # 43 jobs
    "forter",             # 41 jobs -- AI fraud prevention
    "komodohealth",       # 40 jobs -- AI healthcare data
    "everlaw",            # 39 jobs -- AI legal tech
    "fal",                # 39 jobs -- generative media infra
    "obsidiansecurity",   # 37 jobs
    "axonius",            # 33 jobs
    "pacificfusion",      # 32 jobs
    "koboldmetals",       # 31 jobs -- AI mineral exploration
    "midihealth",         # 28 jobs -- AI healthcare
    "shifttechnology",    # 28 jobs -- AI insurance
    "silananotechnologies",  # 28 jobs
    "kalshi",             # 27 jobs
    "hextechnologies",    # 26 jobs -- AI data science platform
    "omadahealth",        # 26 jobs
    "shopmy",             # 26 jobs
    "goodfire",           # 25 jobs -- AI interpretability research
    "hover",              # 25 jobs
    "pindropsecurity",    # 25 jobs -- voice AI security
    "dashlane",           # 24 jobs
    "formationbio",       # 24 jobs -- AI drug development
    "onxmaps",            # 24 jobs
    "doppel",             # 23 jobs -- AI brand protection
    "qventus",            # 22 jobs -- AI healthcare ops
    "forwardnetworks",    # 19 jobs
    "nextdoor",           # 19 jobs
    "scandit",            # 19 jobs -- computer vision
    "typeface",           # 19 jobs -- generative AI content
    "alloy",              # 18 jobs
    "cultureamp",         # 18 jobs
    "layerhealth",        # 18 jobs -- AI healthcare data
    "freenome",           # 17 jobs -- AI cancer detection
    "honor",              # 17 jobs
    "newsela",            # 17 jobs
    "truecaller",         # 17 jobs
    "melio",              # 16 jobs
    "wildlifestudios",    # 16 jobs
    "censys",             # 15 jobs
    "mill",               # 14 jobs
    "hive",               # 13 jobs -- AI data labeling/content moderation
    "worldlabs",          # 13 jobs -- spatial AI (Fei-Fei Li's company)
    "motive",             # 12 jobs
    "novacredit",         # 12 jobs
    "verse",              # 12 jobs
    "waymark",            # 9 jobs -- generative AI video ads
    "collectivehealth",   # 8 jobs
    "incognia",           # 8 jobs
    "nuancelabs",         # 8 jobs
    "offerup",            # 8 jobs
    "descript",           # 7 jobs -- AI video/audio editing
    "enterpret",          # 6 jobs -- AI customer feedback analysis
    "translucent",        # 6 jobs -- AI (Translucent AI)
    "found",              # 5 jobs
    "future",             # 5 jobs -- AI personal training
    "newtonresearch",     # 5 jobs
    "oasishealthpartners",  # 5 jobs
    "syndio",             # 5 jobs
    "apiiro",             # 4 jobs
    "hungryroot",         # 3 jobs
    "boldmetrics",        # 2 jobs
    "paradigm",           # 2 jobs
    "current",            # 1 job
    "profound",           # 1 job -- AI search/answer engine optimization
    "traderepublic",      # 1 job
    # Added 2026-07-03 (YC public directory pass): pulled all 6,004 YC
    # portfolio companies from ycombinator.com/companies' public Algolia
    # index (window.AlgoliaOpts in the page's HTML -- a search-only key
    # scoped to public company data, paginated past its 1000-result cap by
    # querying per-batch via facetFilters). Derived slug candidates from
    # company names not already represented in the DB (via
    # yc_workatastartup/vc_portfolio/greenhouse/lever/ashby/aijobs_net),
    # excluding tokens already in this list -- 4,428 candidates probed live,
    # 154 resolved with jobs. Many short/generic-word slugs (pulse, agency,
    # clara, axle, camp, radar, flip, symphony, mesh, guild, array, etc.)
    # collided with unrelated companies of the same board-token name --
    # verified each hit's actual job titles/locations against the YC
    # company's stated one_liner/location before trusting it (63 of 154
    # rejected on this basis, e.g. "clara" resolved to a Brazil/Mexico
    # accounts-payable fintech, not YC's SF-based "AI primary care doctor").
    # These 91 passed that check.
    "flexport",              # 128 jobs -- Flexport, Platform for global logistics.
    "billiontoone",          # 105 jobs -- BillionToOne, The genetic testing platform detecting and measuring disease.
    "astranis",              # 87 jobs -- Astranis, Advanced satellites for high orbits.
    "faire",                 # 79 jobs -- Faire, The global online platform empowering independent retail.
    "humaninterest",         # 65 jobs -- Human Interest, The 401(k) for small and medium-sized businesses.
    "oklo",                  # 58 jobs -- Oklo, Emission free, always on power from advanced fission power plants.
    "inversionspace",        # 57 jobs -- Inversion Space, Turning space into a transportation layer for Earth
    "instawork",             # 53 jobs -- Instawork, A flexible work app that connects businesses with hourly workers.
    "dropbox",               # 51 jobs -- Dropbox, Backup and share files in the cloud.
    "alpaca",                # 50 jobs -- Alpaca, API-first stock and crypto brokerage platform
    "algolia",               # 44 jobs -- Algolia, A developer-friendly and enterprise-grade search API.
    "maymobility",           # 43 jobs -- May Mobility, Transforming cities and rural areas through AV transit and technology
    "pairteam",              # 43 jobs -- Pair Team, Building the safety net of the future
    "aclu",                  # 41 jobs -- ACLU, Defender of rights and liberties
    "hackerrank",            # 40 jobs -- HackerRank, Change the world to value skills over pedigree
    "apolloio",              # 39 jobs -- Apollo.io, Apollo is the foundation of your entire go-to-market strategy.
    "gocardless",            # 35 jobs -- GoCardless, We're building the world's bank payment network.
    "odeko",                 # 35 jobs -- Odeko, Our operations software makes it easier to run--and grow--your cafe
    "gigs",                  # 35 jobs -- Gigs, The OS for Embedded Telecom
    "nabis",                 # 34 jobs -- Nabis, Nabis is the largest licensed cannabis wholesale platform.
    "marqvision",            # 30 jobs -- MarqVision, IP operating software for brands and content companies
    "icarus",                # 24 jobs -- Icarus, Stratospheric birds for defense
    "pagerduty",             # 24 jobs -- PagerDuty, Real-time visibility into critical apps and services all in one place.
    "webflow",               # 22 jobs -- Webflow, Professional website design and publishing platform.
    "daybreakhealth",        # 21 jobs -- Daybreak Health, The first digital mental health system for youth
    "goatgroup",             # 20 jobs -- GOAT Group, Platform for the greatest products from the past, present and future.
    "radar",                 # 19 jobs -- RADAR, RADAR is building technology to completely transform the in-store retail experience
    "xendit",                # 19 jobs -- Xendit, Provides payment infrastructure for Southeast Asia
    "further",               # 19 jobs -- FurtherAI, AI Workforce for the Insurance Industry
    "pineparkhealth",        # 19 jobs -- Pine Park Health, We provide primary care in senior living communities.
    "sendbird",              # 18 jobs -- Sendbird, The AI agent that doesn't just support, it delights.
    "akidolabs",             # 18 jobs -- Akido Labs, Rebuilding healthcare with AI at the core
    "veriff",                # 17 jobs -- Veriff, AI-powered identity verification solution for fraud prevention.
    "modernhealth",          # 17 jobs -- Modern Health, A mental health benefits platform for employers.
    "mattermost",            # 17 jobs -- Mattermost, Secure Collaboration for Technical Teams
    "ophelia",               # 16 jobs -- Ophelia, Medication & support to beat opioid addiction from home
    "extend",                # 16 jobs -- Extend, Production-ready document processing
    "carrotfertility",       # 15 jobs -- Carrot Fertility, Customized fertility benefits for modern companies.
    "groww",                 # 15 jobs -- Groww, Making financial services simple, transparent and delightful.
    "swayable",              # 15 jobs -- Swayable, Swayable predicts consumer opinion and the impact of content
    "ginkgobioworks",        # 15 jobs -- Ginkgo Bioworks, Our mission is to make biology easier to engineer.
    "nanonets",              # 14 jobs -- NanoNets, Automatic Data Extraction
    "openwork",              # 14 jobs -- OpenWork, The open source alternative to Claude Cowork
    "focalsystems",          # 13 jobs -- Focal Systems, Building the Operating System for B&M Retail using Deep Learning
    "saltsecurity",          # 13 jobs -- Salt Security, Protects organizations from getting breached through their APIs.
    "affinity",              # 13 jobs -- Affinity, A compliance training platform built for regulated industries.
    "starcloud",             # 12 jobs -- Starcloud, Data centers in space
    "pelago",                # 12 jobs -- Pelago, The world's first digital clinic for substance use management
    "givecampus",            # 12 jobs -- GiveCampus, The fundraising platform for schools.
    "momentus",              # 12 jobs -- Momentus, The space infrastructure services company
    "lattice",               # 11 jobs -- Lattice, Modern people management platform.
    "generalproximity",      # 10 jobs -- General Proximity, The next generation of induced-proximity medicines.
    "onshore",               # 10 jobs -- Onshore, AI for corporate tax
    "carbonchain",           # 9 jobs -- CarbonChain, We help companies automate the accounting of their carbon emissions
    "superset",              # 9 jobs -- Superset, Building the platform for software factories
    "prodigal",              # 9 jobs -- Prodigal, Lending Intelligence Software
    "embrace",               # 8 jobs -- Embrace, Modern user-focused observability built on OpenTelemetry
    "bitmovin",              # 8 jobs -- Bitmovin, Powers OTT online video providers with video developer tools.
    "recidiviz",             # 7 jobs -- Recidiviz, Helping create a smaller, fairer, safer justice system
    "legalist",              # 7 jobs -- Legalist, Legal investment firm
    "hubblenetwork",         # 7 jobs -- Hubble Network, Bluetooth to Space
    "albedo",                # 7 jobs -- Albedo, Full-stack VLEO satellite missions
    "cortex",                # 6 jobs -- Cortex, Internal Developer Portal eliminating "developer tax"
    "outschool",             # 6 jobs -- Outschool, A live online learning platform that empowers kids ages 3-18.
    "lob",                   # 6 jobs -- Lob, Automation platform that transforms direct mail
    "zerocater",             # 6 jobs -- Zerocater, Revolutionizing how companies feed their employees
    "spaceium",              # 6 jobs -- Spaceium Inc, In-Space Refueling
    "ansabiotechnologies",   # 6 jobs -- Ansa Biotechnologies, Next-generation DNA synthesis using enzymes
    "postscript",            # 6 jobs -- Postscript, The SMS revenue platform for e-commerce merchants
    "sirum",                 # 5 jobs -- SIRUM, "match.com" for unused medicine
    "niraenergy",            # 5 jobs -- Nira Energy, Software to find the best sites for renewables on the electrical grid
    "enveritas",             # 5 jobs -- Enveritas, Verifies global supply chains for issues like child slavery
    "papa",                  # 5 jobs -- Papa, One-stop-shop for flexible family care
    "feanixbiotechnologies", # 4 jobs -- Feanix Biotechnologies, Farm Genetics Made Easy - Using DNA and Software
    "understoodcare",        # 4 jobs -- Understood Care, Healthcare personal assistants for Medicare patients.
    "poka",                  # 4 jobs -- Poka Labs, Helping industrial manufacturers win deals fast, at the right price.
    "submittable",           # 4 jobs -- Submittable, Launch, manage and measure social impact programs
    "roofr",                 # 3 jobs -- Roofr, Sales software for roofers -- aerial measurements + proposals
    "culturebiosciences",    # 3 jobs -- Culture Biosciences, We grow cells for biotech companies.
    "smartasset",            # 3 jobs -- SmartAsset, Marketplace connecting consumers to financial advisors
    "warp",                  # 3 jobs -- Warp, AI-native Employee Management Platform for High-Growth Companies
    "lucidbots",             # 2 jobs -- Lucid Bots, We build robots for dull, dirty, and dangerous jobs.
    "glide",                 # 2 jobs -- Glide, Glide turns spreadsheets into beautiful, intelligent apps.
    "seer",                  # 2 jobs -- Seer, Sell beyond the store.
    "usergems",              # 2 jobs -- UserGems, The AI Command Center for outbound and ABM
    "sfox",                  # 2 jobs -- SFOX, Crypto-currency trading platform.
    "navierai",              # 2 jobs -- Navier AI, Agent-Driven Engineering
    "baubap",                # 2 jobs -- Baubap, Smart micro financing for everyone
    "recall",                # 2 jobs -- Recall.ai, API to get recordings/transcripts/metadata from meetings
    "aon3d",                 # 1 job  -- AON3D, Additive Manufacturing with advanced materials
    "meruhealth",            # 1 job  -- Meru Health, An online provider for greater mental health
    # Added 2026-07-05 (coverage-gap sizing pass, docs/reports/coverage_gap_estimate_2026-07-04.md):
    "together-ai",           # 58 jobs -- Together AI, generative AI cloud platform
]


BOARD_FETCH_WORKERS = 20  # bounded pool -- each board is one independent GET,
                          # but firing all 248+ boards at once would be
                          # inconsiderate to Greenhouse's shared API


def _fetch_board(token: str) -> list[dict]:
    url = BOARDS_API_URL.format(token=token)
    logger.info("Fetching Greenhouse board: %s", token)
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    jobs = data.get("jobs", [])
    if not jobs:
        logger.warning("Greenhouse board %s returned 0 jobs", token)
    items = []
    for job in jobs:
        location = (job.get("location") or {}).get("name")
        items.append(
            {
                "title": job.get("title", ""),
                "company": token,
                "url": job.get("absolute_url", ""),
                "location": location,
                "updated_at": job.get("updated_at"),
                "content": job.get("content", ""),
                "source": "greenhouse",
            }
        )
    return items


def fetch_raw(board_tokens: list[str] = BOARD_TOKENS) -> list[dict]:
    """Fetch raw job postings from each Greenhouse board token.

    Returns a list of dicts with keys: title, company, url, location,
    updated_at, content, source. Returns whatever succeeded if some boards
    fail -- logs a warning per failed board rather than aborting the whole run.

    Boards are fetched concurrently (bounded pool, see BOARD_FETCH_WORKERS) --
    at 248+ boards, one-at-a-time sequential GETs was the single largest
    contributor to overall scan time.
    """
    items: list[dict] = []
    with ThreadPoolExecutor(max_workers=BOARD_FETCH_WORKERS) as executor:
        future_to_token = {executor.submit(_fetch_board, t): t for t in board_tokens}
        for future in as_completed(future_to_token):
            token = future_to_token[future]
            try:
                items.extend(future.result())
            except Exception:
                logger.exception("Failed to fetch/parse Greenhouse board %s", token)

    logger.info("Fetched %d raw items from Greenhouse (%d boards)", len(items), len(board_tokens))
    return items


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "greenhouse.json"


def main() -> None:
    items = fetch_raw()
    history_path = write_raw_output("greenhouse", items)
    print(f"Fetched {len(items)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
