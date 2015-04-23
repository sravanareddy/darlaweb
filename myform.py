import web

class MyFile(web.form.File):
	"""Rendering for files should not try to display contents"""
	def render(self):
		attrs = self.attrs.copy()
		attrs['type'] = self.get_type()
		if attrs['type']=='file':
			attrs['value'] = ''
		else:
			attrs['value'] = self.value
		attrs['name'] = self.name
		return '<input %s/>' % attrs
		
class MyForm(web.form.Form):
        """Modify default rendering behavior"""
        def rendernote(self, note):
                if note: 
                        return '<span class="error"> {0}</span>'.format(note)
                else: 
                        return ''

        def render(self):
                out = [] 
                out.append(self.rendernote(self.note))
                for i in self.inputs:
                        if not i.is_hidden():
				out.append('<p>')
				out.append(i.description+': ')
                        out.append(i.render())
                        if not i.is_hidden():
				out.append(self.rendernote(i.note))
				out.append('<br><span class="note">{0}</span>'.format(i.post))
				out.append('</p>\n')
                return ''.join(out) 

        def render_disabled(self):
                out = []
                out.append(self.rendernote(self.note))
                for i in self.inputs:
                        out.append('<p>')
                        out.append(i.description+': ')
                        out.append(i.render())
                        out.append(self.rendernote(i.note))
                        out.append('<br><span class="note">dis{0}</span>'.format(i.post))
                        out.append('</p>\n')
                return ''.join(out)
