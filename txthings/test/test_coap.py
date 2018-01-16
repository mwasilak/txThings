'''
Created on 16-10-2012

@author: Maciej Wasilak
'''
from twisted.trial import unittest
from txthings import coap
import six

class TestMessage(unittest.TestCase):

    def test_encode(self):
        msg1 = coap.Message(mtype=coap.CON, mid=0)
        binary1 = (chr(64)+chr(0)+chr(0)+chr(0)).encode()
        self.assertEqual(msg1.encode(), binary1, "wrong encode operation for empty CON message")

        msg2 = coap.Message(mtype=coap.ACK, mid=0xBC90, code=coap.CONTENT, payload=b"temp = 22.5 C", token=b'q')
        msg2.opt.etag = b"abcd"
        binary2 = (six.int2byte(97)+six.int2byte(69)+six.int2byte(188)+six.int2byte(144)+six.int2byte(113)+six.int2byte(68)+b"abcd"+six.int2byte(255)+b"temp = 22.5 C")
        self.assertEqual(msg2.encode(), binary2, "wrong encode operation for ACK message with payload, and Etag option")

        msg3 = coap.Message()
        self.assertRaises(TypeError, msg3.encode)

    def test_decode(self):
        rawdata1 = (chr(64)+chr(0)+chr(0)+chr(0)).encode()
        self.assertEqual(coap.Message.decode(rawdata1).mtype, coap.CON, "wrong message type for decode operation")
        self.assertEqual(coap.Message.decode(rawdata1).mid, 0, "wrong message ID for decode operation")
        self.assertEqual(coap.Message.decode(rawdata1).code, coap.EMPTY, "wrong message code for decode operation")
        self.assertEqual(coap.Message.decode(rawdata1).token, b'', "wrong message token for decode operation")
        self.assertEqual(coap.Message.decode(rawdata1).payload, '', "wrong message payload for decode operation")
        rawdata2 = (six.int2byte(97)+six.int2byte(69)+six.int2byte(188)+six.int2byte(144)+six.int2byte(113)+six.int2byte(68)+b"abcd"+six.int2byte(255)+b"temp = 22.5 C")
        self.assertEqual(coap.Message.decode(rawdata2).mtype, coap.ACK, "wrong message type for decode operation")
        self.assertEqual(coap.Message.decode(rawdata2).mid, 0xBC90, "wrong message ID for decode operation")
        self.assertEqual(coap.Message.decode(rawdata2).code, coap.CONTENT, "wrong message code for decode operation")
        self.assertEqual(coap.Message.decode(rawdata2).token, b'q', "wrong message token for decode operation")
        self.assertEqual(coap.Message.decode(rawdata2).payload, b'temp = 22.5 C', "wrong message payload for decode operation")
        self.assertEqual(coap.Message.decode(rawdata2).opt.etags, [b"abcd"], "problem with etag option decoding for decode operation")
        self.assertEqual(len(coap.Message.decode(rawdata2).opt._options), 1, "wrong number of options after decode operation")

class TestReadExtendedFieldValue(unittest.TestCase):

    def test_readExtendedFieldValue(self):
        arguments = ((0, b"aaaa"),
                     (0, b""),
                     (1, b"aaaa"),
                     (12,b"aaaa"),
                     (13,b"aaaa"),
                     (13,b"a"),
                     (14,b"aaaa"),
                     (14,b"aa"))
        results = ((0, b"aaaa"),
                   (0, b""),
                   (1, b"aaaa"),
                   (12,b"aaaa"),
                   (110,b"aaa"),
                   (110,b""),
                   (25198,b"aa"),
                   (25198,b""))

        for argument, result in zip(arguments, results):
            self.assertEqual(coap.readExtendedFieldValue(argument[0], argument[1]), result,'wrong result for value : '+ str(argument[0]) + ' , rawdata : ' + argument[1].decode())


class TestUintOption(unittest.TestCase):

    def test_encode(self):
        arguments = (0,
                     1,
                     2,
                     40,
                     50,
                     255,
                     256,
                     1000)
        results =   (b"",
                     chr(1).encode(),
                     chr(2).encode(),
                     chr(40).encode(),
                     chr(50).encode(),
                     six.int2byte(255),
                     six.int2byte(1) + six.int2byte(0),
                     six.int2byte(3) + six.int2byte(232))
        for argument, result in zip(arguments, results):
            self.assertEqual(coap.UintOption(0,argument).encode(), result,'wrong encode operation for option value : '+ str(argument))

    def test_decode(self):
        arguments = (b"",
                     chr(1).encode(),
                     chr(2).encode(),
                     chr(40).encode(),
                     chr(50).encode(),
                     six.int2byte(255),
                     six.int2byte(1) + six.int2byte(0),
                     six.int2byte(3) + six.int2byte(232))
        results =   (0,
                     1,
                     2,
                     40,
                     50,
                     255,
                     256,
                     1000)
        for argument, result in zip(arguments, results):
            self.assertEqual(coap.UintOption(0).decode(argument).value, result,'wrong decode operation for rawdata : '+ str(argument))

    def test_length(self):
        arguments = (0,
                     1,
                     2,
                     40,
                     50,
                     255,
                     256,
                     1000)
        results =   (0,
                     1,
                     1,
                     1,
                     1,
                     1,
                     2,
                     2)
        for argument, result in zip(arguments, results):
            self.assertEqual(coap.UintOption(0,argument)._length(), result,'wrong length for option value : '+ str(argument))


class TestOptions(unittest.TestCase):

    def test_setUriPath(self):
        opt1 = coap.Options()
        opt1.uri_path = [b"core"]
        self.assertEqual(len(opt1.getOption(coap.URI_PATH)), 1, 'wrong uri_path setter operation for single string argument')
        self.assertEqual(opt1.getOption(coap.URI_PATH)[0].value, b"core", 'wrong uri_path setter operation for single string argument')
        opt2 = coap.Options()
        opt2.uri_path = (b"core",b".well-known")
        self.assertEqual(len(opt2.getOption(coap.URI_PATH)), 2, 'wrong uri_path setter operation for 2-element tuple argument')
        self.assertEqual(opt2.getOption(coap.URI_PATH)[0].value, b"core", 'wrong uri_path setter operation for 2-element tuple argument')
        self.assertEqual(opt2.getOption(coap.URI_PATH)[1].value, b".well-known", 'wrong uri_path setter operation for 2-element tuple argument')
        opt3 = coap.Options()
        self.assertRaises(ValueError, setattr, opt3, "uri_path", b"core")


