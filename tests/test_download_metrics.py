import unittest
from download_metrics import PullSpeedMeter, format_transfer_speed

class PullSpeedMeterTests(unittest.TestCase):
    def setUp(self):
        self.t = [0.0]
        self.meter = PullSpeedMeter(clock=lambda: self.t[0])
    def ev(self, status="pulling abc", digest="sha256:abc", completed=0, total=10_000_000):
        return {"status": status, "digest": digest, "completed": completed, "total": total}
    def test_exact_transfer_units(self):
        self.meter.observe(self.ev(completed=1000000))
        self.t[0] = 2
        report = self.meter.observe(self.ev(completed=3000000))
        self.assertEqual(report['speed_bps'], 1_000_000)
        self.assertEqual(format_transfer_speed(report['speed_bps']), '1.00 MB/s    ·    8.0 Mbps')
    def test_stall_zeroes_speed_without_events(self):
        self.meter.observe(self.ev(completed=0))
        self.t[0] = 1
        self.meter.observe(self.ev(completed=1000000))
        self.t[0] = 5
        report = self.meter.snapshot()
        self.assertEqual(report['speed_bps'],0)
        self.assertEqual(report['idle_seconds'],4)
    def test_layer_change_does_not_spike(self):
        self.meter.observe(self.ev(completed=8000000))
        self.t[0] = 2
        self.meter.observe(self.ev(completed=10000000))
        self.t[0] = 3
        report = self.meter.observe(self.ev(digest="sha256:def",completed=500000,total=5000000))
        self.assertIsNone(report['speed_bps'])
    def test_resume_regression_resets(self):
        self.meter.observe(self.ev(completed=8000000))
        self.t[0]=1
        report = self.meter.observe(self.ev(completed=5000000))
        self.assertIsNone(report['speed_bps'])
    def test_verification_and_ready_hide_speed(self):
        self.meter.observe(self.ev(completed=0))
        self.t[0]=1
        self.meter.observe(self.ev(completed=1000000))
        self.assertEqual(self.meter.observe({'status':'verifying sha256 digest'})['phase'], 'verifying')
        self.assertIsNone(self.meter.snapshot()['speed_bps'])
        self.assertEqual(self.meter.observe({'status':'success'})['phase'],'ready')
    def test_speed_na_until_second_sample(self):
        self.assertEqual(format_transfer_speed(None), '— MB/s    ·    — Mbps')
        self.assertIsNone(self.meter.observe(self.ev(completed=50))['speed_bps'])
    def test_poll_does_not_read_other_network_usage(self):
        self.meter.observe({'status':'pulling manifest'})
        self.assertEqual(self.meter.snapshot()['phase'], 'preparing')
