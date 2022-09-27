import string
try:
    import inflect
    from kitchen.text.converters import to_unicode
except:
    pass # for python3 version

transfrom = '\xd5\xd3\xd2\xd0\xd1\xcd\xd4'
transto = '\'""--\'\''
try:
    unimaketrans = string.maketrans(transfrom, transto)
except:
    unimaketrans = str.maketrans(transfrom, transto) # for python3 version

replacement_mappings = {"\xe2\x80\x93": " - ",
                        '\xe2\x80\x94': " - ",
                        '\xe2\x80\x99': "'",
                        '\xe2\x80\x9c': '"',
                        '\xe2\x80\x9d': '"',
                        '\xe2\x80\xa6': '...',
                        '\r\n': '\n',
                        '\r': '\n'}

def norm_dollar_signs(word):
    """convert $n to n dollars"""
    if word.startswith('$'):
        suffix = 'dollars'
        if len(word)>1:
            if word[1:] == '1':
                suffix = 'dollar'
            return word[1:]+' '+suffix
        else:
            return suffix
    return word

def process_usertext(inputstring):
    """cleans up unicode, translate numbers, outputs as a list of unicode words."""

    if(isinstance(inputstring, str)):
    #MS line breaks and stylized characters that TextEdit inserts. (is there an existing module that does this?)

        inputstring = string.translate(inputstring.strip(),
                                       unimaketrans)
        for ustr in replacement_mappings:
            inputstring = inputstring.replace(ustr, replacement_mappings[ustr])

        inputstring = to_unicode(inputstring, encoding='utf-8', errors='ignore')   # catch-all?

    cleaned = inputstring.replace('[', '').replace(']', '')  # common in linguists' transcriptions
    cleaned = cleaned.replace('-', ' ').replace('/', ' ')
    # convert digits and normalize $n
    digitconverter = inflect.engine()
    returnstr = ''
    for line in cleaned.splitlines():
        wordlist = map(lambda word: word.strip(string.punctuation), line.split())
        wordlist = ' '.join(map(norm_dollar_signs,
                       wordlist)).split()
        returnstr += ' '.join(map(lambda word:
                        digitconverter.number_to_words(word).replace('-', ' ').replace(',', '') if word[0].isdigit() or (word[0]=="'" and len(word)>1 and word[1].isdigit()) else word,
                        wordlist))+'\n'
    return returnstr
