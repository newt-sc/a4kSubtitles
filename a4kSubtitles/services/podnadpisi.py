# -*- coding: utf-8 -*-

__url = 'https://www.podnapisi.net'

def build_search_requests(core, service_name, meta):
    params = {
        'keywords': meta.title if meta.is_movie else meta.tvshow,
        'language': core.utils.get_lang_ids(meta.languages, core.kodi.xbmc.ISO_639_1),
        'year': meta.year
    }

    if meta.is_tvshow:
        params['seasons'] = meta.season
        params['episodes'] = meta.episode
        params['movie_type'] = ['tv-series', 'mini-series']
    else:
        params['movie_type'] = 'movie'

    request = {
        'method': 'GET',
        'url': '%s/subtitles/search/advanced' % __url,
        'headers': {
            'Accept': 'application/json'
        },
        'params': params
    }

    return [request]

def parse_search_response(core, service_name, meta, response):
    try:
        results = core.json.loads(response)
    except Exception as exc:
        core.logger.error('%s - %s' % (service_name, exc))
        return []

    lang_ids = core.utils.get_lang_ids(meta.languages, core.kodi.xbmc.ISO_639_1)

    def map_result(result):
        name = ''
        last_similarity = -1

        for release_name in result['custom_releases']:
            similarity = core.difflib.SequenceMatcher(None, release_name, meta.filename_without_ext).ratio()
            if similarity > last_similarity:
                last_similarity = similarity
                name = release_name

        name = '%s.srt' % name
        lang_code = result['language']
        lang = meta.languages[lang_ids.index(lang_code)]

        return {
            'service_name': service_name,
            'service': 'Podnadpisi',
            'lang': lang,
            'name': name,
            'rating': 0,
            'lang_code': lang_code,
            'sync': 'true' if meta.filename_without_ext in result['custom_releases'] else 'false',
            'impaired': 'true' if 'hearing_impaired' in result['flags'] else 'false',
            'action_args': {
                'url': '%s%s' % (__url, result['download']),
                'lang': lang,
                'filename': name
            }
        }

    return list(map(map_result, results['data']))

def build_download_request(core, service_name, args):
    request = {
        'method': 'GET',
        'url': args['url']
    }

    return request
