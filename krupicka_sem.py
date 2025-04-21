import subprocess
import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import shutil

def kelvin_to_celsius(temp):
    """
    Převádí teplotu z Kelvinů na stupně Celsia.

    Args:
        temp (float or int): Teplota v Kelvinech.

    Returns:
        float or None: Teplota ve stupních Celsia nebo None pokud vstup není číslo.
    """
    return round(temp - 273.15, 2) if isinstance(temp, (int, float)) else None

def extract_metadata(folder_path):
    """
    Extrahuje metadata z obrázků ve složce pomocí ExifTool.

    Args:
        folder_path (str): Cesta ke složce obsahující obrázky.

    Returns:
        list[dict]: Seznam slovníků obsahujících metadata obrázků.
    """
    # Kontrola dostupnosti ExifTool – nutné pro extrakci metadat
    if not shutil.which("exiftool"):
        raise FileNotFoundError("ExifTool není dostupný v PATH.")

    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Složka {folder_path} neexistuje nebo není adresář.")

    # Filtrování pouze obrázků běžných formátů – JPG, JPEG, PNG
    photos = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")) + list(folder.glob("*.png"))
    if not photos:
        print("Ve složce nejsou žádné obrázky.")
        return []

    data = []
    for photo in photos:
        # Spuštění exiftool pro daný soubor a získání požadovaných metadat
        result = subprocess.run([
            "exiftool", "-json", "-DateTimeOriginal", "-FocalLength", "-ImageTemperatureMax", "-ImageTemperatureMin", str(photo)
        ], capture_output=True, text=True)

        try:
            metadata = json.loads(result.stdout)[0]  # Načtení JSON výstupu
        except:
            continue  # Pokud nastane chyba, pokračujeme na další soubor

        # Zajištění, že metadata obsahují klíč 'FileName'
        file_name = photo.name  # Používáme název souboru jako 'FileName'

        # Převod časového údaje do formátu bez časového pásma pro jednodušší práci a porovnání
        date_time = pd.to_datetime(metadata.get("DateTimeOriginal", None), format="%Y:%m:%d %H:%M:%S.%f%z", errors="coerce")
        if pd.notna(date_time):
            date_time = date_time.tz_convert(None)

        # Sestavení jednoho záznamu s potřebnými hodnotami
        data.append({
            "FileName": file_name,
            "DateTime": date_time,
            "FocalLength": metadata.get("FocalLength", "N/A"),
            "TempMax": kelvin_to_celsius(metadata.get("ImageTemperatureMax")),
            "TempMin": kelvin_to_celsius(metadata.get("ImageTemperatureMin")),
        })
    return data

def plot_temperatures(data):
    """
    Vykreslí časový graf s minimálními a maximálními teplotami.

    Args:
        data (list[dict]): Seznam metadat s časem a teplotami.
    """
    # Převod na DataFrame a filtrování nekompletních záznamů
    df = pd.DataFrame(data).dropna(subset=["DateTime", "TempMax", "TempMin"]).sort_values("DateTime")
    if df.empty:
        print("Žádná platná data pro vykreslení grafu.")
        return

    # Nastavení grafu a vykreslení teplot
    plt.figure(figsize=(10, 5))
    plt.plot(df["DateTime"], df["TempMax"], label="maximální teplota", color="red")
    plt.plot(df["DateTime"], df["TempMin"], label="minimální teplota", color="blue")
    plt.xticks(rotation=45)
    plt.xlabel("Čas měření")
    plt.ylabel("Teplota (°C)")
    plt.title("Teploty hrníčku s teplou vodou během 30 minut")
    plt.legend()
    plt.tight_layout()
    plt.savefig("temperature_plot.jpg")  # Uložení výstupu jako JPEG
    plt.show()

def save_to_excel(data, output_file):
    """
    Uloží extrahovaná metadata do Excel souboru.

    Args:
        data (list[dict]): Metadata k uložení.
        output_file (str): Název výsledného souboru.
    """
    df = pd.DataFrame(data)
    if df.empty:
        print("Žádná data k uložení.")
        return
    df.to_excel(output_file, index=False)
    print(f"Data byla uložena do {output_file}")

if __name__ == "__main__":
    folder = r"C:\\Users\\Jarda\\Desktop\\fotky_pokus"
    output_excel = "metadata.xlsx"

    metadata = extract_metadata(folder)
    if metadata:
        plot_temperatures(metadata)
        save_to_excel(metadata, output_excel)