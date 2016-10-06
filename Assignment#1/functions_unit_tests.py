#!/usr/bin/python3
import unittest, functions

class FunctionsUnitTests(unittest.TestCase):

	def test_set(self):
		functions.rpc_dict = {}
		key = 'dog'
		value = 'happy'
		functions.set(key, value)
		self.assertEqual(functions.rpc_dict, {key: value})

		key = 'dog'
		value = 'sad'
		functions.set(key, value)
		self.assertEqual(functions.rpc_dict, {key: value})

		key = 'cat'
		value = 'ambivalent'
		functions.set(key, value)
		self.assertTrue(key in functions.rpc_dict)
		self.assertEqual(functions.rpc_dict[key], value)

	def test_get(self):
		functions.rpc_dict = {}
		key = 'monkey'
		self.assertEqual(functions.get(key), None)

		functions.rpc_dict['monkey'] = 'bananas'
		self.assertTrue(type(functions.get(key)) is str)

	def test_query_all_keys(self):
		functions.rpc_dict = {}
		self.assertTrue(functions.query_all_keys() is None)

		functions.rpc_dict['C#'] = '1'
		functions.rpc_dict['Python'] = '2'
		functions.rpc_dict['OCaml'] = '3'
		functions.rpc_dict['SML'] = '4'

		self.assertEqual(len(functions.query_all_keys()), 4)

if __name__ == '__main__':
	unittest.main()
	

