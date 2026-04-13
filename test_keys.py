"""
LegalMesh — API Key & Endpoint Tester
Run this on your laptop to verify all keys work:
    cd legalmesh
    python test_keys.py
"""

import asyncio
import httpx
import os
import sys
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
TRUSTFOUNDRY_API_KEY = os.getenv("TRUSTFOUNDRY_API_KEY")

PASS = "✅ PASS"
FAIL = "❌ FAIL"
WARN = "⚠️  WARN"

HF_API_BASE = "https://datasets-server.huggingface.co"

DATASETS = {
    "state_laws": "justicedao/ipfs_state_laws",
    "uscode": "justicedao/ipfs_uscode",
    "federal_register": "justicedao/ipfs_federal_register",
    "court_rules": "justicedao/ipfs_court_rules",
    "caselaw": "justicedao/ipfs_caselaw_access_project",
    "caselaw_embeddings": "justicedao/Caselaw_Access_Project_embeddings",
    "municipal_law": "justicedao/american_municipal_law",
}


async def test_anthropic():
    """Test Anthropic API key."""
    print("\n" + "=" * 60)
    print("1. ANTHROPIC API KEY")
    print("=" * 60)

    if not ANTHROPIC_API_KEY:
        print(f"  {FAIL} — ANTHROPIC_API_KEY not set in .env")
        return False

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=20,
            messages=[{"role": "user", "content": "Say OK"}],
        )
        print(f"  {PASS} — Key works!")
        print(f"  Model: {msg.model}")
        print(f"  Response: {msg.content[0].text}")
        print(f"  Tokens: {msg.usage.input_tokens} in / {msg.usage.output_tokens} out")
        return True
    except Exception as e:
        print(f"  {FAIL} — {str(e)[:200]}")
        return False


async def test_huggingface():
    """Test HuggingFace token and all 7 datasets."""
    print("\n" + "=" * 60)
    print("2. HUGGINGFACE TOKEN + 7 DATASETS")
    print("=" * 60)

    if not HF_TOKEN:
        print(f"  {FAIL} — HF_TOKEN not set in .env")
        return False

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    all_pass = True

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Test token validity
        try:
            r = await client.get("https://huggingface.co/api/whoami-v2", headers=headers)
            if r.status_code == 200:
                user = r.json()
                print(f"  {PASS} — Token valid (user: {user.get('name', 'unknown')})")
            else:
                print(f"  {FAIL} — Token invalid (status {r.status_code})")
                return False
        except Exception as e:
            print(f"  {FAIL} — Token check failed: {str(e)[:100]}")
            return False

        print()

        # Test each dataset
        for name, ds_id in DATASETS.items():
            try:
                # Try rows endpoint (most reliable)
                r = await client.get(
                    f"{HF_API_BASE}/rows",
                    params={"dataset": ds_id, "config": "default", "split": "train", "offset": 0, "length": 1},
                    headers=headers,
                )
                if r.status_code == 200:
                    data = r.json()
                    rows = data.get("rows", [])
                    if rows:
                        columns = list(rows[0].get("row", {}).keys())
                        print(f"  {PASS} {name}: accessible (columns: {columns[:5]})")
                    else:
                        print(f"  {WARN} {name}: accessible but empty")
                else:
                    print(f"  {FAIL} {name}: HTTP {r.status_code} — {r.text[:100]}")
                    all_pass = False
            except Exception as e:
                print(f"  {FAIL} {name}: {str(e)[:100]}")
                all_pass = False

        # Test search endpoint
        print()
        print("  SEARCH API TEST:")
        try:
            r = await client.get(
                f"{HF_API_BASE}/search",
                params={
                    "dataset": "justicedao/ipfs_state_laws",
                    "config": "default",
                    "split": "train",
                    "query": "security deposit landlord",
                    "offset": 0,
                    "length": 3,
                },
                headers=headers,
            )
            if r.status_code == 200:
                data = r.json()
                num = len(data.get("rows", []))
                print(f"  {PASS} Search works! ({num} results for 'security deposit landlord')")
            else:
                print(f"  {WARN} Search returned HTTP {r.status_code} — {r.text[:150]}")
                print(f"  (Search may not be enabled for all datasets — rows API will still work)")
        except Exception as e:
            print(f"  {WARN} Search error: {str(e)[:100]}")

    return all_pass


async def test_trustfoundry():
    """Test TrustFoundry API key against possible endpoints."""
    print("\n" + "=" * 60)
    print("3. TRUSTFOUNDRY API KEY")
    print("=" * 60)

    if not TRUSTFOUNDRY_API_KEY:
        print(f"  {WARN} — TRUSTFOUNDRY_API_KEY not set (optional but recommended)")
        return False

    # Try multiple possible endpoint patterns
    test_configs = [
        ("POST", "https://api.trustfoundry.ai/v1/search", {"query": "landlord security deposit", "limit": 3}),
        ("GET", "https://api.trustfoundry.ai/v1/search", None),
        ("POST", "https://api.trustfoundry.ai/search", {"query": "landlord security deposit", "limit": 3}),
        ("GET", "https://api.trustfoundry.ai/health", None),
        ("GET", "https://api.trustfoundry.ai/", None),
    ]

    auth_headers_options = [
        ("Bearer", {"Authorization": f"Bearer {TRUSTFOUNDRY_API_KEY}", "Content-Type": "application/json"}),
        ("X-API-Key", {"X-API-Key": TRUSTFOUNDRY_API_KEY, "Content-Type": "application/json"}),
    ]

    found_working = False

    async with httpx.AsyncClient(timeout=10.0) as client:
        for method, url, body in test_configs:
            for auth_name, headers in auth_headers_options:
                try:
                    if method == "POST" and body:
                        r = await client.post(url, json=body, headers=headers, follow_redirects=True)
                    else:
                        r = await client.get(url, headers=headers, follow_redirects=True)

                    if r.status_code < 400:
                        print(f"  {PASS} {method} {url} ({auth_name})")
                        print(f"       Status: {r.status_code}")
                        print(f"       Response: {r.text[:200]}")
                        found_working = True
                        break
                    elif r.status_code == 401:
                        print(f"  {FAIL} {method} {url} ({auth_name}): 401 Unauthorized")
                    elif r.status_code == 404:
                        pass  # skip silently
                    else:
                        print(f"  {WARN} {method} {url} ({auth_name}): HTTP {r.status_code}")
                except httpx.ConnectError:
                    print(f"  {FAIL} Cannot connect to {url} — domain may not exist")
                    break
                except Exception as e:
                    print(f"  {WARN} {method} {url}: {str(e)[:80]}")

            if found_working:
                break

    if not found_working:
        print(f"\n  {WARN} Could not find working TrustFoundry endpoint.")
        print(f"  Ask the TrustFoundry team for their exact API URL and auth method.")
        print(f"  The app will still work without it — just won't have TrustFoundry results.")

    return found_working


async def main():
    print("🔑 LegalMesh — API Key & Endpoint Tester")
    print("=" * 60)

    results = {}
    results["anthropic"] = await test_anthropic()
    results["huggingface"] = await test_huggingface()
    results["trustfoundry"] = await test_trustfoundry()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for name, passed in results.items():
        icon = PASS if passed else FAIL
        print(f"  {icon} {name}")

    all_critical_pass = results["anthropic"] and results["huggingface"]
    print()
    if all_critical_pass:
        print("🚀 READY TO DEMO! Run:")
        print("   python -m backend.main")
        print("   streamlit run frontend_streamlit/app.py")
    else:
        print("⚠️  Fix the failing keys above before demo.")

    return all_critical_pass


if __name__ == "__main__":
    asyncio.run(main())
