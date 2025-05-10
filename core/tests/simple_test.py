from django.test import TestCase

class SimpleTest(TestCase):
    databases = {'core'}
    
    def test_basic_example(self):
        """A very basic test that should always pass"""
        self.assertEqual(1 + 1, 2) 