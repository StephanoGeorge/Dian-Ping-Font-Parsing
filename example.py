from pathlib import Path

import dian_ping_font_parsing

html_text = Path('example.html').read_text()
html = dian_ping_font_parsing.parse_html(html_text)
review_list = html.xpath("//div[@class='txt-c']")
for review in review_list:
    print(''.join((i.strip() for i in review.xpath('./text() | ./svgmtsi/text()'))))

# 米粉上菜很快～团购很实惠味道正和我的口味就是3量，都有点不够吃米粉消化的太快了配菜有很多，自助添加～有酸菜，海带，香菜，葱花，小米椒等～可能下次去要吃两碗了[委...
# 很炫酷的家烧烤店店面装饰霓虹灯，酷酷的～就连一次性手套🧤，“就爱这套”让人浮愚联翩啊包浆豆腐，端上桌，还冒着泡泡，热气腾腾，看着真爽肥肠卷大葱～昆明特色菜...
# 排队人好多，特别不开心排队太久了，对味道的期望值太高了店铺装饰好洋气～之前在重庆喝过～环境不错，适合打卡。奶盖蜜瓜，真的好甜，而且没有果肉，至少没喝到奇兰水仙，普通奶茶...
