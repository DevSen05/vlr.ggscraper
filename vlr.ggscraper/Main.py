import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
from io import BytesIO
import os

from Colors import agent_colors



# FILE NAME SANITIZER


def sanitize_filename(name):
    return "".join(
        c if c.isalnum() or c in "._- " else "_"
        for c in name
    ).replace(" ", "_")



# DOWNLOAD + CONVERT AGENT ICONS


def download_agent_icon(agent_name, img_url, folder):
    raw_path = os.path.join(folder, f"{agent_name}_raw")
    png_path = os.path.join(folder, f"{agent_name}.png")

    if os.path.exists(png_path):
        return png_path

    try:
        r = requests.get(img_url, stream=True)
        r.raise_for_status()

        with open(raw_path, "wb") as f:
            f.write(r.content)

        img = Image.open(BytesIO(r.content)).convert("RGBA")
        img.save(png_path, format="PNG")

        if os.path.exists(raw_path):
            os.remove(raw_path)

        return png_path

    except Exception as e:
        print(f"Failed to download icon for {agent_name}: {e}")
        return None



# SCRAPER


def fetch_player_stats(url, icon_folder):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    # Extract player name from large profile header
    player_header = soup.select_one("h1.wf-title")
    player_name_clean = player_header.text.strip() if player_header else "Player"

    #  Extract Current & Past teams using nearest heading context 
    current_teams = []
    past_teams = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        name = a.get_text(strip=True)
        if not name or "/team/" not in href:
            continue

        # Look upwards for the nearest heading that mentions Current or Past teams
        marker = a.find_previous(string=lambda t: t and ("Current Teams" in t or "Past Teams" in t))
        if not marker:
            continue

        header_text = marker.strip().lower()
        if "current teams" in header_text:
            current_teams.append(name)
        elif "past teams" in header_text:
            past_teams.append(name)

    # De-duplicate while preserving order
    def unique(seq):
        seen = set()
        out = []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    current_teams = unique(current_teams)
    past_teams = unique(past_teams)

    # Locate stats table
    table = soup.select_one("table.wf-table")
    if table is None:
        print("Could not find player stats table.")
        return None, None, player_name_clean, current_teams, past_teams

    rows = table.select("tbody tr")
    agent_data = []
    icon_paths = {}

    for row in rows:
        tds = row.select("td")

        agent_img = tds[0].select_one("img")
        agent_name = agent_img["alt"].capitalize()

        img_url = agent_img["src"]
        if img_url.startswith("/"):
            img_url = "https://www.vlr.gg" + img_url
        elif img_url.startswith("//"):
            img_url = "https:" + img_url

        icon_paths[agent_name] = download_agent_icon(agent_name, img_url, icon_folder)

        cols = [td.text.strip() for td in tds[1:]]
        agent_data.append([agent_name] + cols)

    columns = [
        "Agent", "Use", "Rnd", "Rating", "ACS", "KD", "ADR",
        "KAST", "KPR", "APR", "FKPR", "FDPR",
        "K", "D", "A", "FK", "FD"
    ]

    df = pd.DataFrame(agent_data, columns=columns)

    numeric_cols = ["Rating", "ACS", "KD", "ADR", "KAST",
                    "KPR", "APR", "FKPR", "FDPR", "FK", "FD"]

    for col in numeric_cols:
        df[col] = df[col].str.replace("%", "").astype(float)

    return df, icon_paths, player_name_clean, current_teams, past_teams



# GRAPHING — COLORS + ICONS + TITLES


def plot_stat_with_icons(df, stat_name_display, values, folder, filename, icon_paths):
    plt.figure(figsize=(10, 6))

    bar_colors = [agent_colors.get(agent, "#4c72b0") for agent in df["Agent"]]
    bars = plt.bar(df["Agent"], values, color=bar_colors, edgecolor="black")

    # Value labels above bars
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2., height,
            f"{height:.2f}",
            ha='center', va='bottom', fontsize=10
        )

    ax = plt.gca()
    ax.set_xticks([])

    # Icons under bars
    for i, agent in enumerate(df["Agent"]):
        icon_path = icon_paths.get(agent)
        if icon_path and os.path.exists(icon_path):
            img = plt.imread(icon_path)
            imagebox = OffsetImage(img, zoom=0.22)
            ab = AnnotationBbox(
                imagebox,
                (i, -0.22),
                frameon=False,
                xycoords=("data", "axes fraction")
            )
            ax.add_artist(ab)

    # Final title: PLAYER NAME : STAT
    plt.title(stat_name_display, fontsize=16, fontweight="bold")
    plt.ylabel(stat_name_display, fontsize=13)

    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(folder, filename))
    plt.close()


def plot_stat_bars(df, folder, icon_paths, player_name_clean):

    duel_wr = (df["FK"] / (df["FK"] + df["FD"]).replace(0, 1)) * 100
    games_played = df["Use"].str.extract(r"\((\d+)\)").astype(int)[0]

    stats_to_plot = {
        "Comparative First Duel Winrate (%)": duel_wr,
        "Comparative KAST (%)": df["KAST"],
        "Comparative K/D": df["KD"],
        "Comparative ACS": df["ACS"],
        "Comparative Rating 2.0": df["Rating"],
        "Comparative Games Played": games_played
    }

    for stat_name, values in stats_to_plot.items():

        # Graph title that displays ON the chart
        stat_name_display = f"{player_name_clean} : {stat_name}"

        
        filename = sanitize_filename(stat_name) + ".png"

        plot_stat_with_icons(df, stat_name_display, values, folder, filename, icon_paths)



# MAIN


player_url = input("Enter VLR.gg player URL: ").strip()

if not player_url.startswith("http"):
    player_url = "https://" + player_url

if "timespan=" not in player_url:
    player_url += ("&" if "?" in player_url else "?") + "timespan=all"

try:
    player_dirname = player_url.split("/player/")[1].split("/")[1].split("?")[0].lower()
except:
    player_dirname = "player"

main_folder = os.path.join(os.getcwd(), player_dirname)
icon_folder = os.path.join(main_folder, "icons")
os.makedirs(main_folder, exist_ok=True)
os.makedirs(icon_folder, exist_ok=True)

df, icon_paths, player_name_clean, current_teams, past_teams = fetch_player_stats(player_url, icon_folder)

if df is not None:
    print("\nAgent Breakdown:\n")
    print(df)
    print(f"\nSaving graphs to: {main_folder}\n")

    plot_stat_bars(df, main_folder, icon_paths, player_name_clean)

    
    # WRITE PLAYER CURRENT & PAST TEAMS TEXT FILE
    
    txt_filename = f"{player_name_clean}_past_teams.txt"
    txt_path = os.path.join(main_folder, txt_filename)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Player: {player_name_clean}\n\n")

        f.write("Current Teams:\n")
        if current_teams:
            for t in current_teams:
                f.write(f"- {t}\n")
        else:
            f.write("- None\n")

        f.write("\nPast Teams:\n")
        if past_teams:
            for t in past_teams:
                f.write(f"- {t}\n")
        else:
            f.write("- None\n")

    print("All graphs saved successfully with full titles, colors, and icons!")
    print(f"Team info saved to: {txt_path}")
else:
    print("No stats found.")
