import time
import json
from ngxgroup_com import *

if __name__ == '__main__':
    start_time = time.time()

    a = Handler()
    # final_data = a.Execute('eyckaWQnOiAnMycsICdJbnRlcm5hdGlvblNlY0lOJzogJ05HQUNDRVNTMDAwNScsICdTeW1ib2wnOiAnQUNDRVNTJywgJ1ByZXZDbG9zZSc6IDEwLjUsICdPcGVuUHJpY2UnOiAxMC41LCAnRGF5c0hpZ2gnOiAxMC42LCAnRGF5c0xvdyc6IDEwLjQsICdWb2x1bWUnOiAzMDgxMzI3MS4wLCAnVmFsdWUnOiAzMjI0MzY0MjIuOSwgJ01hcmtldENhcCc6IDM3MzIyNDg2OTAzMS4wLCAnU2hhcmVzT3V0c3RhbmRpbmcnOiAzNTU0NTIyNTYyMi4wLCAnRGl2aWRlbmQnOiBOb25lLCAnWWllbGQnOiBOb25lLCAnU2VjdG9yJzogJ0ZJTkFOQ0lBTCBTRVJWSUNFUycsICdTdWJTZWN0b3InOiAnQmFua2luZycsICdDb21wYW55TmFtZSc6ICdBQ0NFU1MgQkFOSyBQTEMuJywgJ01hcmtldENsYXNzaWZpY2F0aW9uJzogJ1ByZW1pdW0gQm9hcmQnLCAnRGF0ZUxpc3RlZCc6IE5vbmUsICdEYXRlT2ZJbmNvcnBvcmF0aW9uJzogJzE5ODktMDItMDhUMDA6MDA6MDAnLCAnV2Vic2l0ZSc6ICd3d3cuYWNjZXNzYmFua3BsYy5jb20nLCAnTG9nb3VybCc6ICd3d3cuYWNjZXNzYmFua3BsYy5jb20nLCAnU3RvY2tQcmljZVBlcmNDaGFuZ2UnOiAtMC40OCwgJ1N0b2NrUHJpY2VDaGFuZ2UnOiAwLjAsICdTdG9ja1ByaWNlQ3VyJzogMTAuNSwgJ0NvbXBhbnlQcm9maWxlU3VtbWFyeSc6IE5vbmUsICdOYXR1cmVvZkJ1c2luZXNzJzogJ0NvbW1lcmNpYWwgQmFua2luZycsICdDb21wYW55QWRkcmVzcyc6ICdBY2Nlc3MgVG93ZXIgUGxvdCAxNC8xNSwgUHJpbmNlIEFsYWJhIE9uaXJ1IFN0cmVldCwgT25pcnUgRXN0YXRlLCBWaWN0b3JpYSBJc2xhbmQsIExhZ29zJywgJ1RlbGVwaG9uZSc6ICcyMzQxMjgwNTYyOCcsICdGYXgnOiAnQUNDRVNTIEJBTksgUExDIDAyOTIwMDMyOEMzTjlZSTJENjYwJywgJ0VtYWlsJzogJ2luZm9AYWNjZXNzYmFua3BsYy5jb20nLCAnQ29tcGFueVNlY3JldGFyeSc6ICdNci4gU3VuZGF5IEVrd29jaGknLCAnQXVkaXRvcic6ICdQcmljZXdhdGVyaG91c2VDb29wZXJzJywgJ1JlZ2lzdHJhcnMnOiBOb25lLCAnQm9hcmRPZkRpcmVjdG9ycyc6ICdBam9yaXRzZWRlcmUgIEF3b3Npa2EsIERyLiBHcmVnb3J5IEpvYm9tZSAsIERyLiBPa2V5IE53dWtlICwgSGFzc2FuICBVc21hbiwgTXIgUGF1bCBVc29ybzsgU0FOICwgTXIuIEFkZSBCYWpvbW8gLCBNci4gQWRlbml5aSBBZGVrb3lhICAsIE1yLiBIZXJiZXJ0IFdpZ3dlICwgTXIuIElib3JvbWEgQWtwYW5hICAsIE1yLiBSb29zZXZlbHQgT2dib25uYSAsIE1yLiBWaWN0b3IgRXR1b2t3dSAsIE1ycy4gQW50aG9uaWEgS2VtaSBPZ3VubWVmdW4gLCBNcnMuIENoaXpvbWEgT2tvbGkgLCBNcnMuIElmZXlpbndhIE9zaW1lICAsIE1zLiBIYWRpemEgQW1idXJzYSAsIE9sdXNleWkgIEt1bWFwYXlpLCBPbW9zYWxld2EgRmFqb2JpJywgJ0lEJzogNSwgJ0hJR0g1MldLX1BSSUNFJzogMTAuNiwgJ0hJR0g1MldLX0RBVEVUSU1FJzogJzIwMjItMDItMTFUMDA6MDA6MDAnLCAnTE9XNTJXS19QUklDRSc6IDcuMDUsICdMT1c1MldLX0RBVEVUSU1FJzogJzIwMjEtMDQtMjdUMDA6MDA6MDAnLCAnU3ltYm9sMic6ICdBQ0NFU1MgIFtDRytdJywgJ0xTX1NURCc6ICcsW0NHK10nLCAnT0ZGSUNJQUxfT1BFTic6IE5vbmUsICdPRkZJQ0lBTF9DTE9TRSc6IDEwLjUsICdMYXN0VXBsb2FkSW5mbyc6IE5vbmUsICdRdWF0ZXJJRCc6IE5vbmUsICdRdWF0ZXJZZWFyJzogTm9uZSwgJ1RvdGFsQXNzZXRzVW5kZXJNYW5hZ2VtZW50JzogTm9uZSwgJ2ltZ1BhdGgnOiBOb25lLCAnQWRkcmVzcyc6IE5vbmUsICdDYWJsZSc6IE5vbmUsICdQQWRkcmVzcyc6IE5vbmUsICdUZWxleCc6IE5vbmV9',
    #                        'Financial_Information', '', '')
    final_data = a.Execute('ACCESS BANK PLC','','','')
    print(json.dumps(final_data, indent=4))

    elapsed_time = time.time() - start_time
    print('\nTask completed - Elapsed time: ' + str(round(elapsed_time, 2)) + ' seconds')
