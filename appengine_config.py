from gaesessions import SessionMiddleware 

def webapp_add_wsgi_middleware(app): 
   app = SessionMiddleware(app, cookie_key='\x82\xa8\x9d\xaf\x81,m\xc4y\xd4C\xfb\x14?a\xec\x85{\x1c\x9a\x8dU\x1e\x86\xf2;\xc3\xc2\xb0x\xf3\xe5\xedX\xc1\xfe\xadM.;\xce\r\xc9\x9a\xae\x13=(H\xe6\xcb\x10\x16Y\x1b\xf5\x05Ua]\x0e5Z\xc3') 
   return app
