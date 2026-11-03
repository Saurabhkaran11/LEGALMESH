# TrustFoundry
TRUSTFOUNDRY_BASE_URL = "https://api.trustfoundry.ai"

# Legal domains the classifier can choose from, with example topics
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
