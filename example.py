from pathlib import Path

import dian_ping_font_parsing

html_text = Path('example.html').read_text()
html = dian_ping_font_parsing.parse_html(html_text)
review_list = html.xpath("//div[@class='txt-c']")
for i in review_list:
    print(''.join(i.xpath('./text() | ./svgmtsi/text()')))
