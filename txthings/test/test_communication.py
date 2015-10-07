'''
Created on 04-10-2015

@author: Maciej Wasilak
'''
from twisted.internet import defer, reactor
from twisted.trial import unittest
from twisted.test import proto_helpers
from txthings import coap
from txthings import resource

SERVER_ADDRESS = "192.168.37.137"
SERVER_PORT = 5683

CLIENT_ADDRESS = "192.168.37.2"
CLIENT_PORT = 61616

PAYLOAD = "123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 "

class FakeTwoWayDatagramTransport:

    def __init__(self, recipient, address, port):
        self.recipient = recipient
        self.address = address
        self.port = port

    def write(self, packet, addr):
        reactor.callLater(0.1, self.recipient.datagramReceived, packet, (self.address, self.port))


class TextResource (resource.CoAPResource):

    def __init__(self):
        resource.CoAPResource.__init__(self)
        self.text = PAYLOAD

    def render_GET(self, request):
        response = coap.Message(code=coap.CONTENT, payload='%s' % (self.text,))
        return defer.succeed(response)

class TestGetRemoteResource(unittest.TestCase):
    """This is a very high-level test case which tests blockwise exchange between
       client and server."""

    def setUp(self):
        
        root = resource.CoAPResource()
        text = TextResource()
        root.putChild('text', text)
        server_endpoint = resource.Endpoint(root)
        self.server_protocol = coap.Coap(server_endpoint)
        
        client_endpoint = resource.Endpoint(None)
        self.client_protocol = coap.Coap(client_endpoint)
        
        self.server_transport = FakeTwoWayDatagramTransport(recipient=self.client_protocol, address=SERVER_ADDRESS, port=SERVER_PORT)
        self.client_transport = FakeTwoWayDatagramTransport(recipient=self.server_protocol, address=CLIENT_ADDRESS, port=CLIENT_PORT)
        
        self.client_protocol.transport = self.client_transport
        self.server_protocol.transport = self.server_transport
        
    def test_exchange(self):
        request = coap.Message(code=coap.GET)
        request.opt.uri_path = ('text',)
        request.remote = (SERVER_ADDRESS, SERVER_PORT)
        d = self.client_protocol.request(request)
        d.addCallback(self.evaluateResponse)
        return d
        
    def evaluateResponse(self, response):
        for value in self.client_protocol.recent_local_ids.itervalues():
            value[1].cancel()
        for value in self.server_protocol.recent_remote_ids.itervalues():
            value[1].cancel()
        self.assertEqual(response.payload, PAYLOAD)
