#!/usr/bin/python3
import unittest, client
from argparse import Namespace

class ClientUnitTests(unittest.TestCase):
	
	def test_create_dict(self):
		args = Namespace(server = '', get= '', id= '')
		self.assertEqual(len(client.Client.create_dict(self, args)), 2)
		args = Namespace(server= '', set= '', id= '')
		self.assertEqual(len(client.Client.create_dict(self, args)), 2)
		args = Namespace(server= '', print= '', id= '')
		self.assertEqual(len(client.Client.create_dict(self, args)), 2)
		args = Namespace(server= '', query_all_keys= '', id='')
		self.assertEqual(len(client.Client.create_dict(self, args)), 2)

if __name__ == '__main__':
	unittest.main()
	