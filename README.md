# AFTERLIGHT | Artificial Life Arena

A real-time spectator simulation where artificial-life-inspired soldiers fight using simple movement, collision, and attack rules. The default is 300 soldiers per army (600 total), and a battle begins as soon as the app starts.

## Getting started

Install Python 3.10 or later, then run this from the project folder. The interface uses the Python standard-library Tkinter package.

```powershell
python main.py
```

No third-party packages are required.

## Controls

- **PAUSE / RESUME** or **Space** — pause or resume the battle
- **0.5× / 1× / 2×** — change the simulation speed
- **UNITS PER ARMY** — choose 100–1,000 soldiers for each side
- **NEW BATTLE** — start a new battle with the selected army size
- **Click a soldier** — inspect an individual soldier's health

The red EMBER army and blue TIDELINE army each have scouts, infantry, and heavy soldiers. Units avoid collisions with nearby soldiers and attack enemies within range. Attacking soldiers are briefly highlighted, with an attack line showing their target. The battle ends when one army is wiped out.

The simulation updates at approximately 30 steps per second.

## Tests

```powershell
python -m unittest discover -s tests -v
```
