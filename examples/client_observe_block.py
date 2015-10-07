'''
Created on 20-09-2015

@author: Maciej Wasilak
'''

import sys

from twisted.internet.defer import Deferred
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.python import log

import txthings.coap as coap
import txthings.resource as resource


class Agent():
    """
    Example class which performs single GET request to coap://vs0.inf.ethz.ch
    port 5683 (official IANA assigned CoAP port), URI "obs-large".
    This resource supports observation, and sends large (multi-block) 
    notifications.
    """

    def __init__(self, protocol):
        self.protocol = protocol
        reactor.callLater(1, self.requestResource)

    def requestResource(self):
        request = coap.Message(code=coap.GET)
        #Send request to "coap://iot.eclipse.org:5683/obs-large"
        request.opt.uri_path = ('obs-large',)
        request.opt.observe = 0
        request.remote = ('198.41.30.241', coap.COAP_PORT)
        d = protocol.request(request, observeCallback=self.printLaterResponse, 
                             observeCallbackArgs=('*** OBSERVE NOTIFICATION BEGIN ***',),
                             observeCallbackKeywords={'footer':'*** OBSERVE NOTIFICATION END ***'})
        d.addCallback(self.printResponse)
        d.addErrback(self.noResponse)

    def printResponse(self, response):
        print '*** FIRST RESPONSE BEGIN ***'
        print response.payload
        print '*** FIRST RESPONSE END ***'

    def printLaterResponse(self, response, header, footer):
        print header
        print response.payload
        print footer

    def noResponse(self, failure):
        print '*** FAILED TO FETCH RESOURCE'
        print failure
        #reactor.stop()

log.startLogging(sys.stdout)

endpoint = resource.Endpoint(None)
protocol = coap.Coap(endpoint)
client = Agent(protocol)

reactor.listenUDP(0, protocol)
reactor.run()
