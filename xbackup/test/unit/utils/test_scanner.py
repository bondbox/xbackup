#!/usr/bin/python3
# coding:utf-8

import os
import unittest

import mock

from ....utils.scanner import backup_scanner


class test_scanner(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.scanner = backup_scanner(None, [os.path.join("xbackup")],
                                      [os.path.join("xbackup", "test")])

    def tearDown(self):
        pass

    def test_iter(self):
        for object in self.scanner:
            self.assertIsInstance(object, backup_scanner.object)
            self.assertIsInstance(object.path, str)
            self.assertIsInstance(object.start, str)
            self.assertIsInstance(object.abspath, str)
            self.assertIsInstance(object.relpath, str)
            self.assertIsInstance(object.realpath, str)
            self.assertIsInstance(object.size, int)
            self.assertIsInstance(object.isdir, bool)
            self.assertIsInstance(object.isfile, bool)
            self.assertIsInstance(object.islink, bool)

            if object.isfile:
                self.assertIsInstance(object.md5, str)
                self.assertIsInstance(object.sha1, str)
                self.assertIsInstance(object.sha256, str)
            else:
                self.assertEqual(object.md5, None)
                self.assertEqual(object.sha1, None)
                self.assertEqual(object.sha256, None)

    def test_start(self):
        start = self.scanner.start
        self.assertIsInstance(start, str)
        self.assertEqual(start, os.getcwd())

    def test_reload(self):
        self.assertEqual(self.scanner.reload(), None)
