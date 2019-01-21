import sys
import unittest

suite = unittest.TestLoader().discover(
    'spat.tests',
    pattern='test_*.py',
    )
result = unittest.TextTestRunner(verbosity=1).run(suite)

if result.wasSuccessful():
    sys.exit()
else:
    problems = len(result.failures) + len(result.errors)
    sys.exit(problems)

