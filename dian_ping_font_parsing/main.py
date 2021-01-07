import atexit
import itertools
import logging
import math
import re
import tempfile
from pathlib import Path

import pytesseract
import requests
import requests.adapters
import yaml
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from lxml import etree

_headers_computer = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4230.1 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh-TW;q=0.8,zh-HK;q=0.7,zh;q=0.5,en-US;q=0.3,en;q=0.2',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}

_fonts_path = Path.home() / '.config' / 'dian_ping_font_decrypt'
_fonts_path.mkdir(parents=True, exist_ok=True)
_fonts_path /= Path('fonts.yaml')
_fonts_path.touch(exist_ok=True)
_fonts_text = _fonts_path.read_text()
if _fonts_text:
    fonts = yaml.safe_load(_fonts_text)
else:
    fonts = {
        'css': {},
        'woff': {},
    }

_session = requests.Session()


def save_fonts():
    _fonts_path.write_text(yaml.safe_dump(fonts, allow_unicode=False, sort_keys=False))


atexit.register(save_fonts)


def parse_html(html_text: str) -> etree._Element:
    html = etree.HTML(html_text)
    css_url = html.xpath("//link[contains(@href,'svgtextcss')]/@href")
    if not css_url:
        return html
    css_url = f'https:{css_url[0]}'
    if css_url not in fonts['css']:
        css = _send_request(requests.Request(
            'GET', css_url,
        ).prepare()).text
        font_list = re.findall(r'@font-face\{font-family: "PingFangSC-Regular-(.+?)".+?'
                               r'format\("embedded-opentype"\),url\("(.+?\.woff)', css)
        fonts['css'][css_url] = {class_name: get_fonts(f'https:{font_url}') for class_name, font_url in font_list}
    for class_name, font in fonts['css'][css_url].items():
        nodes = html.xpath(f"//*[@class='{class_name}']")
        for node in nodes:
            node.text = ''.join([font[i] if i in font else i for i in node.text])
    return html


def get_fonts(font_url):
    if font_url in fonts['woff']:
        return fonts['woff'][font_url]
    font_content = _send_request(requests.Request(
        'GET', font_url
    ).prepare()).content
    with tempfile.NamedTemporaryFile(suffix='.woff') as io:
        io.write(font_content)
        ttf = TTFont(io.name)
        code_list = ttf.getGlyphOrder()[2:]
        code_list = [chr(int(i.replace('uni', ''), 16)) for i in code_list]
        code_list_chinese = code_list[10:]
        font_size = 40
        font_width = 42
        font_height = 52
        column = 30
        line_count = math.ceil(len(code_list_chinese) / column)
        image = Image.new('RGB', ((column + 1) * font_width, (line_count + 1) * font_height), (255, 255, 255))
        image_draw = ImageDraw.Draw(image)
        image_font = ImageFont.truetype(font=io.name, size=font_size)
        for line_index, line in enumerate(itertools.zip_longest(*([iter(code_list_chinese)] * column), fillvalue='')):
            image_draw.text((font_width, (line_index + 0.5) * font_height),
                            ''.join(line), font=image_font, fill='#000000')
        # image.save('font.jpg')
        result = pytesseract.image_to_string(image, lang='chi_sim')
        result = re.sub(r'[ \n]', '', result)
        result = dict(zip(code_list, [*[str(i) for i in range(1, 10)], '0', *result]))
        fonts['woff'][font_url] = result
        return result


def _send_request(prepared_request: requests.PreparedRequest) -> requests.Response:
    url = prepared_request.url
    prepared_request.prepare_headers({**_headers_computer, 'Host': re.search(r'^https?://(.+?)(/|$)', url).group(1)})
    while True:
        try:
            response = _session.send(prepared_request, timeout=6, allow_redirects=False)
            return response
        except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e1:
            continue
        except Exception as e:
            logging.error(f'Exception: {type(e).__name__}', exc_info=True)
