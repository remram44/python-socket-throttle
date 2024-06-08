import time


class LeakyBucket(object):
    def __init__(self, rate, limit):
        """An accounting object, using the "leaky bucket" algorithm.

        Operations fill a bucket, which empties at the provided `rate`. The
        bucket has a given `limit` after which operations will block, waiting
        for space in the bucket.
        """
        self.total = 0
        self._rate = rate
        self._limit = limit
        self._done = 0
        self._last = self._timer()

    _timer = time.perf_counter

    def _update(self):
        # Update current usage
        now = self._timer()
        self._done = max(0, self._done - self._rate * (now - self._last))
        self._last = now

    _sleep = time.sleep

    def make_available(self, amount):
        # If available now, return
        available = self._limit - self._done
        if available >= amount:
            return

        self._update()

        # If available now, return
        available = self._limit - self._done
        if available >= amount:
            return

        # Otherwise, sleep long enough
        replenish = min(amount - available, self._done)
        self._sleep(replenish / self._rate)

    def make_empty(self):
        if self._done == 0:
            return

        self._update()

        self._sleep(self._done / self._rate)

    def add_some(self, min_amount, max_amount=None):
        """Do a variable number of operations.

        Returns the amount that can be used now, sleeping if necessary to
        obtain at least `min_amount`.
        """
        if max_amount is None:
            max_amount = min_amount
        assert min_amount <= max_amount

        # If available now, return
        available = self._limit - self._done
        if available >= min_amount:
            amount = min(available, max_amount)
            self._done += amount
            self.total += amount
            return amount

        self._update()

        # If available now, return
        available = self._limit - self._done
        if available >= min_amount:
            amount = min(available, max_amount)
            self._done += amount
            self.total += amount
            return amount

        # Otherwise, sleep long enough for min_amount to be available
        replenish = min(min_amount - available, self._done)
        self._sleep(replenish / self._rate)

        self._done += min_amount
        self.total += min_amount
        return min_amount
