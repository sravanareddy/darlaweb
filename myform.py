import web

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
                        out.append('<p>')
                        out.append(i.description+': ')
                        out.append(i.render()) 
                        out.append(self.rendernote(i.note))
                        out.append('<br><span class="note">{0}</span>'.format(i.post))
                        out.append('</p>\n')
                return ''.join(out) 

