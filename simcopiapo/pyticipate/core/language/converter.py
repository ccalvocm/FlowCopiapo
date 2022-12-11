def _replace(tag_start, tag_end, lookup, content, throw_on_no_lookup=False):
    new_content_arr = []
    beg = 0
    while True:
        s_ind = content.find(tag_start, beg)
        if s_ind < 0:
            new_content_arr.append(content[beg:])
            break
        e_ind = content.find(tag_end, s_ind)
        new_content_arr.append(content[beg:s_ind])
        tag = content[s_ind:e_ind+len(tag_end)]
        tag_content = tag[len(tag_start):-len(tag_end)]
        if tag_content in lookup:
            tag_substitute = lookup[tag_content]
            new_content_arr.append(tag_substitute)
        else:
            if throw_on_no_lookup:
                raise RuntimeError('Tag {} has no substitute!'.format(tag))
            new_content_arr.append(tag)
        beg = e_ind + len(tag_end)
    return ''.join(new_content_arr)

def _replace_file(infile, outfile, tag_start, tag_end, lookup, throw_on_no_lookup=False):
    fi = open(infile,'r')
    fo = open(outfile,'w')
    try:
        content = fi.read()
        new_content = _replace(tag_start, tag_end, lookup, content, throw_on_no_lookup)
        fo.write(new_content)
        fo.flush()
    except Exception as e:
        print(e)
    finally:
        fo.close()
        fi.close()

def convert_file(infile, outfile, converter_json_file, language_code='en-au'):

    def load_language_lookup(json_file, code):
        fi = open(json_file, 'r')
        import json
        obj = json.loads(fi.read())
        fi.close()
        lookup = {}
        for o in obj:
            lookup[o['TAG']] = o[code]
        return lookup

    lookup = load_language_lookup(converter_json_file, language_code)

    _replace_file(infile, outfile, '$-', '-$', lookup, True)