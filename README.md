
**📌 Overview**

STATSTEALER scrapes any VLR.gg player profile and automatically generates:

**📊 Agent Performance Charts**

For every agent the player has used, the script outputs:

- ACS
- ADR
- K/D
- KAST
- First Duel Winrate (%)
- Rating 2.0
- Games Played

Each stat becomes its own graph with:

- ✔ Agent-specific color palettes
- ✔ Agent icons aligned under each bar
- ✔ Clean layout with grid + labels
- ✔ Graph title in the format:
  <Player Name> : <Stat Name>

**📝 Team History Text File**  
Automatically extracts Current Teams and Past Teams, saved as:  
<PlayerName>_past_teams.txt

**🚀 How to Use**

**Install dependencies**

pip install requests beautifulsoup4 pandas matplotlib pillow

**Run the program**

python Main.py

**Enter any VLR.gg player link**

Example: https://www.vlr.gg/player/9/tenz

Wait a few seconds.  
Your graphs + team history will appear inside a folder named after the player.

**🔧 Features & Details**

✔ Intelligent URL handling  
Automatically fixes missing https:// and forces timespan=all.

✔ Clean graph formatting  
- Bars colored by agent theme  
- Icons perfectly aligned under x-axis  
- Crisp label formatting  
- High DPI PNGs

✔ Error-safe scraping  
Missing icons or stats fail gracefully without breaking the script.

✔ Cached icons  
Icons download once and are reused.

**📣 Notes**

- Script works with all VLR.gg players, regardless of region.  
- Works on Windows, MacOS, and Linux.  
- Tested on Python 3.10–3.12.

