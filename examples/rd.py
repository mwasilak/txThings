"""
Resource Directory example

Simple Resource Directory (draft-ietf-core-resource-directory-01) implementation for txThings

Supports register, update, remove.
Supports resource lookup and endpoint lookup.
No support for simple directory
No support for groups.
No support for domain lookup.

Created on 25-08-2014

@author: Maciej Wasilak
"""

import sys
import fnmatch

from twisted.internet import defer
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.python import log

import txthings.coap as coap
import txthings.resource as resource
import txthings.ext.link_header as link_header


DEFAULT_LIFETIME = 86400

def parseUriQuery(query_list):
    query_dict = {}
    for query in query_list:
        name, value = query.split('=',1)
        if name in query_dict:
            raise ValueError('Multiple query segments with same name')
        else:
            query_dict[name] = value
    return query_dict

class DirectoryResource (resource.CoAPResource):
    """
    This class implements Registration function (point 5.2 of the draft).
    """

    def __init__(self):
        resource.CoAPResource.__init__(self)
        self.visible = True
        self.addParam(resource.LinkParam("title", "Resource Directory"))
        self.directory = {}
        self.eid = 0

    def render_POST(self, request):
        """
        Add new entry to resource directory.
        """
        if request.opt.content_format is not coap.media_types_rev['application/link-format']:
            log.msg('Unsupported content-format!')
            response = coap.Message(code=coap.UNSUPPORTED_CONTENT_FORMAT, payload='')
            return defer.succeed(response)
        try:
            params = parseUriQuery(request.opt.uri_query)
        except ValueError:
            log.msg("Bad or ambiguous query options!")
            response = coap.Message(code=coap.BAD_REQUEST, payload="Bad or ambiguous query options!")
            return defer.succeed(response)

        if 'ep' not in params:
            log.msg("No 'ep' query option in request.")
            response = coap.Message(code=coap.BAD_REQUEST, payload="No 'ep' query option in request.")
            return defer.succeed(response)
        endpoint = params['ep']
        
        if endpoint in self.directory:
            del self.children[self.directory[endpoint]]
        else:
            self.directory[endpoint] = str(self.eid)
            self.eid += 1

        link_format = link_header.parse_link_value(request.payload)
        domain = params.get('d', '')
        endpoint_type = params.get('et', '')
        lifetime = params.get('lt', DEFAULT_LIFETIME)
        context = params.get('con', 'coap://'+request.remote[0]+":"+str(request.remote[1]))

        entry = DirectoryEntryResource(self, link_format, endpoint, domain, endpoint_type, lifetime, context)
        self.putChild(self.directory[endpoint], entry)
        response = coap.Message(code=coap.CREATED, payload='')
        response.opt.location_path = ('rd', self.directory[endpoint])
        log.msg("RD entry added: endpoint=%s, lifetime=%d" % (endpoint, lifetime))
        return defer.succeed(response)


class DirectoryEntryResource (resource.CoAPResource):
    """
    Simple implementation of Resource Directory (draft-ietf-core-resource-directory-01).
    
    This class implements Update and Removal functions (points 5.3 and 5.4
    of the draft).
    """
    
    def __init__(self, parent, link_format, endpoint, domain, endpoint_type, lifetime, context):
        resource.CoAPResource.__init__(self)
        self.visible = False
        self.parent = parent
        self.endpoint = endpoint
        self.link_format = link_format
        self.domain = domain
        self.endpoint_type = endpoint_type
        self.context = context
        self.timeout = reactor.callLater(float(lifetime), self.removeResource)

    def render_PUT(self, request):
        """
        Update this resource directory entry.
        """
        try:
            params = parseUriQuery(request.opt.uri_query)
        except ValueError:
            log.msg("Bad or ambiguous query options!")
            response = coap.Message(code=coap.BAD_REQUEST, payload="Bad or ambiguous query options!")
            return defer.succeed(response)

        lifetime = params.get('lt', DEFAULT_LIFETIME)
        self.timeout.cancel()
        self.timeout = reactor.callLater(float(lifetime), self.removeResource)
        self.endpoint_type = params.get('et', '')
        self.context = params.get('con', 'coap://'+request.remote[0]+":"+str(request.remote[1]))
        
        response = coap.Message(code=coap.CHANGED, payload='')
        log.msg("RD entry updated: endpoint=%s, lifetime=%d" % (self.endpoint,lifetime))
        return defer.succeed(response)

    def render_DELETE(self, request):
        """
        Delete this resource directory entry.
        """
        log.msg("RD entry deleted: endpoint=%s" % self.endpoint)
        self.removeResource()
        response = coap.Message(code=coap.DELETED, payload='')
        return defer.succeed(response)
    
    def removeResource(self):
        """
        Remove this resource. Used by both expiry and deletion.
        """
        location = self.parent.directory.pop(self.endpoint)
        del(self.parent.children[location])


class EndpointLookupResource (resource.CoAPResource):
    """
    Simple implementation of Resource Directory (draft-ietf-core-resource-directory-01).
    
    This class implements Endpoint Lookup function (point 7 of the draft).
    """

    def __init__(self, directory_resource):
        resource.CoAPResource.__init__(self)
        self.visible = True
        self.directory = directory_resource

    def render_GET(self, request):
        """
        Return list of endpoints matching params specified in URI query.
        """
        try:
            params = parseUriQuery(request.opt.uri_query)
        except ValueError:
            log.msg("Bad or ambiguous query options!")
            response = coap.Message(code=coap.BAD_REQUEST, payload="Bad or ambiguous query options!")
            return defer.succeed(response)
        
        ep_pattern = params.get('ep', '*')
        d_pattern = params.get('d', '*')
        et_pattern = params.get('et', '*')
        
        link_format = []
        first_entry = True
        for entry in self.directory.children.values():
            if fnmatch.fnmatch(entry.endpoint, ep_pattern) and \
                    fnmatch.fnmatch(entry.domain, d_pattern) and \
                    fnmatch.fnmatch(entry.endpoint_type, et_pattern):
                if first_entry is True:
                    first_entry = False
                else:
                    link_format.append(',')
                link_format.append('<')
                link_format.append(entry.context)
                link_format.append('>;ep="')
                link_format.append(entry.endpoint)
                link_format.append('"')

        response = coap.Message(code=coap.CONTENT, payload=''.join(link_format))
        response.opt.content_format = coap.media_types_rev['application/link-format']
        return defer.succeed(response)

class ResourceLookupResource (resource.CoAPResource):
    """
    Simple implementation of Resource Directory (draft-ietf-core-resource-directory-01).
    
    This class implements Resource Lookup function (point 7 of the draft).
    """

    def __init__(self, directory_resource):
        resource.CoAPResource.__init__(self)
        self.visible = True
        self.directory = directory_resource

    def render_GET(self, request):
        """
        Return list of resources matching params specified in URI query.
        """
        try:
            params = parseUriQuery(request.opt.uri_query)
        except ValueError:
            log.msg("Bad or ambiguous query options!")
            response = coap.Message(code=coap.BAD_REQUEST, payload="Bad or ambiguous query options!")
            return defer.succeed(response)
        
        #Endpoint parameters
        ep_pattern = params.get('ep', '*')
        d_pattern = params.get('d', '*')
        et_pattern = params.get('et', '*')
        
        #Resource parameters
        rt_pattern = params.get('rt', '*')
        title_pattern = params.get('title', '*')
        if_pattern = params.get('if', '*')
        
        link_format = []
        first_entry = True
        for entry in self.directory.children.values():
            if fnmatch.fnmatch(entry.endpoint, ep_pattern) and \
                    fnmatch.fnmatch(entry.domain, d_pattern) and \
                    fnmatch.fnmatch(entry.endpoint_type, et_pattern):
                for uri, params in entry.link_format.items():
                    if fnmatch.fnmatch(params.get('rt',''), rt_pattern) and \
                            fnmatch.fnmatch(params.get('title',''), title_pattern) and \
                            fnmatch.fnmatch(params.get('if',''), if_pattern):
                        if first_entry is True:
                            first_entry = False
                        else:
                            link_format.append(',')
                        link_format.append('<')
                        link_format.append(entry.context)
                        link_format.append(uri)
                        link_format.append('>')
                        for name, value in params.items():
                            link_format.append(';')
                            link_format.append(name)
                            link_format.append('="')
                            link_format.append(value)
                            link_format.append('"')

        response = coap.Message(code=coap.CONTENT, payload=''.join(link_format))
        response.opt.content_format = coap.media_types_rev['application/link-format']
        return defer.succeed(response)


log.startLogging(sys.stdout)

#: </>
root = resource.CoAPResource()

#: </rd>
rd = DirectoryResource()
root.putChild('rd', rd)

#: </rd-lookup>
lookup = resource.CoAPResource()
root.putChild('rd-lookup', lookup)

#: </rd-lookup/ep>
ep_lookup = EndpointLookupResource(rd)
lookup.putChild('ep', ep_lookup)

#: </rd-lookup/res>
res_lookup = ResourceLookupResource(rd)
lookup.putChild('res', res_lookup)

endpoint = resource.Endpoint(root)
protocol = coap.Coap(endpoint)

reactor.listenUDP(coap.COAP_PORT, protocol)
reactor.run()
