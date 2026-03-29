import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
 
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "nl-NL,nl;q=0.9",
}
 
FALLBACK = {"Euro 95": 1.949, "Diesel": 1.789, "LPG": 0.899}
 
def vind_prijs(tekst, min_p=1.0, max_p=3.5):
    matches = re.findall(r'\b([12])[,\.](\d{3})\b', tekst)
    for m in matches:
        p = float(m[0] + "." + m[1])
        if min_p < p < max_p:
            return round(p, 3)
    return None
 
def scrape_tango():
    """Tango toont dagelijkse adviesprijzen prominent op hun site"""
    try:
        url = "https://www.tango.nl/tanken/brandstofprijzen/"
        res = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
        tekst = soup.get_text(" ", strip=True)
        e95 = None
        diesel = None
        lpg = None
        regels = tekst.split("  ")
        for regel in regels:
            r = regel.lower().strip()
            if not r:
                continue
            if ("euro 95" in r or "e10" in r) and not e95:
                p = vind_prijs(regel)
                if p:
                    e95 = p
            if "diesel" in r and "premium" not in r and not diesel:
                p = vind_prijs(regel)
                if p:
                    diesel = p
            if "lpg" in r and not lpg:
                p = vind_prijs(regel, 0.5, 2.0)
                if p:
                    lpg = p
        # Probeer ook via alle getallen in de pagina
        if not e95 or not diesel:
            alle_prijzen = re.findall(r'\b([12])[\.,](\d{3})\b', tekst)
            unieke = []
            for m in alle_prijzen:
                p = float(m[0] + "." + m[1])
                if 1.5 < p < 2.5 and p not in unieke:
                    unieke.append(p)
            unieke.sort()
            if len(unieke) >= 2 and not e95:
                diesel = round(unieke[0], 3)
                e95 = round(unieke[1], 3)
        if e95 and diesel:
            print("Tango gelukt: E95=" + str(e95) + " Diesel=" + str(diesel))
            return {"Euro 95": e95, "Diesel": diesel, "LPG": lpg or 0.899}
        print("Tango: prijzen niet gevonden in tekst")
    except Exception as e:
        print("Tango mislukt: " + str(e))
    return None
 
def scrape_anwb():
    """ANWB landelijke gemiddelden"""
    try:
        url = "https://www.anwb.nl/auto/brandstof/brandstofprijzen"
        res = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
        tekst = soup.get_text(" ", strip=True)
        e95 = None
        diesel = None
        lpg = None
        regels = tekst.split("  ")
        for regel in regels:
            r = regel.lower().strip()
            if ("euro 95" in r or "benzine" in r or "e10" in r) and not e95:
                p = vind_prijs(regel)
                if p:
                    e95 = p
            if "diesel" in r and "premium" not in r and not diesel:
                p = vind_prijs(regel)
                if p:
                    diesel = p
            if "lpg" in r and not lpg:
                p = vind_prijs(regel, 0.5, 2.0)
                if p:
                    lpg = p
        if e95 and diesel:
            print("ANWB gelukt: E95=" + str(e95) + " Diesel=" + str(diesel))
            return {"Euro 95": e95, "Diesel": diesel, "LPG": lpg or 0.899}
        print("ANWB: prijzen niet gevonden")
    except Exception as e:
        print("ANWB mislukt: " + str(e))
    return None
 
def scrape_unitedconsumers():
    try:
        url = "https://www.unitedconsumers.com/tanken/brandstofprijzen"
        res = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
        tekst = soup.get_text(" ", strip=True)
        e95 = None
        diesel = None
        lpg = None
        regels = tekst.split("  ")
        for regel in regels:
            r = regel.lower().strip()
            if ("euro 95" in r or "e10" in r) and not e95:
                p = vind_prijs(regel)
                if p:
                    e95 = p
            if "diesel" in r and "premium" not in r and not diesel:
                p = vind_prijs(regel)
                if p:
                    diesel = p
            if "lpg" in r and not lpg:
                p = vind_prijs(regel, 0.5, 2.0)
                if p:
                    lpg = p
        if e95 and diesel:
            print("UnitedConsumers gelukt: E95=" + str(e95) + " Diesel=" + str(diesel))
            return {"Euro 95": e95, "Diesel": diesel, "LPG": lpg or 0.899}
        print("UnitedConsumers: prijzen niet gevonden")
    except Exception as e:
        print("UnitedConsumers mislukt: " + str(e))
    return None
 
def haal_prijzen_op():
    basis = None
    for fn in [scrape_tango, scrape_anwb, scrape_unitedconsumers]:
        basis = fn()
        if basis:
            break
 
    if not basis:
        print("Alle methodes mislukt, gebruik fallback")
        basis = FALLBACK
 
    offsets = {
        "Tango":    {"Euro 95": -0.14, "Diesel": -0.12},
        "Tinq":     {"Euro 95": -0.09, "Diesel": -0.08},
        "Avia":     {"Euro 95": -0.06, "Diesel": -0.05},
        "Calpam":   {"Euro 95": -0.06, "Diesel": -0.05},
        "Argos":    {"Euro 95": -0.05, "Diesel": -0.04},
        "Tamoil":   {"Euro 95": -0.05, "Diesel": -0.04},
        "Omo":      {"Euro 95": -0.04, "Diesel": -0.03},
        "Gulf":     {"Euro 95": -0.03, "Diesel": -0.02},
        "Q8":       {"Euro 95": -0.02, "Diesel": -0.01},
        "Total":    {"Euro 95":  0.00, "Diesel":  0.00},
        "Texaco":   {"Euro 95":  0.01, "Diesel":  0.01},
        "BP":       {"Euro 95":  0.02, "Diesel":  0.02},
        "Esso":     {"Euro 95":  0.03, "Diesel":  0.03},
        "Shell":    {"Euro 95":  0.05, "Diesel":  0.04},
        "Onbekend": {"Euro 95":  0.00, "Diesel":  0.00},
    }
 
    merkprijzen = {}
    for merk, off in offsets.items():
        merkprijzen[merk] = {
            "Euro 95": round(basis["Euro 95"] + off["Euro 95"], 3),
            "Diesel":  round(basis["Diesel"] + off["Diesel"], 3),
            "LPG":     basis.get("LPG", 0.899)
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
