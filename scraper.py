import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

URL = "https://www.brandstof-zoeker.nl/"

# Voorbeeld postcode → GPS lookup
postcode_coord_lookup = {
    "1012AB": {"lat": 52.374, "lon": 4.897},
    "1021AA": {"lat": 52.400, "lon": 4.920},
    "1071AC": {"lat": 52.345, "lon": 4.890}
}

def haal_prijzen():
    res = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")

    stations = []
    rows = soup.select("table tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:  # Controleer of alle brandstofkolommen aanwezig zijn
            continue
        try:
            naam = cols[0].text.strip()
            locatie = cols[1].text.strip()
            euro95 = float(cols[2].text.strip().replace(",", "."))
            diesel = float(cols[3].text.strip().replace(",", "."))
            lpg = float(cols[4].text.strip().replace(",", "."))

            # Voor demo: gebruik altijd 1012AB voor coördinaten
            coord = postcode_coord_lookup.get("1012AB", {"lat": 52.374, "lon": 4.897})

            stations.append({
                "naam": naam,
                "locatie": locatie,
                "euro95": euro95,
                "diesel": diesel,
                "lpg": lpg,
                "lat": coord["lat"],
                "lon": coord["lon"]
            })
        except Exception as e:
            print("Fout bij row:", e)
            continue
    return stations

def sla_op(data):
    with open("prijzen.json", "w") as f:
        json.dump({
            "updated": datetime.now().isoformat(),
            "stations": data
        }, f, indent=2)

if __name__ == "__main__":
    print("⛽ Prijzen ophalen...")
    data = haal_prijzen()
    print(f"✅ {len(data)} stations gevonden")
    sla_op(data)
    print("💾 prijzen.json bijgewerkt")
