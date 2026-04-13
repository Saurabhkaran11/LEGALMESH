import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
TRUSTFOUNDRY_API_KEY = os.getenv("TRUSTFOUNDRY_API_KEY")
THENVOI_API_KEY = os.getenv("THENVOI_API_KEY")

# HuggingFace dataset IDs
DATASETS = {
    "state_laws": "justicedao/ipfs_state_laws",
    "uscode": "justicedao/ipfs_uscode",
    "federal_register": "justicedao/ipfs_federal_register",
    "court_rules": "justicedao/ipfs_court_rules",
    "caselaw": "justicedao/ipfs_caselaw_access_project",
    "caselaw_embeddings": "justicedao/Caselaw_Access_Project_embeddings",
    "municipal_law": "justicedao/american_municipal_law",
}

# TrustFoundry
TRUSTFOUNDRY_BASE_URL = "https://api.trustfoundry.ai"

# Legal domain taxonomy (subset of FOLIO's 18K concepts)
LEGAL_DOMAINS = {
    "employment": ["wages", "overtime", "discrimination", "wrongful termination", "harassment", "FMLA", "workers compensation"],
    "housing": ["landlord", "tenant", "eviction", "lease", "security deposit", "habitability", "rent"],
    "family": ["divorce", "custody", "child support", "adoption", "domestic violence", "alimony"],
    "consumer": ["debt", "credit", "fraud", "warranty", "refund", "contract", "billing"],
    "immigration": ["visa", "green card", "deportation", "asylum", "citizenship", "work permit"],
    "criminal": ["arrest", "charges", "bail", "plea", "sentencing", "probation", "expungement"],
    "personal_injury": ["accident", "negligence", "medical malpractice", "slip and fall", "damages"],
    "business": ["corporation", "LLC", "partnership", "trademark", "patent", "copyright", "contract"],
    "tax": ["IRS", "audit", "deduction", "filing", "tax court", "penalty", "exemption"],
    "civil_rights": ["discrimination", "voting", "free speech", "equal protection", "ADA", "Title VII"],
}

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
    "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    "DC": "District of Columbia",
}
