import web

class MyForm(web.form.Form):
        """Modify default rendering behavior"""
        def render(self):
                out = [] 
                for i in self.inputs:
                        out.append('<p>')
                        out.append(i.description+': ')
                        out.append(i.render()) 
                        out.append('<br><span class="note">{0}</span>'.format(i.post))
                        out.append('</p>\n')
                return ''.join(out) 
