# -*- coding: utf-8 -*-

import sys
import os
import json
import re
import pytest
import time

dir_name = os.path.dirname(__file__)
main = os.path.join(dir_name, '..')
a4kSubtitles = os.path.join(main, '..', 'a4kSubtitles')
lib = os.path.join(a4kSubtitles, 'lib')
services = os.path.join(a4kSubtitles, 'services')

sys.path.append(dir_name)
sys.path.append(main)
sys.path.append(a4kSubtitles)
sys.path.append(lib)
sys.path.append(services)

from a4kSubtitles import api
from tests import utils

__movie_video_meta = {
    'year': '2016',
    'title': 'Fantastic Beasts and Where to Find Them',
    'imdb_id': 'tt3183660',
    'filename': 'Fantastic.Beasts.and.Where.to.Find.Them.2016.1080p.BluRay.x264.DTS-JYK.mkv',
    'filesize': '3592482379',
    'filehash': '4985126cbf92fe60',
    'subdb_hash': 'fb7e5d6ac9c3f94813467988de753d0e',
}

__tvshow_video_meta = {
    "year": "2018",
    "title": "The Passenger",
    "tvshow": "Westworld",
    "imdb_id": "tt6243312",
    "season": "2",
    "episode": "10",
    "filename": "Westworld.S02E10.1080p.WEB.H264-DEFLATE.mkv",
    "filesize": "7945997565",
    "filehash": "d603a5b0e73d4b6b",
    "subdb_hash": "2aec1b70afe702e67ab39a0af776ba5a",
}

def __remove_last_results(a4ksubtitles_api):
    try:
        os.remove(a4ksubtitles_api.core.utils.results_filepath)
    except: pass

def __search(a4ksubtitles_api, settings={}, video_meta={}):
    search = lambda: None
    search.params = {
        'languages': 'English',
        'preferredlanguage': '',
    }

    search.settings = {
        'general.timeout': '15',
        'general.results_limit': '20',
        'general.remove_ads': 'true',
        'opensubtitles.enabled': 'false',
        'opensubtitles.username': '',
        'opensubtitles.password': '',
        'bsplayer.enabled': 'false',
        'podnadpisi.enabled': 'false',
        'subdb.enabled': 'false',
    }
    search.settings.update(settings)

    search.video_meta = {}
    search.video_meta.update(video_meta)

    search.results = a4ksubtitles_api.search(search.params, search.settings, search.video_meta)

    return search

def __search_movie(a4ksubtitles_api, settings={}, video_meta={}):
    movie_video_meta = __movie_video_meta.copy()
    movie_video_meta.update(video_meta)
    return __search(a4ksubtitles_api, settings, movie_video_meta)

def __search_tvshow(a4ksubtitles_api, settings={}, video_meta={}):
    tvshow_video_meta = __tvshow_video_meta.copy()
    tvshow_video_meta.update(video_meta)
    return __search(a4ksubtitles_api, settings, tvshow_video_meta)

def test_api():
    def get_error_msg(e):
        return str(e.value).replace('\'', '')

    with pytest.raises(ImportError) as e:
        api.A4kSubtitlesApi()
    assert get_error_msg(e) == "No module named xbmc"

    with pytest.raises(ImportError) as e:
        api.A4kSubtitlesApi({'xbmc': True})
    assert get_error_msg(e) == "No module named xbmcaddon"

    with pytest.raises(ImportError) as e:
        api.A4kSubtitlesApi({'xbmc': True, 'xbmcaddon': True})
    assert get_error_msg(e) == "No module named xbmcplugin"

    with pytest.raises(ImportError) as e:
        api.A4kSubtitlesApi({'xbmc': True, 'xbmcaddon': True, 'xbmcplugin': True})
    assert get_error_msg(e) == "No module named xbmcgui"

    with pytest.raises(ImportError) as e:
        api.A4kSubtitlesApi({'xbmc': True, 'xbmcaddon': True, 'xbmcplugin': True, 'xbmcgui': True})
    assert get_error_msg(e) == "No module named xbmcvfs"

    api.A4kSubtitlesApi({'xbmc': True, 'xbmcaddon': True, 'xbmcplugin': True, 'xbmcgui': True, 'xbmcvfs': True})
    api.A4kSubtitlesApi({'kodi': True})

def test_search_missing_imdb_id():
    a4ksubtitles_api = api.A4kSubtitlesApi({'kodi': True})
    log_error_spy = utils.spy_fn(a4ksubtitles_api.core.logger, 'error')

    params = {
        'languages': 'English',
        'preferredlanguage': '',
    }
    a4ksubtitles_api.search(params)

    log_error_spy.called_with('missing imdb id!')

def test_opensubtitles():
    a4ksubtitles_api = api.A4kSubtitlesApi({'kodi': True})
    __remove_last_results(a4ksubtitles_api)

    # search
    settings = {
        'opensubtitles.enabled': 'true',
        'opensubtitles.username': os.getenv('A4KSUBTITLES_OPENSUBTITLES_USERNAME', ''),
        'opensubtitles.password': os.getenv('A4KSUBTITLES_OPENSUBTITLES_PASSWORD', '')
    }
    search = __search_movie(a4ksubtitles_api, settings)

    assert len(search.results) == 20

    expected_result_name = 'Fantastic.Beasts.and.Where.to.Find.Them.2016.1080p.BluRay.x264.DTS-JYK.srt'
    expected_result_name2 = 'Fantastic.Beasts.and.Where.to.Find.Them.2016.1080p.BluRay.x264.DTS-FGT.srt'
    assert search.results[0]['name'] == expected_result_name or search.results[0]['name'] == expected_result_name2

    __remove_last_results(a4ksubtitles_api)

    # search (imdb only)
    video_meta = {
        'filesize': '',
        'filehash': '',
    }
    search = __search_movie(a4ksubtitles_api, settings, video_meta)

    assert len(search.results) == 20

    # download
    item = search.results[0]

    params = {
        'action': 'download',
        'service_name': 'opensubtitles',
        'action_args': item['action_args']
    }

    search.settings['general.remove_ads'] = 'false'
    filepath = a4ksubtitles_api.download(params, search.settings)

    assert filepath != ''

    # remove_ads
    with open(filepath, 'r') as f:
        sub_contents = f.read()

    assert re.match(r'.*OpenSubtitles.*', sub_contents, re.DOTALL) is not None

    search.settings['general.remove_ads'] = 'true'
    filepath = a4ksubtitles_api.download(params, search.settings)

    assert filepath != ''

    with open(filepath, 'r') as f:
        sub_contents = f.read()

    assert re.match(r'.*OpenSubtitles.*', sub_contents, re.DOTALL) is None

def test_opensubtitles_tvshow():
    a4ksubtitles_api = api.A4kSubtitlesApi({'kodi': True})
    __remove_last_results(a4ksubtitles_api)

    # search
    settings = {
        'opensubtitles.enabled': 'true',
    }
    search = __search_tvshow(a4ksubtitles_api, settings)

    # download
    item = search.results[0]

    params = {
        'action': 'download',
        'service_name': 'opensubtitles',
        'action_args': item['action_args']
    }

    filepath = a4ksubtitles_api.download(params, search.settings)

    assert filepath != ''

def test_bsplayer():
    a4ksubtitles_api = api.A4kSubtitlesApi({'kodi': True})
    __remove_last_results(a4ksubtitles_api)

    # search
    settings = {
        'bsplayer.enabled': 'true',
    }
    search = __search_movie(a4ksubtitles_api, settings)

    assert len(search.results) == 16

    expected_result_name = os.path.splitext(search.video_meta['filename'])[0]
    result_name = os.path.splitext(search.results[0]['name'])[0]
    assert expected_result_name == result_name

    # cache
    request_execute_spy = utils.spy_fn(a4ksubtitles_api.core.request, 'execute')
    __search_movie(a4ksubtitles_api, settings)

    assert request_execute_spy.call_count == 0

    request_execute_spy.restore()

    # download
    item = search.results[0]

    params = {
        'action': 'download',
        'service_name': 'bsplayer',
        'action_args': item['action_args']
    }

    filepath = a4ksubtitles_api.download(params, search.settings)

    assert filepath != ''

def test_bsplayer_tvshow():
    a4ksubtitles_api = api.A4kSubtitlesApi({'kodi': True})
    __remove_last_results(a4ksubtitles_api)

    # search
    settings = {
        'bsplayer.enabled': 'true',
    }
    search = __search_tvshow(a4ksubtitles_api, settings)

    # download
    item = search.results[0]

    params = {
        'action': 'download',
        'service_name': 'bsplayer',
        'action_args': item['action_args']
    }

    filepath = a4ksubtitles_api.download(params, search.settings)

    assert filepath != ''

def test_podnadpisi():
    a4ksubtitles_api = api.A4kSubtitlesApi({'kodi': True})
    __remove_last_results(a4ksubtitles_api)

    # search
    settings = {
        'podnadpisi.enabled': 'true',
    }
    search = __search_movie(a4ksubtitles_api, settings)

    # download
    item = search.results[0]

    params = {
        'action': 'download',
        'service_name': 'podnadpisi',
        'action_args': item['action_args']
    }

    filepath = a4ksubtitles_api.download(params, search.settings)

    assert filepath != ''

def test_podnadpisi_tvshow():
    a4ksubtitles_api = api.A4kSubtitlesApi({'kodi': True})
    __remove_last_results(a4ksubtitles_api)

    # search
    settings = {
        'podnadpisi.enabled': 'true',
    }
    search = __search_tvshow(a4ksubtitles_api, settings)

    # download
    item = search.results[0]

    params = {
        'action': 'download',
        'service_name': 'podnadpisi',
        'action_args': item['action_args']
    }

    filepath = a4ksubtitles_api.download(params, search.settings)

    assert filepath != ''

def test_subdb():
    a4ksubtitles_api = api.A4kSubtitlesApi({'kodi': True})
    __remove_last_results(a4ksubtitles_api)

    # search
    settings = {
        'subdb.enabled': 'true',
    }
    search = __search_movie(a4ksubtitles_api, settings)

    # download
    item = search.results[0]

    params = {
        'action': 'download',
        'service_name': 'subdb',
        'action_args': item['action_args']
    }

    filepath = a4ksubtitles_api.download(params, search.settings)

    assert filepath != ''

def test_subdb_tvshow():
    a4ksubtitles_api = api.A4kSubtitlesApi({'kodi': True})
    __remove_last_results(a4ksubtitles_api)

    # search
    settings = {
        'subdb.enabled': 'true',
    }

    search = __search_tvshow(a4ksubtitles_api, settings)

    # download
    item = search.results[0]

    params = {
        'action': 'download',
        'service_name': 'subdb',
        'action_args': item['action_args']
    }

    filepath = a4ksubtitles_api.download(params, search.settings)

    assert filepath != ''

def test_subscene():
    a4ksubtitles_api = api.A4kSubtitlesApi({'kodi': True})
    __remove_last_results(a4ksubtitles_api)

    # search
    settings = {
        'subscene.enabled': 'true',
    }
    search = __search_movie(a4ksubtitles_api, settings)

    # download
    item = search.results[0]

    params = {
        'action': 'download',
        'service_name': 'subscene',
        'action_args': item['action_args']
    }

    if os.getenv('CI', None) is not None:
        time.sleep(2)

    filepath = a4ksubtitles_api.download(params, search.settings)

    assert filepath != ''

def test_subscene_tvshow():
    a4ksubtitles_api = api.A4kSubtitlesApi({'kodi': True})
    __remove_last_results(a4ksubtitles_api)

    # search
    settings = {
        'subscene.enabled': 'true',
    }

    if os.getenv('CI', None) is not None:
        time.sleep(2)

    search = __search_tvshow(a4ksubtitles_api, settings)

    # download
    item = search.results[0]

    params = {
        'action': 'download',
        'service_name': 'subscene',
        'action_args': item['action_args']
    }

    if os.getenv('CI', None) is not None:
        time.sleep(2)

    filepath = a4ksubtitles_api.download(params, search.settings)

    assert filepath != ''

def test_addic7ed_tvshow():
    a4ksubtitles_api = api.A4kSubtitlesApi({'kodi': True})
    __remove_last_results(a4ksubtitles_api)

    # search
    settings = {
        'addic7ed.enabled': 'true',
    }
    search = __search_tvshow(a4ksubtitles_api, settings)

    # download
    item = search.results[0]

    params = {
        'action': 'download',
        'service_name': 'addic7ed',
        'action_args': item['action_args']
    }

    filepath = a4ksubtitles_api.download(params, search.settings)

    assert filepath != ''
