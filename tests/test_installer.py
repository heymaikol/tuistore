import unittest

from tuistore.installer import classify, make
from tuistore.platform import Env


class TestDnfYumClassification(unittest.TestCase):
    """dnf and yum are distinct binaries with independent availability —
    legacy RHEL-family boxes (RHEL7, CentOS7, Amazon Linux 2) only ship
    yum, and a `yum install` line must be gated on `yum` being present,
    not `dnf`."""

    def test_yum_install_classifies_as_yum_not_dnf(self):
        self.assertEqual(classify("sudo yum install mytool"), "yum")

    def test_dnf_install_still_classifies_as_dnf(self):
        self.assertEqual(classify("sudo dnf install mytool"), "dnf")

    def test_yum_only_environment_reports_yum_method_available(self):
        # RHEL7 / CentOS7 / Amazon Linux 2: yum present, dnf absent.
        env = Env("linux", "centos", {"rhel"}, "x86_64", tools={"yum"})
        cmd = "sudo yum install mytool"
        kind = classify(cmd)
        method = make(kind, cmd, source="readme")
        self.assertTrue(method.available(env))
        self.assertEqual(method.why_unavailable(env), "")

    def test_yum_only_environment_does_not_offer_dnf_method(self):
        env = Env("linux", "centos", {"rhel"}, "x86_64", tools={"yum"})
        method = make("dnf", "sudo dnf install mytool", source="readme")
        self.assertFalse(method.available(env))
        self.assertEqual(method.why_unavailable(env), "needs dnf")

    def test_dnf_only_environment_does_not_offer_yum_method(self):
        env = Env("linux", "fedora", {"fedora", "rhel"}, "x86_64", tools={"dnf"})
        method = make("yum", "sudo yum install mytool", source="readme")
        self.assertFalse(method.available(env))
        self.assertEqual(method.why_unavailable(env), "needs yum")

    def test_dnf_environment_still_offers_dnf_method(self):
        env = Env("linux", "fedora", {"fedora", "rhel"}, "x86_64", tools={"dnf"})
        method = make("dnf", "sudo dnf install mytool", source="readme")
        self.assertTrue(method.available(env))


if __name__ == "__main__":
    unittest.main()
