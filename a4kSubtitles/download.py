# -*- coding: utf-8 -*-

def __download(core, filepath, request):
    request['stream'] = True
    with core.request.execute(core, request) as r:
        with open(filepath, 'wb') as f:
            core.shutil.copyfileobj(r.raw, f)

def __extract_gzip(core, archivepath, filename):
    filepath = core.os.path.join(core.utils.temp_dir, filename)

    if core.utils.py2:
        with open(archivepath, 'rb') as f:
            gzip_file = f.read()

        with core.gzip.GzipFile(fileobj=core.utils.StringIO(gzip_file)) as gzip:
            with open(filepath, 'wb') as f:
                f.write(gzip.read())
                f.flush()
    else:
        with core.gzip.open(archivepath, 'rb') as f_in:
            with open(filepath, 'wb') as f_out:
                core.shutil.copyfileobj(f_in, f_out)

    return filepath

def __extract_zip(core, archivepath, filename, episodeid):
    sub_exts = ['.srt', '.sub']
    sub_exts_secondary = ['.smi', '.ssa', '.aqt', '.jss', '.ass', '.rt', '.txt']

    archivepath_ = core.utils.quote_plus(archivepath)
    subfile = core.utils.find_file_in_archive(core, archivepath_, sub_exts, episodeid)
    if not subfile:
        subfile = core.utils.find_file_in_archive(core, archivepath_, sub_exts_secondary, episodeid)

    dest = core.os.path.join(core.utils.temp_dir, filename)
    if not subfile:
        try:
            return __extract_gzip(core, archivepath, filename)
        except:
            core.os.rename(archivepath, dest)
            return dest

    src = 'archive://' + archivepath_ + '/' + subfile
    core.kodi.xbmcvfs.copy(src, dest)
    return dest

def __insert_lang_code_in_filename(core, filename, lang):
    filename_chunks = filename.split('.')
    lang_code = core.kodi.xbmc.convertLanguage(lang, core.kodi.xbmc.ISO_639_2)
    filename_chunks.insert(-1, lang_code)
    return '.'.join(filename_chunks)

def __postprocess(core, filepath):
    try:
        with open(filepath, 'rb') as f:
            text_bytes = f.read()

        text = text_bytes.decode(core.utils.default_encoding)

        try:
            if all(ch in text for ch in core.utils.cp1251_garbled):
                text = text.encode(core.utils.base_encoding).decode('cp1251')
            elif all(ch in text for ch in core.utils.koi8r_garbled):
                try:
                    text = text.encode(core.utils.base_encoding).decode('koi8-r')
                except:
                    text = text.encode(core.utils.base_encoding).decode('koi8-u')
        except: pass

        try:
            clean_text = core.utils.cleanup_subtitles(core, text)
            if len(clean_text) > len(text) / 2:
                text = clean_text
        except: pass

        with open(filepath, 'wb') as f:
            f.write(text.encode(core.utils.default_encoding))
    except: pass

def download(core, params):
    core.logger.debug(lambda: core.json.dumps(params, indent=2))

    core.shutil.rmtree(core.utils.temp_dir, ignore_errors=True)
    core.kodi.xbmcvfs.mkdirs(core.utils.temp_dir)

    actions_args = params['action_args']
    filename = __insert_lang_code_in_filename(core, actions_args['filename'], actions_args['lang'])
    archivepath = core.os.path.join(core.utils.temp_dir, 'sub.zip')

    service_name = params['service_name']
    service = core.services[service_name]
    request = service.build_download_request(core, service_name, actions_args)

    if actions_args.get('raw', False):
        filepath = core.os.path.join(core.utils.temp_dir, filename)
        __download(core, filepath, request)
    else:
        __download(core, archivepath, request)
        if actions_args.get('gzip', False):
            filepath = __extract_gzip(core, archivepath, filename)
        else:
            episodeid = actions_args.get('episodeid', '')
            filepath = __extract_zip(core, archivepath, filename, episodeid)

    __postprocess(core, filepath)

    if core.api_mode_enabled:
        return filepath

    listitem = core.kodi.xbmcgui.ListItem(label=filepath)
    core.kodi.xbmcplugin.addDirectoryItem(handle=core.handle, url=filepath, listitem=listitem, isFolder=False)
