#!/usr/bin/env python
# -*- coding: UTF-8 -*-


import os
import sys
import logging
import unittest

from mock import Mock
from mock import ANY
from mock import patch

from sanji.connection.mockup import Mockup
from sanji.message import Message

from voluptuous import er

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../")
    from index import Index
except ImportError as e:
    print "Please check the python PATH for import test module. (%s)" \
        % __file__
    exit(1)


class TestIndexClass(unittest.TestCase):

    def setUp(self):
        root_path = os.path.dirname(os.path.realpath(__file__)) + "/../"
        try:
            os.unlink(root_path + "data/ntp.json")
            os.unlink(root_path + "data/ntp.json.backup")
        except:
            pass
        self.index = Index(connection=Mockup())

    def tearDown(self):
        self.index.stop()
        self.index = None

    def test_get(self):
        result = {
            "time": "2015-03-26T16:27:48.611441Z",
            "timezone": "Asia/Taipei",
            "ntp": {
                "enable": 0,
                "server": "pool.ntp.org",
                "interval": 7200
            }
        }
        resp = Mock()
        with patch("index.SysTime.get_system_time") as get_system_time:
            get_system_time.return_value = "2015-03-26T16:27:48.611441Z"
            self.index.get(message=None, response=resp, test=True)
        resp.assert_called_once_with(data=result)

    def test_put_schema__should_pass(self):
        # arrange
        SUT = {
            "time": "2015-03-26T16:27:48.611441Z",
            "timezone": "Asia/Taipei",
            "ntp": {
                "enable": True,
                "server": "pool.ntp.org",
                "interval": 7200
            }
        }

        # act
        data = Index.PUT_SCHEMA(SUT)

        # assert
        self.assertEqual(SUT, data)

    def test_put_schema__time_empty_should_fail(self):
        # arrange
        SUT = {
            "time": ""
        }

        # act
        with self.assertRaises(er.MultipleInvalid):
            Index.PUT_SCHEMA(SUT)

    def test_put(self):
        result = {
            "time": ANY,
            "timezone": ANY,
            "ntp": {
                "enable": ANY,
                "server": ANY,
                "interval": ANY
            }
        }

        # case 1: no input parameters
        resp = Mock()
        msg = Message({"data": {}})
        self.index.put(message=msg, response=resp, test=True)
        resp.assert_called_once_with(code=400,
                                     data={"message": "No input paramters."})

        # case 2: change timezone (Normal)
        with patch("index.SysTime.set_system_timezone") as set_system_timezone:
            resp = Mock()
            set_system_timezone.return_value = True
            msg = Message({"data": {"timezone": "Asia/Taipei"}})
            self.index.put(message=msg, response=resp, test=True)
            resp.assert_called_once_with(data=result)

        # case 3: change timezone (Abnormal 1)
            resp = Mock()
            set_system_timezone.return_value = False
            msg = Message({"data": {"timezone": "Asia/Taipei"}})
            self.index.put(message=msg, response=resp, test=True)
            resp.assert_called_once_with(
                code=500, data={"message": "Change timezone failed."})

        # case 4: change timezone (Abnormal 2)
        resp = Mock()
        msg = Message({"data": {"timezone": "Asia/Taipe"}})
        self.index.put(message=msg, response=resp, test=True)
        resp.assert_called_once_with(
            code=400, data={"message": "Timezone not exist."})

        # case 5: change system time (Normal)
        with patch("index.SysTime.set_system_time") as set_system_time:
            resp = Mock()
            set_system_time.return_value = True
            msg = Message(
                {"data": {"time": "2015-03-26T16:27:48.611441Z"}})
            self.index.put(message=msg, response=resp, test=True)
            resp.assert_called_once_with(data=result)

        # case 6: change system time (Abnormal 1)
            resp = Mock()
            set_system_time.return_value = False
            self.index.put(message=msg, response=resp, test=True)
            resp.assert_called_once_with(
                code=500, data={"message": "Change system time failed."})

        # case 7: update ntp settings (Normal)
        with patch.object(self.index.ntp, "update") as update:
            resp = Mock()
            update.return_value = True
            msg = Message({
                "data": {
                    "ntp": {}
                    }
                })
            self.index.put(message=msg, response=resp, test=True)
            resp.assert_called_once_with(data=result)

        # case 8: update ntp settings (Abnormal 1)
            resp = Mock()
            update.return_value = False
            self.index.put(message=msg, response=resp, test=True)
            resp.assert_called_once_with(
                code=500, data={"message": "Update ntp settings failed."})

        # case 9: update ntp settings (Abnormal 2)
            resp = Mock()
            update.side_effect = RuntimeError("Some exception.")
            self.index.put(message=msg, response=resp, test=True)
            resp.assert_called_once_with(
                code=400, data={"message": "Some exception."})


if __name__ == "__main__":
    FORMAT = "%(asctime)s - %(levelname)s - %(lineno)s - %(message)s"
    logging.basicConfig(level=0, format=FORMAT)
    logger = logging.getLogger("Index")
    unittest.main()
