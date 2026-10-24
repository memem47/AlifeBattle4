from __future__ import annotations

import random
import tkinter as tk
from tkinter import messagebox

from battle_sim import BattleSimulation, UNIT_RADIUS, Unit


BACKGROUND = "#090d12"
PANEL = "#101820"
PANEL_LIGHT = "#151f29"
GRID = "#1a2730"
TEXT = "#e8edf0"
MUTED = "#71808a"
RED = "#ff5b58"
BLUE = "#56c8ff"
GOLD = "#f5c66c"
WORLD_WIDTH = 1_100
WORLD_HEIGHT = 720


class BattleApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("AFTERLIGHT  |  Artificial Life Arena")
        self.root.configure(bg=BACKGROUND)
        self.root.geometry("1380x860")
        self.root.minsize(1100, 700)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

        self.team_size_var = tk.IntVar(value=300)
        self.simulation = BattleSimulation(WORLD_WIDTH, WORLD_HEIGHT, team_size=300)
        self.running = True
        self.speed = 1.0
        self.frame_number = 0
        self.selected_unit: Unit | None = None
        self.rng = random.Random(2048)
        self.view_scale = 1.0
        self.view_offset_x = 0.0
        self.view_offset_y = 0.0
        self.unit_shapes: list[int] = []
        self.corpse_markers: dict[int, tuple[int, int]] = {}
        self.attack_effects: dict[int, tuple[int, int, int, int]] = {}
        self.particle_data: list[list[float | int]] = []
        self._build_interface()
        self._draw_battlefield()
        self._update_dashboard()
        self.root.bind_all("<space>", self._toggle_pause)
        self.root.after(33, self._animate)

    def _build_interface(self) -> None:
        header = tk.Frame(self.root, bg=BACKGROUND, height=86)
        header.pack(fill="x", padx=25, pady=(19, 12))
        header.pack_propagate(False)

        brand = tk.Frame(header, bg=BACKGROUND)
        brand.pack(side="left", fill="y")
        tk.Label(
            brand,
            text="A / L",
            fg=GOLD,
            bg=BACKGROUND,
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")
        tk.Label(
            brand,
            text="AFTERLIGHT     /     ARTIFICIAL LIFE ARENA",
            fg=TEXT,
            bg=BACKGROUND,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", pady=(3, 0))
        tk.Label(
            brand,
            text="AN UNSCRIPTED BATTLE. EVERY SOLDIER MAKES ITS OWN CHOICE.",
            fg=MUTED,
            bg=BACKGROUND,
            font=("Consolas", 9),
        ).pack(anchor="w", pady=(5, 0))

        self.live_label = tk.Label(
            header,
            text="●  LIVE SIMULATION",
            fg="#8fdbad",
            bg=BACKGROUND,
            font=("Consolas", 10, "bold"),
        )
        self.live_label.pack(side="right", anchor="n", pady=7)

        body = tk.Frame(self.root, bg=BACKGROUND)
        body.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        arena_panel = tk.Frame(body, bg=PANEL)
        arena_panel.pack(side="left", fill="both", expand=True)

        arena_header = tk.Frame(arena_panel, bg=PANEL, height=44)
        arena_header.pack(fill="x", padx=16)
        arena_header.pack_propagate(False)
        tk.Label(
            arena_header,
            text="FIELD 01    /    THE OPEN PLAIN",
            fg="#a4b0b9",
            bg=PANEL,
            font=("Consolas", 9, "bold"),
        ).pack(side="left", anchor="center")
        self.clock_label = tk.Label(
            arena_header,
            text="00:00",
            fg=TEXT,
            bg=PANEL,
            font=("Consolas", 11, "bold"),
        )
        self.clock_label.pack(side="right", anchor="center")

        self.canvas = tk.Canvas(
            arena_panel,
            bg="#11191a",
            highlightthickness=0,
            width=WORLD_WIDTH,
            height=WORLD_HEIGHT,
            cursor="crosshair",
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.canvas.bind("<Button-1>", self._select_unit)
        self.canvas.bind("<Configure>", self._on_resize)

        self.sidebar = tk.Frame(body, bg=PANEL, width=285)
        self.sidebar.pack(side="right", fill="y", padx=(14, 0))
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

    def _build_sidebar(self) -> None:
        pad = 16
        tk.Label(
            self.sidebar,
            text="LIVE INTELLIGENCE",
            fg=MUTED,
            bg=PANEL,
            font=("Consolas", 9, "bold"),
        ).pack(anchor="w", padx=pad, pady=(18, 14))

        self.army_labels: list[tk.Label] = []
        for team, name, color in (
            (0, "EMBER   /   RED", RED),
            (1, "TIDELINE   /   BLUE", BLUE),
        ):
            card = tk.Frame(self.sidebar, bg=PANEL_LIGHT)
            card.pack(fill="x", padx=pad, pady=5)
            tk.Label(
                card,
                text=name,
                fg=color,
                bg=PANEL_LIGHT,
                font=("Consolas", 9, "bold"),
            ).pack(anchor="w", padx=11, pady=(10, 3))
            label = tk.Label(
                card,
                text="1,000",
                fg=TEXT,
                bg=PANEL_LIGHT,
                font=("Segoe UI", 25, "bold"),
            )
            label.pack(anchor="w", padx=10, pady=(0, 4))
            bar_bg = tk.Frame(card, bg="#28333a", height=4)
            bar_bg.pack(fill="x", padx=11, pady=(1, 11))
            fill = tk.Frame(bar_bg, bg=color, height=4)
            fill.place(relwidth=1, relheight=1)
            self.army_labels.append(label)
            setattr(self, f"team_{team}_bar", fill)

        casualty_panel = tk.Frame(self.sidebar, bg=PANEL, highlightbackground="#24313a", highlightthickness=1)
        casualty_panel.pack(fill="x", padx=pad, pady=(17, 0))
        tk.Label(
            casualty_panel,
            text="CASUALTIES",
            fg=MUTED,
            bg=PANEL,
            font=("Consolas", 9, "bold"),
        ).pack(anchor="w", padx=12, pady=(10, 3))
        self.casualty_label = tk.Label(
            casualty_panel,
            text="000  —  000",
            fg=TEXT,
            bg=PANEL,
            font=("Consolas", 15, "bold"),
        )
        self.casualty_label.pack(anchor="w", padx=12, pady=(0, 10))

        tk.Label(
            self.sidebar,
            text="UNITS PER ARMY",
            fg=MUTED,
            bg=PANEL,
            font=("Consolas", 9, "bold"),
        ).pack(anchor="w", padx=pad, pady=(22, 9))
        size_row = tk.Frame(self.sidebar, bg=PANEL)
        size_row.pack(fill="x", padx=pad)
        self.team_size_input = tk.Spinbox(
            size_row,
            from_=100,
            to=1_000,
            increment=100,
            textvariable=self.team_size_var,
            bg="#1a252d",
            fg=TEXT,
            buttonbackground="#26333b",
            insertbackground=TEXT,
            relief="flat",
            bd=0,
            font=("Consolas", 11, "bold"),
            width=8,
            justify="center",
        )
        self.team_size_input.pack(side="left", fill="x", expand=True)
        tk.Label(
            size_row,
            text="soldiers",
            fg=MUTED,
            bg=PANEL,
            font=("Consolas", 9),
        ).pack(side="left", padx=(8, 0))

        tk.Label(
            self.sidebar,
            text="SIMULATION SPEED",
            fg=MUTED,
            bg=PANEL,
            font=("Consolas", 9, "bold"),
        ).pack(anchor="w", padx=pad, pady=(17, 9))
        speed_row = tk.Frame(self.sidebar, bg=PANEL)
        speed_row.pack(fill="x", padx=pad)
        self.speed_buttons: list[tk.Button] = []
        for speed in (0.5, 1.0, 2.0):
            button = tk.Button(
                speed_row,
                text=f"{speed:g}×",
                command=lambda value=speed: self._set_speed(value),
                font=("Consolas", 9, "bold"),
                relief="flat",
                bd=0,
                padx=9,
                pady=7,
                cursor="hand2",
            )
            button.pack(side="left", expand=True, fill="x", padx=(0, 4))
            self.speed_buttons.append(button)

        self.pause_button = tk.Button(
            self.sidebar,
            text="Ⅱ    PAUSE",
            command=self._toggle_pause,
            bg="#26333b",
            fg=TEXT,
            activebackground="#354650",
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            font=("Consolas", 10, "bold"),
            cursor="hand2",
            pady=11,
        )
        self.pause_button.pack(fill="x", padx=pad, pady=(17, 7))
        tk.Button(
            self.sidebar,
            text="↻    NEW BATTLE",
            command=self._restart,
            bg="#392e23",
            fg="#f0c981",
            activebackground="#51402f",
            activeforeground="#ffe3ac",
            relief="flat",
            bd=0,
            font=("Consolas", 10, "bold"),
            cursor="hand2",
            pady=10,
        ).pack(fill="x", padx=pad)

        tk.Frame(self.sidebar, bg="#25313a", height=1).pack(fill="x", padx=pad, pady=(20, 13))
        tk.Label(
            self.sidebar,
            text="FIELD NOTES",
            fg=MUTED,
            bg=PANEL,
            font=("Consolas", 9, "bold"),
        ).pack(anchor="w", padx=pad, pady=(0, 8))
        self.event_label = tk.Label(
            self.sidebar,
            text="The two armies advance.\nThe outcome is unwritten.",
            fg="#c0c9ce",
            bg=PANEL,
            justify="left",
            anchor="nw",
            wraplength=245,
            font=("Segoe UI", 9),
        )
        self.event_label.pack(fill="x", padx=pad)

        tk.Label(
            self.sidebar,
            text="CLICK A SOLDIER TO FOLLOW\nSPACE  /  PAUSE",
            fg="#586670",
            bg=PANEL,
            justify="left",
            font=("Consolas", 8),
        ).pack(side="bottom", anchor="w", padx=pad, pady=14)
        self._update_speed_buttons()

    def _draw_battlefield(self) -> None:
        self.canvas.delete("all")
        self.unit_shapes.clear()
        self.corpse_markers.clear()
        self.attack_effects.clear()
        self.particle_data.clear()
        self._update_view_transform()
        self.canvas.create_rectangle(
            0,
            0,
            max(self.canvas.winfo_width(), 1),
            max(self.canvas.winfo_height(), 1),
            fill="#11191a",
            outline="",
        )
        for x in range(0, WORLD_WIDTH + 1, 55):
            x1, y1 = self._world_to_view(x, 0)
            x2, y2 = self._world_to_view(x, WORLD_HEIGHT)
            self.canvas.create_line(x1, y1, x2, y2, fill=GRID)
        for y in range(0, WORLD_HEIGHT + 1, 55):
            x1, y1 = self._world_to_view(0, y)
            x2, y2 = self._world_to_view(WORLD_WIDTH, y)
            self.canvas.create_line(x1, y1, x2, y2, fill=GRID)

        rng = random.Random(321)
        for _ in range(470):
            x, y = rng.randrange(WORLD_WIDTH), rng.randrange(WORLD_HEIGHT)
            size = rng.choice((1, 1, 1, 2))
            color = rng.choice(("#24302a", "#29342d", "#30352d", "#232d2b"))
            view_x, view_y = self._world_to_view(x, y)
            self.canvas.create_oval(
                view_x - size * self.view_scale,
                view_y - size * self.view_scale,
                view_x + size * self.view_scale,
                view_y + size * self.view_scale,
                fill=color,
                outline="",
            )

        center_x1, center_y1 = self._world_to_view(WORLD_WIDTH / 2, 0)
        center_x2, center_y2 = self._world_to_view(WORLD_WIDTH / 2, WORLD_HEIGHT)
        self.canvas.create_line(
            center_x1,
            center_y1,
            center_x2,
            center_y2,
            fill="#433f33",
            dash=(4, 7),
        )
        label_x, label_y = self._world_to_view(WORLD_WIDTH / 2 + 13, 18)
        self.canvas.create_text(
            label_x,
            label_y,
            text="NO MAN'S LAND",
            fill="#77705c",
            anchor="nw",
            font=("Consolas", 8),
        )
        north_x, north_y = self._world_to_view(16, 17)
        self.canvas.create_text(
            north_x,
            north_y,
            text="N",
            fill="#617178",
            anchor="nw",
            font=("Consolas", 8, "bold"),
        )

        for index, unit in enumerate(self.simulation.units):
            color = self._unit_color(unit)
            x, y = self._world_to_view(unit.x, unit.y)
            radius = UNIT_DOT * self.view_scale
            shape = self.canvas.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                fill=color,
                outline="",
            )
            self.unit_shapes.append(shape)
            if not unit.alive:
                self._draw_corpse(index)
        self._draw_selection()

    def _unit_color(self, unit: Unit) -> str:
        if unit.team == 0:
            return ("#ffb06b", "#f36d55", "#ba4b44")[unit.kind]
        return ("#a3e9ff", "#59bce6", "#3d789f")[unit.kind]

    def _update_view_transform(self) -> None:
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        self.view_scale = min(width / WORLD_WIDTH, height / WORLD_HEIGHT)
        self.view_offset_x = (width - WORLD_WIDTH * self.view_scale) / 2
        self.view_offset_y = (height - WORLD_HEIGHT * self.view_scale) / 2

    def _world_to_view(self, x: float, y: float) -> tuple[float, float]:
        return (
            self.view_offset_x + x * self.view_scale,
            self.view_offset_y + y * self.view_scale,
        )

    def _draw_selection(self) -> None:
        self.canvas.delete("selection")
        unit = self.selected_unit
        if unit is None or not unit.alive:
            return
        x, y = self._world_to_view(unit.x, unit.y)
        radius = max(6, UNIT_DOT * self.view_scale * 2.5)
        self.canvas.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            outline=GOLD,
            width=1,
            tags="selection",
        )

    def _select_unit(self, event: tk.Event) -> None:
        self._update_view_transform()
        world_x = (event.x - self.view_offset_x) / self.view_scale
        world_y = (event.y - self.view_offset_y) / self.view_scale
        best: Unit | None = None
        best_distance = 18.0**2
        for unit in self.simulation.units:
            if not unit.alive:
                continue
            distance = (unit.x - world_x) ** 2 + (unit.y - world_y) ** 2
            if distance < best_distance:
                best, best_distance = unit, distance
        self.selected_unit = best
        if best is not None:
            name = ("SCOUT", "INFANTRY", "HEAVY")[best.kind]
            color = "EMBER" if best.team == 0 else "TIDELINE"
            self.event_label.config(
                text=f"FOLLOWING {color} {name}\n"
                f"Health  {best.health:.0f} / {best.max_health:.0f}\n"
                "An individual among two thousand."
            )
            self._draw_selection()

    def _on_resize(self, _event: tk.Event) -> None:
        if self.unit_shapes:
            self._draw_battlefield()

    def _render_units(self) -> None:
        self._update_view_transform()
        for index, (unit, shape) in enumerate(zip(self.simulation.units, self.unit_shapes)):
            if unit.alive:
                x, y = self._world_to_view(unit.x, unit.y)
                radius = UNIT_DOT * self.view_scale
                self.canvas.coords(shape, x - radius, y - radius, x + radius, y + radius)
            elif index not in self.corpse_markers:
                self._draw_corpse(index)
        self._render_attack_effects()
        self._draw_selection()

    def _draw_corpse(self, index: int) -> None:
        unit = self.simulation.units[index]
        x, y = self._world_to_view(unit.x, unit.y)
        shape = self.unit_shapes[index]
        corpse_fill = "#49352f" if unit.team == 0 else "#293b43"
        corpse_mark = "#bc7663" if unit.team == 0 else "#69a1b8"
        self.canvas.itemconfigure(
            shape,
            fill=corpse_fill,
            outline=corpse_mark,
            width=1,
        )
        radius = max(2.5, UNIT_DOT * self.view_scale * 0.8)
        first_mark = self.canvas.create_line(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            fill=corpse_mark,
            width=1,
            tags="corpse",
        )
        second_mark = self.canvas.create_line(
            x - radius,
            y + radius,
            x + radius,
            y - radius,
            fill=corpse_mark,
            width=1,
            tags="corpse",
        )
        self.corpse_markers[index] = (first_mark, second_mark)

    def _render_attack_effects(self) -> None:
        for attacker_index, target_index in self.simulation.attacking_pairs:
            old_effect = self.attack_effects.pop(attacker_index, None)
            if old_effect is not None:
                self.canvas.delete(old_effect[0], old_effect[1])

            attacker = self.simulation.units[attacker_index]
            target = self.simulation.units[target_index]
            start_x, start_y = self._world_to_view(attacker.x, attacker.y)
            end_x, end_y = self._world_to_view(target.x, target.y)
            color = "#ffd76a" if attacker.team == 0 else "#b7f3ff"
            beam = self.canvas.create_line(
                start_x,
                start_y,
                end_x,
                end_y,
                fill=color,
                width=2,
                arrow=tk.LAST,
                tags="attack-effect",
            )
            radius = max(6, (UNIT_RADIUS + 3) * self.view_scale)
            ring = self.canvas.create_oval(
                start_x - radius,
                start_y - radius,
                start_x + radius,
                start_y + radius,
                outline=color,
                width=2,
                tags="attack-effect",
            )
            self.attack_effects[attacker_index] = (
                beam,
                ring,
                target_index,
                self.frame_number + 4,
            )

        for attacker_index, (beam, ring, target_index, expires_at) in tuple(
            self.attack_effects.items()
        ):
            if self.frame_number >= expires_at:
                self.canvas.delete(beam, ring)
                del self.attack_effects[attacker_index]
                continue
            attacker = self.simulation.units[attacker_index]
            target = self.simulation.units[target_index]
            start_x, start_y = self._world_to_view(attacker.x, attacker.y)
            end_x, end_y = self._world_to_view(target.x, target.y)
            self.canvas.coords(beam, start_x, start_y, end_x, end_y)
            radius = max(6, (UNIT_RADIUS + 3) * self.view_scale)
            self.canvas.coords(
                ring,
                start_x - radius,
                start_y - radius,
                start_x + radius,
                start_y + radius,
            )

    def _animate(self) -> None:
        if not self.root.winfo_exists():
            return
        if self.running:
            self.simulation.step((1.0 / 30.0) * self.speed)
            self.frame_number += 1
            self._render_units()
            if self.frame_number % 6 == 0:
                self._update_dashboard()
                self._add_combat_bursts()
        self.root.after(33, self._animate)

    def _add_combat_bursts(self) -> None:
        for _ in range(4):
            unit = self.simulation.units[self.rng.randrange(len(self.simulation.units))]
            if not unit.alive:
                continue
            x, y = self._world_to_view(unit.x, unit.y)
            color = GOLD if unit.team == 0 else "#d6f6ff"
            spark = self.canvas.create_line(
                x,
                y,
                x + self.rng.uniform(-3, 3),
                y - self.rng.uniform(2, 5),
                fill=color,
                width=1,
                tags="burst",
            )
            self.particle_data.append([spark, x, y, 0])
        for particle in self.particle_data[:]:
            particle[3] = int(particle[3]) + 1
            if int(particle[3]) > 5:
                self.canvas.delete(int(particle[0]))
                self.particle_data.remove(particle)

    def _update_dashboard(self) -> None:
        alive = self.simulation.alive_counts
        for team, count in enumerate(alive):
            self.army_labels[team].config(text=f"{count:,}")
            bar = getattr(self, f"team_{team}_bar")
            bar.place(relwidth=max(0.0, count / self.simulation.team_size), relheight=1)
        self.casualty_label.config(
            text=f"{self.simulation.casualties[0]:03,}  —  "
            f"{self.simulation.casualties[1]:03,}"
        )
        total_seconds = int(self.simulation.elapsed)
        self.clock_label.config(text=f"{total_seconds // 60:02}:{total_seconds % 60:02}")
        if self.simulation.winner is not None:
            winner = self.simulation.winner
            self.running = False
            if winner == -1:
                result = "The field falls silent.\nBoth armies have been lost."
            else:
                army = "EMBER" if winner == 0 else "TIDELINE"
                result = f"{army} holds the field.\nThe battle is over."
            self.event_label.config(text=result)
            self.live_label.config(text="■  BATTLE CONCLUDED", fg=GOLD)
            self.pause_button.config(text="Ⅱ    RESUME")
        elif self.frame_number % 30 == 0 and self.selected_unit is None:
            self.event_label.config(
                text=self._battle_report(alive)
            )

    def _battle_report(self, alive: tuple[int, int]) -> str:
        fallen = self.simulation.casualties
        losses = fallen[0] + fallen[1]
        if losses == 0:
            return "Both formations advance.\nThe first contact is near."
        if abs(fallen[0] - fallen[1]) < 10:
            return f"Heavy fighting on both fronts.\n{losses:,} have fallen."
        leading = "TIDELINE" if fallen[0] > fallen[1] else "EMBER"
        remaining = alive[0] + alive[1]
        return f"{leading} is pushing forward.\n{losses:,} fallen · {remaining:,} remain."

    def _set_speed(self, speed: float) -> None:
        self.speed = speed
        self._update_speed_buttons()

    def _update_speed_buttons(self) -> None:
        for button, speed in zip(self.speed_buttons, (0.5, 1.0, 2.0)):
            active = speed == self.speed
            button.config(
                bg="#31414b" if active else "#1a252d",
                fg=TEXT if active else MUTED,
                activebackground="#3b4d58",
                activeforeground=TEXT,
            )

    def _toggle_pause(self, _event: tk.Event | None = None) -> str:
        self.running = not self.running
        if self.simulation.winner is not None and self.running:
            self._restart()
            return "break"
        self.pause_button.config(text="Ⅱ    PAUSE" if self.running else "▶    RESUME")
        self.live_label.config(
            text="●  LIVE SIMULATION" if self.running else "Ⅱ  SIMULATION PAUSED",
            fg="#8fdbad" if self.running else GOLD,
        )
        return "break"

    def _restart(self) -> None:
        try:
            team_size = self.team_size_var.get()
        except (tk.TclError, ValueError):
            messagebox.showerror(
                "Invalid army size",
                "Enter a whole number between 100 and 1,000.",
                parent=self.root,
            )
            return
        if not 100 <= team_size <= 1_000:
            messagebox.showerror(
                "Invalid army size",
                "Enter a whole number between 100 and 1,000.",
                parent=self.root,
            )
            return
        self.simulation = BattleSimulation(
            WORLD_WIDTH,
            WORLD_HEIGHT,
            team_size=team_size,
        )
        self.selected_unit = None
        self.running = True
        self.frame_number = 0
        self.pause_button.config(text="Ⅱ    PAUSE")
        self.live_label.config(text="●  LIVE SIMULATION", fg="#8fdbad")
        self._draw_battlefield()
        self._update_dashboard()

    def _close(self) -> None:
        self.root.destroy()


UNIT_DOT = UNIT_RADIUS


def main() -> None:
    root = tk.Tk()
    BattleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
