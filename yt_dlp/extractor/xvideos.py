import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote
from ..utils import (
    clean_html,
    determine_ext,
    ExtractorError,
    int_or_none,
    parse_duration,
)


class XVideosIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:[^/]+\.)?xvideos2?\.com/video.*?|
                            (?:www\.)?xvideos\.es/video.*?|
                            (?:www|flashservice)\.xvideos\.com/embedframe/|
                            static-hw\.xvideos\.com/swf/xv-player\.swf\?.*?\bid_video=
                        )
                        (?P<id>[0-9a-zA-Z]+)
                    '''
    _TESTS = [{
        'url': 'https://www.xvideos.com/video4588838/motorcycle_guy_cucks_influencer_steals_his_gf',
        'md5': '14cea69fcb84db54293b1e971466c2e1',
        'info_dict': {
            'id': '4588838',
            'ext': 'mp4',
            'title': 'Motorcycle Guy Cucks Influencer, Steals his GF',
            'duration': 108,
            'age_limit': 18,
            'thumbnail': r're:^https://img-hw.xvideos-cdn.com/.+\.jpg',
        }
    }, {
        # Broken HLS formats
        'url': 'https://www.xvideos.com/video65982001/what_s_her_name',
        'md5': 'b82d7d7ef7d65a84b1fa6965f81f95a5',
        'info_dict': {
            'id': '65982001',
            'ext': 'mp4',
            'title': 'what\'s her name?',
            'duration': 120,
            'age_limit': 18,
            'thumbnail': r're:^https://img-hw.xvideos-cdn.com/.+\.jpg',
        }
    }, {
        'url': 'https://flashservice.xvideos.com/embedframe/4588838',
        'only_matching': True,
    }, {
        'url': 'https://www.xvideos.com/embedframe/4588838',
        'only_matching': True,
    }, {
        'url': 'http://static-hw.xvideos.com/swf/xv-player.swf?id_video=4588838',
        'only_matching': True,
    }, {
        'url': 'http://xvideos.com/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'https://xvideos.com/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'https://xvideos.es/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'https://www.xvideos.es/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'http://xvideos.es/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'http://www.xvideos.es/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'http://fr.xvideos.com/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'https://fr.xvideos.com/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'http://it.xvideos.com/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'https://it.xvideos.com/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'http://de.xvideos.com/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'https://de.xvideos.com/video4588838/biker_takes_his_girl',
        'only_matching': True
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        mobj = re.search(r'<h1 class="inlineError">(.+?)</h1>', webpage)
        if mobj:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, clean_html(mobj.group(1))), expected=True)

        title = self._html_search_regex(
            (r'<title>(?P<title>.+?)\s+-\s+XVID',
             r'setVideoTitle\s*\(\s*(["\'])(?P<title>(?:(?!\1).)+)\1'),
            webpage, 'title', default=None,
            group='title') or self._og_search_title(webpage)

        tags = [
            clean_html(tag[0].replace('-', ' ').title())
            for tag in re.findall(r'<a[^>]+href="[^"]*tags\/([^"]+)"[^>]*>(.+?)</a>', webpage)]

        thumbnails = []
        for preference, thumbnail in enumerate(('', '169')):
            thumbnail_url = self._search_regex(
                r'setThumbUrl%s\(\s*(["\'])(?P<thumbnail>(?:(?!\1).)+)\1' % thumbnail,
                webpage, 'thumbnail', default=None, group='thumbnail')
            if thumbnail_url:
                thumbnails.append({
                    'url': thumbnail_url,
                    'preference': preference,
                })

        duration = int_or_none(self._og_search_property(
            'duration', webpage, default=None)) or parse_duration(
            self._search_regex(
                r'<span[^>]+class=["\']duration["\'][^>]*>.*?(\d[^<]+)',
                webpage, 'duration', fatal=False))

        formats = []

        video_url = compat_urllib_parse_unquote(self._search_regex(
            r'flv_url=(.+?)&', webpage, 'video URL', default=''))
        if video_url:
            formats.append({
                'url': video_url,
                'format_id': 'flv',
            })

        manifest_url = None
        for kind, _, format_url in re.findall(
                r'setVideo([^(]+)\((["\'])(http.+?)\2\)', webpage):
            format_id = kind.lower()
            if format_id == 'hls':
                formats.append({
                    'url': format_url,
                    'format_id': '%s-%s' % ('hls', 'high'),
                    'quality': 'high',
                    'manifest_url': format_url,
                })
                manifest_url = format_url
                # hls_formats = self._extract_m3u8_formats(
                #     format_url, video_id, 'mp4',
                #     entry_protocol='m3u8_native', m3u8_id='hls', fatal=False)
                #
                # hls_formats_count = len(hls_formats)
                # attempts = 0
                # while True:
                #     self._check_formats(hls_formats, video_id)
                #     if len(hls_formats) == hls_formats_count or attempts > 10:
                #         break
                #     attempts += 1
                #     self.to_screen(
                #         '%s: URL is invalid, try to check again (attempt %d)'
                #         % (video_id, attempts))
                # formats.extend(hls_formats)
                #
                # formats.extend(hls_formats)
            elif format_id in ('urllow', 'urlhigh'):
                formats.append({
                    'url': format_url,
                    'format_id': '%s-%s' % (determine_ext(format_url, 'mp4'), format_id[3:]),
                    'quality': -2 if format_id.endswith('low') else None,
                })

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'duration': duration,
            'thumbnails': thumbnails,
            'age_limit': 18,
            'tags': tags,
            'categories': tags,
            'manifest_url': manifest_url
        }


class XVideosQuickiesIE(InfoExtractor):
    IE_NAME = 'xvideos:quickies'
    _VALID_URL = r'https?://(?P<domain>(?:[^/]+\.)?xvideos2?\.com)/amateur-channels/[^#]+#quickies/a/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.xvideos.com/amateur-channels/wifeluna#quickies/a/47258683',
        'md5': '16e322a93282667f1963915568f782c1',
        'info_dict': {
            'id': '47258683',
            'ext': 'mp4',
            'title': 'Verification video',
            'age_limit': 18,
            'duration': 16,
            'thumbnail': r're:^https://cdn.*-pic.xvideos-cdn.com/.+\.jpg',
        }
    }]

    def _real_extract(self, url):
        domain, id_ = self._match_valid_url(url).group('domain', 'id')
        return self.url_result(f'https://{domain}/video{id_}/_', XVideosIE, id_)
