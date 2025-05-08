import subprocess

class Firewall:
    def __init__(self):
        self.rules = []

    def add_rule(self, rule):
        try:
            subprocess.run(['sudo', 'iptables', '-A'] + rule.split())
            self.rules.append(rule)
            return True
        except Exception as e:
            logging.error(f"Firewall rule error: {e}")
            return False

    def setup_basic_rules(self):
        rules = [
            'INPUT -p tcp --dport 5000 -j ACCEPT',  # Flask server
            'INPUT -p tcp --dport 631 -j ACCEPT',   # CUPS
            'INPUT -p tcp --dport 3128 -j ACCEPT',  # Squid
            'INPUT -j DROP'                         # Drop all other traffic
        ]
        for rule in rules:
            self.add_rule(rule)
