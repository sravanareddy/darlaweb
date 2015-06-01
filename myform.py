import web

class MyRadio(web.form.Radio):
	"""get_type not implemented in original"""
	def get_type(self):
		return 'radio'
        def render(self):
                x = '<span>'
                for arg in self.args:
                    if isinstance(arg, (tuple, list)):
                        value, desc, id= arg 
                    else:
                        value, desc, id= arg, arg, arg
                    attrs = self.attrs.copy()
                    attrs['name'] = self.name
                    attrs['type'] = 'radio'
                    attrs['value'] = value
                    attrs['id'] = id #add id
                    if self.value == value:
                        attrs['checked'] = 'checked'
                    x += '<input %s/> %s' % (attrs, desc)
                x += '</span>'
                return x

class MyButton(web.form.Button):
	"""get_type not implemented in original"""
	
	def get_type(self):
		return 'button'
	
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
        def rendernote(self, note, disabled = False):
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
                                out.append(i.description)
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
			if i.name=='submit':  #don't show submit button here
				continue
                        if not i.is_hidden():
				out.append('<p class="dis">')
				out.append(i.description+' ')
			i.attrs['disabled'] = True
                        out.append(i.render())
                        if not i.is_hidden():
				out.append(self.rendernote(i.note))
				out.append('<br><span class="disnote">{0}</span>'.format(i.post))
				out.append('</p>\n')
                return ''.join(out)

class ListToForm(web.form.Form):
        """override so a list of inputs can be sent in"""
        def __init__(self, inputs, **kw): #inputs here is a list
                self.inputs = inputs
                self.valid = True
                self.note = None
                self.validators = kw.pop('validators', [])

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
                                out.append(i.pre)
                                out.append('<p>')
                                if not i.post.startswith('Check if'): #don't show name for speaker checkbox
                                        out.append(i.description+' ')
                        out.append(i.render())
                        if not i.is_hidden():
                                out.append(self.rendernote(i.note))
                                if not i.post.startswith('Check if'):
                                        out.append('<br>')
                                else:
                                        out.append(' ')
                                out.append('<span class="note">{0}</span>'.format(i.post))
                                out.append('</p>\n')

                return ''.join(out) 

        # def render_disabled(self):
        #         out = []
        #         out.append(self.rendernote(self.note))
        #         for i in self.inputs:
        #                 out.append('<p>')
        #                 out.append(i.description+': ')
        #                 out.append(i.render())
        #                 out.append(self.rendernote(i.note))
        #                 out.append('<span class="note">dis{0}</span>'.format(i.post))
        #                 out.append('</p>\n')
        #         return ''.join(out)

