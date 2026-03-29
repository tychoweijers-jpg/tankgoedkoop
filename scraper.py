import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
 
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "nl-NL,nl;q=0.9",
}
 
# Actuele GLA prijzen 29 maart 2026 (bron: brandstof-zoeker.nl)
FALLBACK = {"Euro 95": 2.558, "Diesel": 2.647, "LPG": 1.323}
 
def vind_prijs(tekst, min_p=1.5, max_p=3.5):
    matches = re.findall(r'\b([2])[\.,](\d{3})\b', tekst)
    for m in matches:
        p = round(float(m[0] + "." + m[1]), 3)
        if min_p < p < max_p:
            return p
    return None
 
def scrape_brandstofzoeker():
    """Scrape adviesprijzen van brandstof-zoeker.nl"""
    try:
        url = "https://www.brandstof-zoeker.nl/adviesprijzen/"
        res = requests.get(url, headers=HEADERS, timeout=20)
        print("Brandstof-zoeker status: " + str(res.status_code))
        soup = BeautifulSoup(res.text, "html.parser")
        tekst = soup.get_text(" ", strip=True)
        print("Tekst fragment: " + tekst[:300])
 
        e95 = diesel = lpg = None
        for regel in tekst.split("\n"):
            r = regel.lower().strip()
            if ("euro 95" in r or "benzine" in r) and not e95:
                p = vind_prijs(regel)
                if p: e95 = p
            if "diesel" in r and "spec" not in r and "premium" not in r and not diesel:
                p = vind_prijs(regel)
                if p: diesel = p
            if "lpg" in r and not lpg:
                p = vind_prijs(regel, 0.5, 2.0)
                if p: lpg = p
 
        if e95 and diesel:
            print("Brandstof-zoeker gelukt: E95=" + str(e95) + " Diesel=" + str(diesel))
            return {"Euro 95": e95, "Diesel": diesel, "LPG": lpg or 1.323}
        print("Brandstof-zoeker: niet gevonden")
    except Exception as e:
        print("Brandstof-zoeker fout: " + str(e))
    return None
 
def scrape_unitedconsumers():
    """Scrape GLA van UnitedConsumers"""
    try:
        url = "https://www.unitedconsumers.com/tanken/brandstofprijzen"
        res = requests.get(url, headers=HEADERS, timeout=20)
        print("UC status: " + str(res.status_code))
        soup = BeautifulSoup(res.text, "html.parser")
        tekst = soup.get_text(" ", strip=True)
 
        e95 = diesel = lpg = None
        for regel in tekst.replace("  ", "\n").split("\n"):
            r = regel.lower().strip()
            if ("euro 95" in r or "e10" in r) and not e95:
                p = vind_prijs(regel)
                if p: e95 = p
            if "diesel" in r and "premium" not in r and not diesel:
                p = vind_prijs(regel)
                if p: diesel = p
            if "lpg" in r and not lpg:
                p = vind_prijs(regel, 0.5, 2.0)
                if p: lpg = p
 
        if e95 and diesel:
            print("UC gelukt: E95=" + str(e95) + " Diesel=" + str(diesel))
            return {"Euro 95": e95, "Diesel": diesel, "LPG": lpg or 1.323}
        print("UC: niet gevonden")
    except Exception as e:
        print("UC fout: " + str(e))
    return None
 
def haal_prijzen_op():
    basis = None
    for fn in [scrape_brandstofzoeker, scrape_unitedconsumers]:
        basis = fn()
        if basis:
            break
 
    if not basis:
        print("Scraping mislukt, gebruik actuele GLA van 29 maart 2026")
        basis = FALLBACK
 
    offsets = {
        "Tango":    {"Euro 95": -0.55, "Diesel": -0.44},
        "Tinq":     {"Euro 95": -0.50, "Diesel": -0.40},
        "Avia":     {"Euro 95": -0.48, "Diesel": -0.38},
        "Calpam":   {"Euro 95": -0.48, "Diesel": -0.38},
        "Argos":    {"Euro 95": -0.47, "Diesel": -0.37},
        "Tamoil":   {"Euro 95": -0.47, "Diesel": -0.37},
        "Omo":      {"Euro 95": -0.46, "Diesel": -0.36},
        "Gulf":     {"Euro 95": -0.45, "Diesel": -0.35},
        "Q8":       {"Euro 95": -0.44, "Diesel": -0.34},
        "Total":    {"Euro 95": -0.42, "Diesel": -0.32},
        "Texaco":   {"Euro 95": -0.40, "Diesel": -0.30},
        "BP":       {"Euro 95": -0.38, "Diesel": -0.28},
        "Esso":     {"Euro 95": -0.35, "Diesel": -0.25},
        "Shell":    {"Euro 95": -0.30, "Diesel": -0.20},
        "Onbekend": {"Euro 95": -0.42, "Diesel": -0.32},
    }
 
    merkprijzen = {}
    for merk, off in offsets.items():
        merkprijzen[merk] = {
            "Euro 95": round(basis["Euro 95"] + off["Euro 95"], 3),
            "Diesel":  round(basis["Diesel"] + off["Diesel"], 3),
            "LPG":     round(basis.get("LPG", 1.323) * 0.65, 3)
        }
 
    return {"basis": basis, "merken": merkprijzen}
 
def sla_op(data):
    output = {
        "bijgewerkt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "prijzen": data["basis"],
        "merkprijzen": data["merken"]
    }
    with open("prijzen.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print("Opgeslagen: " + str(data["basis"]))
 
if __name__ == "__main__":
    data = haal_prijzen_op()
    sla_op(data)
 
