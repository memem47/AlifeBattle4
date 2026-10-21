from __future__ import annotations

import math
import random
from dataclasses import dataclass


TEAM_SIZE = 300
UNIT_RADIUS = 3.2
COLLISION_DIAMETER = UNIT_RADIUS * 2.0
CELL_SIZE = 18.0


@dataclass(slots=True)
class Unit:
    team: int
    x: float
    y: float
    speed: float
    health: float
    max_health: float
    damage: float
    attack_rate: float
    cooldown: float
    kind: int
    alive: bool = True


class BattleSimulation:
    """Lightweight artificial-life battle with spatially hashed local physics."""

    def __init__(
        self,
        width: int = 1_100,
        height: int = 720,
        team_size: int = TEAM_SIZE,
        seed: int | None = None,
    ) -> None:
        if width <= 0 or height <= 0 or team_size <= 0:
            raise ValueError("Arena dimensions and team size must be positive.")
        self.width = width
        self.height = height
        self.team_size = team_size
        self.random = random.Random(seed)
        self.units: list[Unit] = []
        self.casualties = [0, 0]
        self.elapsed = 0.0
        self.tick = 0
        self.attacking_pairs: list[tuple[int, int]] = []
        self._create_army(0)
        self._create_army(1)
        self._resolve_collisions()

    def _create_army(self, team: int) -> None:
        formation_width = self.width * 0.30
        formation_height = self.height * 0.84
        columns = max(
            1,
            round(math.sqrt(self.team_size * formation_width / formation_height)),
        )
        rows = math.ceil(self.team_size / columns)
        x_spacing = formation_width / columns
        y_spacing = formation_height / rows
        start_x = self.width * (0.06 if team == 0 else 0.64)
        start_y = (self.height - formation_height) / 2

        for index in range(self.team_size):
            column = index % columns
            row = index // columns
            mirrored_column = column if team == 0 else columns - 1 - column
            x = start_x + (mirrored_column + 0.5) * x_spacing
            y = start_y + (row + 0.5) * y_spacing
            x += self.random.uniform(-1.7, 1.7)
            y += self.random.uniform(-1.7, 1.7)
            roll = self.random.random()
            if roll < 0.17:
                kind = 0
                speed, health, damage, attack_rate = 66.0, 54.0, 12.0, 1.05
            elif roll < 0.34:
                kind = 2
                speed, health, damage, attack_rate = 38.0, 145.0, 22.0, 0.78
            else:
                kind = 1
                speed, health, damage, attack_rate = 50.0, 88.0, 15.0, 0.95
            self.units.append(
                Unit(
                    team=team,
                    x=x,
                    y=y,
                    speed=speed * self.random.uniform(0.9, 1.1),
                    health=health,
                    max_health=health,
                    damage=damage,
                    attack_rate=attack_rate,
                    cooldown=self.random.uniform(0.0, 1.0 / attack_rate),
                    kind=kind,
                )
            )

    @property
    def alive_counts(self) -> tuple[int, int]:
        return (
            self.team_size - self.casualties[0],
            self.team_size - self.casualties[1],
        )

    @property
    def winner(self) -> int | None:
        left, right = self.alive_counts
        if left == right == 0:
            return -1
        if left == 0:
            return 1
        if right == 0:
            return 0
        return None

    def step(self, dt: float = 1.0 / 30.0) -> None:
        if not math.isfinite(dt) or dt <= 0.0 or dt > 0.25:
            raise ValueError("Step duration must be finite and between 0 and 0.25 seconds.")
        if self.winner is not None:
            return

        buckets = self._build_buckets()
        damage_taken = [0.0] * len(self.units)
        self.attacking_pairs = []
        directions = (1, -1)

        for index, unit in enumerate(self.units):
            if not unit.alive:
                continue
            unit.cooldown = max(0.0, unit.cooldown - dt)
            cell_x = int(unit.x // CELL_SIZE)
            cell_y = int(unit.y // CELL_SIZE)
            nearest_index = -1
            nearest_distance_sq = 24.0 * 24.0
            separation_x = 0.0
            separation_y = 0.0
            nearby_indices: list[int] = []

            for grid_y in range(cell_y - 1, cell_y + 2):
                for grid_x in range(cell_x - 1, cell_x + 2):
                    for other_index in buckets.get((grid_x, grid_y), ()):
                        if other_index == index:
                            continue
                        nearby_indices.append(other_index)
                        other = self.units[other_index]
                        if not other.alive:
                            continue
                        dx = unit.x - other.x
                        dy = unit.y - other.y
                        distance_sq = dx * dx + dy * dy
                        if other.team != unit.team and distance_sq < nearest_distance_sq:
                            nearest_index = other_index
                            nearest_distance_sq = distance_sq
                        if distance_sq < (UNIT_RADIUS * 2.0) ** 2:
                            if distance_sq < 0.0001:
                                angle = (index * 2.399963229728653) % math.tau
                                dx, dy, distance_sq = math.cos(angle), math.sin(angle), 1.0
                            distance = math.sqrt(distance_sq)
                            strength = (UNIT_RADIUS * 2.0 - distance) / distance
                            separation_x += dx * strength
                            separation_y += dy * strength

            if nearest_index >= 0:
                nearest = self.units[nearest_index]
                dx, dy = nearest.x - unit.x, nearest.y - unit.y
                distance = math.sqrt(max(nearest_distance_sq, 0.0001))
                if distance <= 15.0:
                    if unit.cooldown <= 0.0:
                        damage_taken[nearest_index] += unit.damage
                        unit.cooldown = 1.0 / unit.attack_rate
                        self.attacking_pairs.append((index, nearest_index))
                    desired_x = directions[unit.team] * 0.12
                    desired_y = 0.0
                else:
                    desired_x = dx / distance
                    desired_y = dy / distance
            else:
                desired_x = directions[unit.team]
                desired_y = (self.height * 0.5 - unit.y) / self.height * 0.18

            wall_margin = min(18.0, self.width * 0.08, self.height * 0.08)
            if unit.x < wall_margin:
                desired_x += (wall_margin - unit.x) / wall_margin * 2.0
            elif unit.x > self.width - wall_margin:
                desired_x -= (unit.x - (self.width - wall_margin)) / wall_margin * 2.0
            if unit.y < wall_margin:
                desired_y += (wall_margin - unit.y) / wall_margin * 2.0
            elif unit.y > self.height - wall_margin:
                desired_y -= (unit.y - (self.height - wall_margin)) / wall_margin * 2.0

            movement_x = desired_x + separation_x * 0.85
            movement_y = desired_y + separation_y * 0.85
            movement_x = max(movement_x, 0.08) if unit.team == 0 else min(movement_x, -0.08)
            movement_length = math.hypot(movement_x, movement_y)
            if movement_length > 1.0:
                movement_x /= movement_length
                movement_y /= movement_length
            next_x = min(
                self.width * 0.96 if unit.team == 1 else self.width - UNIT_RADIUS,
                max(
                    self.width * 0.04 if unit.team == 0 else UNIT_RADIUS,
                    unit.x + movement_x * unit.speed * dt,
                ),
            )
            next_y = min(
                self.height - UNIT_RADIUS,
                max(UNIT_RADIUS, unit.y + movement_y * unit.speed * dt),
            )
            collides = False
            for other_index in nearby_indices:
                other = self.units[other_index]
                if not other.alive:
                    continue
                dx, dy = next_x - other.x, next_y - other.y
                if dx * dx + dy * dy < COLLISION_DIAMETER * COLLISION_DIAMETER:
                    collides = True
                    break
            if not collides:
                unit.x, unit.y = next_x, next_y

        for index, damage in enumerate(damage_taken):
            unit = self.units[index]
            if damage and unit.alive:
                unit.health -= damage
                if unit.health <= 0.0:
                    unit.alive = False
                    self.casualties[unit.team] += 1

        self._resolve_collisions()
        self.tick += 1
        self.elapsed += dt

    def _build_buckets(self) -> dict[tuple[int, int], list[int]]:
        buckets: dict[tuple[int, int], list[int]] = {}
        for index, unit in enumerate(self.units):
            if unit.alive:
                key = (int(unit.x // CELL_SIZE), int(unit.y // CELL_SIZE))
                buckets.setdefault(key, []).append(index)
        return buckets

    def _resolve_collisions(self) -> None:
        neighbor_offsets = ((0, 0), (0, 1), (1, -1), (1, 0), (1, 1))
        minimum_distance = COLLISION_DIAMETER
        minimum_distance_sq = minimum_distance * minimum_distance
        for _ in range(2):
            buckets = self._build_buckets()
            for (cell_x, cell_y), indices in buckets.items():
                for grid_offset_x, grid_offset_y in neighbor_offsets:
                    neighbors = buckets.get(
                        (cell_x + grid_offset_x, cell_y + grid_offset_y), ()
                    )
                    for index in indices:
                        unit = self.units[index]
                        for other_index in neighbors:
                            if (
                                grid_offset_x == grid_offset_y == 0
                                and other_index <= index
                            ):
                                continue
                            other = self.units[other_index]
                            dx, dy = other.x - unit.x, other.y - unit.y
                            distance_sq = dx * dx + dy * dy
                            if distance_sq >= minimum_distance_sq:
                                continue
                            if distance_sq < 0.0001:
                                angle = (
                                    index * 2.399963229728653
                                    + other_index * 4.117140968
                                ) % math.tau
                                dx, dy, distance_sq = math.cos(angle), math.sin(angle), 1.0
                            distance = math.sqrt(distance_sq)
                            push = (minimum_distance - distance) * 0.51 / distance
                            push_x, push_y = dx * push, dy * push
                            unit_min_x = self.width * 0.04 if unit.team == 0 else UNIT_RADIUS
                            unit_max_x = self.width * 0.96 if unit.team == 1 else self.width - UNIT_RADIUS
                            other_min_x = self.width * 0.04 if other.team == 0 else UNIT_RADIUS
                            other_max_x = self.width * 0.96 if other.team == 1 else self.width - UNIT_RADIUS
                            unit.x = min(unit_max_x, max(unit_min_x, unit.x - push_x))
                            unit.y = min(
                                self.height - UNIT_RADIUS,
                                max(UNIT_RADIUS, unit.y - push_y),
                            )
                            other.x = min(other_max_x, max(other_min_x, other.x + push_x))
                            other.y = min(
                                self.height - UNIT_RADIUS,
                                max(UNIT_RADIUS, other.y + push_y),
                            )

    def minimum_unit_distance(self) -> float:
        """Return the smallest alive-unit separation; useful for physics checks."""
        minimum = math.inf
        buckets = self._build_buckets()
        for index, unit in enumerate(self.units):
            if not unit.alive:
                continue
            cell_x = int(unit.x // CELL_SIZE)
            cell_y = int(unit.y // CELL_SIZE)
            for grid_y in range(cell_y - 1, cell_y + 2):
                for grid_x in range(cell_x - 1, cell_x + 2):
                    for other_index in buckets.get((grid_x, grid_y), ()):
                        if other_index <= index:
                            continue
                        other = self.units[other_index]
                        minimum = min(minimum, math.hypot(unit.x - other.x, unit.y - other.y))
        return minimum
