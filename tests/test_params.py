import logging
logging.disable(logging.CRITICAL)

import unittest
import mock
import sys
import os

# for finding modules in the sibling directories
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from utils.util_classes import Params
from utils.custom_exceptions import *

class TestParams(unittest.TestCase):
	"""
	Tests the Params object.		
	"""

	def test_add_key_value_pair(self):
		p = Params()
		v = "some_value"
		p.add( key = v)
		self.assertEqual(p.get("key"), v)

	def test_add_multiple_key_value_pairs(self):
		p = Params()
		v1 = "some_value"
		v2 = "other_value"
		p.add( key1 = v1, key2 = v2)
		self.assertEqual(p.get("key1"), v1)
		self.assertEqual(p.get("key2"), v2)

	def test_add_dict(self):
		p = Params()
		d = {"a":1, "b":2}
		p.add(d)
		self.assertEqual(p.get("a"), 1)
		self.assertEqual(p.get("b"), 2)

	def test_add_multiple_dicts(self):
		p = Params()
		d1 = {"a":1, "b":2}
		d2 = {"c":3, "d":4}
		p.add(d1, d2)
		self.assertEqual(p.get("a"), 1)
		self.assertEqual(p.get("b"), 2)
		self.assertEqual(p.get("c"), 3)
		self.assertEqual(p.get("d"), 4)

	def test_add_both_simultaneously(self):
		p = Params()
		v = "some_value"
		d = {"a":1, "b":2}

		p.add(d, key = v)

		self.assertEqual(p.get("a"), 1)
		self.assertEqual(p.get("b"), 2)
		self.assertEqual(p.get("key"), v)

	def test_asking_for_missing_value_kills_pipeline(self):
		p = Params()

		# add some value. Not necessary to do this.
		v = "some_value"
		p.add( key = v)
		self.assertRaises(ParameterNotFoundException, p.get, "missing_val")

	def test_reset_param(self):
		p = Params()
		v = "some_value"
		p.add( key = v)
		p.reset_param('key', 'new_value')
		self.assertEqual(p.get('key'), 'new_value')


	def test_trying_to_reset_unset_param_raises_exception(self):
		with self.assertRaises(ParameterNotFoundException):
			p = Params()
			p.reset_param('key', 'new_value')

if __name__ == "__main__":
	unittest.main()
