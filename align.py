"""class that calls alignment things """

import web
from web import form
import myform
import utilities

urls = {
	 '/?', 'align'
	 }

class align:
	def GET(self):
		return "TESTING"
	def POST(self):
		return "GOT IT!"

app_align = web.application(urls, locals())