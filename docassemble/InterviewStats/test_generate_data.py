import unittest


class GenerateData(unittest.TestCase):

    def test_nothing(self):
        # Empty test case, as pytests fails if there are no tests found.
        # Can't easily test any other files as they all try to load docassemble's db
        pass
