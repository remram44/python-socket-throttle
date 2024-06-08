class Unlimited(object):
    def __init__(self):
        self.total = 0

    def make_available(self, min_amount, max_amount=None):
        if max_amount is None:
            max_amount = min_amount
        return max_amount

    def make_empty(self):
        pass

    def add_some(self, min_amount, max_amount=None):
        if max_amount is None:
            max_amount = min_amount
        self.total += max_amount
        return max_amount

    def add_unchecked(self, amount):
        self.total += amount
