import math
import unittest

from battle_sim import BattleSimulation, TEAM_SIZE, UNIT_RADIUS


class BattleSimulationTests(unittest.TestCase):
    def test_starts_with_default_team_size(self) -> None:
        simulation = BattleSimulation(seed=7)

        self.assertEqual(len(simulation.units), TEAM_SIZE * 2)
        self.assertEqual(simulation.alive_counts, (TEAM_SIZE, TEAM_SIZE))
        self.assertEqual([unit.team for unit in simulation.units].count(0), TEAM_SIZE)
        self.assertEqual([unit.team for unit in simulation.units].count(1), TEAM_SIZE)

    def test_supports_configurable_army_sizes(self) -> None:
        for team_size in (100, 300, 1_000):
            with self.subTest(team_size=team_size):
                simulation = BattleSimulation(team_size=team_size, seed=7)

                self.assertEqual(len(simulation.units), team_size * 2)
                self.assertEqual(simulation.alive_counts, (team_size, team_size))
                self.assertGreaterEqual(
                    simulation.minimum_unit_distance(),
                    UNIT_RADIUS * 2.0 - 0.05,
                )

    def test_seed_makes_initial_armies_reproducible(self) -> None:
        first = BattleSimulation(team_size=20, seed=13)
        second = BattleSimulation(team_size=20, seed=13)

        self.assertEqual(
            [(unit.x, unit.y, unit.kind) for unit in first.units],
            [(unit.x, unit.y, unit.kind) for unit in second.units],
        )

    def test_units_advance_without_leaving_the_arena_or_overlapping(self) -> None:
        simulation = BattleSimulation(width=420, height=260, team_size=70, seed=3)
        left_start = sum(unit.x for unit in simulation.units[:70]) / 70
        right_start = sum(unit.x for unit in simulation.units[70:]) / 70

        for _ in range(45):
            simulation.step(0.1)

        self.assertGreater(sum(unit.x for unit in simulation.units[:70]) / 70, left_start)
        self.assertLess(sum(unit.x for unit in simulation.units[70:]) / 70, right_start)
        self.assertLess(simulation.units[0].x, 210)
        self.assertGreater(simulation.units[70].x, 210)
        self.assertGreaterEqual(
            simulation.minimum_unit_distance(),
            UNIT_RADIUS * 2.0 - 0.05,
        )
        self.assertTrue(
            all(
                UNIT_RADIUS <= unit.x <= simulation.width - UNIT_RADIUS
                and UNIT_RADIUS <= unit.y <= simulation.height - UNIT_RADIUS
                for unit in simulation.units
                if unit.alive
            )
        )
        self.assertAlmostEqual(simulation.elapsed, 4.5)

    def test_units_fight_and_simulation_concludes(self) -> None:
        simulation = BattleSimulation(width=100, height=90, team_size=8, seed=9)
        for index, unit in enumerate(simulation.units):
            unit.x = 37.0 + index % 8 * 5.0
            unit.y = 35.0 + index // 8 * 10.0
            unit.cooldown = 0.0
            unit.speed = 0.0
            unit.health = 1.0
            unit.damage = 2.0

        simulation.step(0.1)

        self.assertGreater(sum(simulation.casualties), 0)
        self.assertTrue(simulation.attacking_pairs)
        self.assertTrue(
            all(
                simulation.units[attacker].team != simulation.units[target].team
                for attacker, target in simulation.attacking_pairs
            )
        )
        while simulation.winner is None:
            simulation.step(0.1)
        self.assertIn(simulation.winner, (0, 1, -1))
        self.assertEqual(sum(simulation.alive_counts), 0)

    def test_units_without_nearby_enemies_keep_their_forward_heading(self) -> None:
        simulation = BattleSimulation(team_size=1, seed=11)
        red, blue = simulation.units
        red.x, red.y = 400.0, 100.0
        blue.x, blue.y = 800.0, 600.0
        red.speed = 50.0
        blue.speed = 0.0

        simulation.step(0.1)

        self.assertGreater(red.x, 400.0)
        self.assertLess(red.y - 100.0, 1.0)

    def test_invalid_steps_are_rejected(self) -> None:
        simulation = BattleSimulation(team_size=1, seed=4)

        for dt in (0.0, -0.1, math.inf, math.nan, 0.26):
            with self.subTest(dt=dt), self.assertRaises(ValueError):
                simulation.step(dt)


if __name__ == "__main__":
    unittest.main()
