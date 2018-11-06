#!/usr/bin/python

from urlparse import urlparse, parse_qs
import SimpleHTTPServer
import SocketServer
import mimetypes
import Quartz
import shutil
import json
import sys
import cgi
import os

# NSEvent.h
NSSystemDefined = 14
# hidsystem/ev_keymap.h
NX_KEYTYPE_NEXT = 17
NX_KEYTYPE_PLAY = 16
NX_KEYTYPE_FAST = 19
NX_KEYTYPE_REWIND = 20
NX_KEYTYPE_SOUND_UP = 0
NX_KEYTYPE_PREVIOUS = 18
NX_KEYTYPE_SOUND_DOWN = 1

supportedcmds = {
  'playpause': NX_KEYTYPE_PLAY,
  'next': NX_KEYTYPE_NEXT,
  'prev': NX_KEYTYPE_PREVIOUS,
  'volup': NX_KEYTYPE_SOUND_UP,
  'voldown': NX_KEYTYPE_SOUND_DOWN
}

def HIDPostAuxKey(key):
  def doKey(down):
    ev = Quartz.NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
      NSSystemDefined, # type
      (0,0), # location
      0xa00 if down else 0xb00, # flags
      0, # timestamp
      0, # window
      0, # ctx
      8, # subtype
      (key << 16) | ((0xa if down else 0xb) << 8), # data1
      -1 # data2
    )
    cev = ev.CGEvent()
    Quartz.CGEventPost(0, cev)
  doKey(True)
  doKey(False)

class HTTPServer(SimpleHTTPServer.SimpleHTTPRequestHandler):
  def _set_headers(self, mime = 'text/html'):
    self.send_response(200)
    self.send_header('Content-type', mime)
    self.end_headers()
  
  def do_GET(self):
    query = parse_qs(urlparse(self.path).query)
    if 'cmd' in query:
      self._set_headers('application/json')
      print 'Call cmd ', query['cmd'][0]
      try:
        ret = {
          'key': lambda x: HIDPostAuxKey(supportedcmds[x])
        }[query['cmd'][0]](query['val'][0])
        self.wfile.write(json.dumps(ret))
      except:
        pass
    else:
      file = self.path[1:]
      if file == '':
        file = 'index.html'
      try:
        with open(os.path.join(os.path.dirname(__file__), file), 'rb') as f:
          mime = mimetypes.guess_type(file)[0]
          self.send_response(200)
          self.send_header("Content-Type", mime)
          fs = os.fstat(f.fileno())
          self.send_header("Content-Length", str(fs.st_size))
          self.end_headers()
          shutil.copyfileobj(f, self.wfile)
      except:
        pass

def StartServer(port):
  Handler = HTTPServer
  httpd = SocketServer.TCPServer(("0.0.0.0", port), Handler)
  httpd.allow_reuse_address = True
  try:
    httpd.serve_forever()
  except KeyboardInterrupt:
    httpd.shutdown()
    httpd.server_close()

if __name__ == '__main__':
    StartServer(8000)
