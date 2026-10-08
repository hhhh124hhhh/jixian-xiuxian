"""风险修炼数值与边界测试。运行：python -m unittest discover -s tests/unit -p test_risk_run.py"""
import unittest
from core.risk_run import RiskRun, FIRE_RATES, PILL_QUOTA, CULTIVATION_QUOTA, LIFESPAN


class ControlledRandom:
    def __init__(self, rolls=None, tides=None):
        self.rolls = iter(rolls or [])
        self.tides = iter(tides or [])

    def random(self):
        return next(self.rolls, 0.99)

    def randrange(self, n):
        return next(self.tides, 0) % n


class RiskRunTests(unittest.TestCase):
    def test_locked_probabilities_and_limits(self):
        self.assertEqual(FIRE_RATES, (0, 5, 10, 15, 22, 30, 40))
        self.assertEqual((PILL_QUOTA, CULTIVATION_QUOTA), (6, 12))
        self.assertEqual(RiskRun(ControlledRandom()).chance, 50)

    def test_bank_spends_quota_and_low_combo_cannot_loop_forever(self):
        run = RiskRun(ControlledRandom())
        for _ in range(2):
            self.assertTrue(run.act("breathe")["success"])
        self.assertEqual(run.pending_exp, 40)
        self.assertTrue(run.act("bank")["success"])
        self.assertEqual(run.s.exp, 40)
        self.assertEqual(run.s.quota, 9)
        for _ in range(3):
            run.act("breathe")
            run.act("bank")
        self.assertEqual(run.s.quota, 0)
        self.assertEqual(run.s.exp, 160)
        self.assertFalse(run.can("breathe"))

    def test_tide_bonus_is_revealed_then_requires_its_threshold(self):
        run = RiskRun(ControlledRandom(tides=[1, 0]))
        self.assertEqual(run.s.tide, 1)
        for _ in range(4):
            run.act("breathe")
        run.act("bank")
        self.assertEqual(run.s.exp, 220)  # 4² * 10 + 60
        self.assertEqual(run.s.tide, 0)

    def test_discount_requires_three_combo_and_is_single_use(self):
        run = RiskRun(ControlledRandom(tides=[2, 0]))
        for _ in range(3):
            run.act("breathe")
        run.act("bank")
        self.assertTrue(run.s.discount)
        self.assertEqual(run.s.exp, 90)
        run.act("brew")
        self.assertEqual(run.s.exp, 70)
        self.assertFalse(run.s.discount)
        run.act("brew")
        self.assertEqual(run.s.exp, 30)

    def test_brewing_is_not_free_and_three_pills_guarantee_tribulation(self):
        run = RiskRun(ControlledRandom(rolls=[0.99]))
        run.s.exp = 250
        for _ in range(3):
            self.assertTrue(run.act("brew")["success"])
        self.assertEqual(run.s.exp, 130)
        self.assertEqual(run.s.life, LIFESPAN - 6)
        self.assertEqual(run.chance, 100)  # 理论 101%，有效 100%
        self.assertTrue(run.act("tribulate")["success"])
        self.assertEqual(run.s.realm, 1)
        self.assertEqual((run.s.quota, run.s.life, run.s.made, run.s.pills), (12, 22, 0, 0))

    def test_two_failure_guarantees_then_half_exp_penalty(self):
        run = RiskRun(ControlledRandom(rolls=[0.99, 0.99, 0.99]))
        run.s.exp = 101
        for expected_fails in (1, 2):
            run.act("tribulate")
            self.assertEqual(run.s.exp, 101)
            self.assertEqual(run.s.fails, expected_fails)
        run.act("tribulate")
        self.assertEqual(run.s.exp, 50)  # ceil(101/2) = 51

    def test_demon_interrupts_until_one_of_three_choices(self):
        run = RiskRun(ControlledRandom(rolls=[0.99, 0.99, 0.99, 0.0]))
        for _ in range(3):
            run.act("breathe")
        run.act("breathe")
        self.assertEqual(run.s.phase, "demon")
        self.assertEqual(run.s.demon_prior, 3)
        self.assertFalse(run.can("breathe"))
        self.assertTrue(run.can("demon_calm"))
        run.act("demon_calm")
        self.assertEqual(run.s.exp, 45)
        self.assertEqual(run.s.phase, "playing")
        self.assertEqual(run.s.combo, 0)

    def test_no_unbankable_last_breath(self):
        run = RiskRun(ControlledRandom())
        run.s.quota = 1
        before = run.s.actions
        self.assertFalse(run.act("breathe")["success"])
        self.assertEqual(run.s.actions, before)

    def test_life_and_quota_dead_end_is_a_loss(self):
        run = RiskRun(ControlledRandom())
        run.s.quota = 2
        run.act("breathe")
        run.act("bank")
        self.assertEqual(run.s.phase, "lost")

    def test_refining_cap_six_pills(self):
        run = RiskRun(ControlledRandom())
        run.s.exp = 1000
        for _ in range(6):
            run.act("brew")
        self.assertEqual((run.s.pills, run.s.made), (6, 6))
        self.assertFalse(run.can("brew"))


if __name__ == "__main__":
    unittest.main()
