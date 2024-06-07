import socket_throttle
import unittest


class MockedLeakyBucket(socket_throttle.LeakyBucket):
    def __init__(self, *args, **kwargs):
        self.mock_timer = 0
        self.mock_sleeps = []
        super(MockedLeakyBucket, self).__init__(*args, **kwargs)

    def _timer(self):
        return self.mock_timer

    def _sleep(self, duration):
        self.mock_sleeps.append(duration)
        self.mock_timer += duration


class TestLeakyBucket(unittest.TestCase):
    def test_leaky_bucket(self):
        bucket = MockedLeakyBucket(1, 200)

        # Under the limit
        ret = bucket.add_some(10, 150)
        self.assertEqual(ret, 150)
        self.assertEqual(bucket.mock_timer, 0)
        self.assertEqual(bucket.mock_sleeps, [])

        # This is over the limit, and will return a smaller value
        ret = bucket.add_some(10, 150)
        self.assertEqual(ret, 50)
        self.assertEqual(bucket.mock_timer, 0)
        self.assertEqual(bucket.mock_sleeps, [])

        # Since we are over the limit, we'll have to sleep, and return minimum
        ret = bucket.add_some(10, 100)
        self.assertEqual(ret, 10)
        self.assertEqual(bucket.mock_timer, 10.0)
        self.assertEqual(bucket.mock_sleeps, [10.0])

        # Wait and replenish 50
        bucket._sleep(50)
        bucket._update()
        self.assertEqual(bucket._done, 150.0)

        # Request over the limit, will sleep to empty bucket
        ret = bucket.add_some(300, 350)
        self.assertEqual(ret, 300)
        self.assertEqual(bucket.mock_timer, 210.0)
        self.assertEqual(bucket.mock_sleeps, [10.0, 50.0, 150.0])

        # This means we are now over the limit at 300
        # Request a little, it will have to sleep first
        ret = bucket.add_some(10, 20)
        self.assertEqual(ret, 10)
        self.assertEqual(bucket.mock_timer, 320.0)
        self.assertEqual(bucket.mock_sleeps, [10.0, 50.0, 150.0, 110.0])


if __name__ == '__main__':
    unittest.main()
