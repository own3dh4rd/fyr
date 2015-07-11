#coding: utf-8
import bs4
import urllib2
import sys, os
from Queue import Queue
import threading



if sys.platform == "win32":
    class UniStream(object):
        __slots__= ("fileno", "softspace",)

        def __init__(self, fileobject):
            self.fileno = fileobject.fileno()
            self.softspace = False

        def write(self, text):
            os.write(self.fileno, text.encode("utf_8") if isinstance(text, unicode) else text)

    sys.stdout = UniStream(sys.stdout)
    sys.stderr = UniStream(sys.stderr)

try:
    import uniconsole
except ImportError:
    sys.exc_clear()
else:
    del uniconsole



ing_categories = {
    u'Алкоголь': "http://eda.ru/wiki/ingredienty/wine_and_spirts/page{}",
    u'Бакалея': "http://eda.ru/wiki/ingredienty/grocery/page{}",
    u'Готовые продукты': "http://eda.ru/wiki/ingredienty/ready/page{}",
    u'Грибы': "http://eda.ru/wiki/ingredienty/fungi/page{}",
    u'Зелень и травы': "http://eda.ru/wiki/ingredienty/greenery/page{}",
    u'Крупы, бобовые и мука': "http://eda.ru/wiki/ingredienty/beans/page{}",
    u'Молочные продукты и яйца': "http://eda.ru/wiki/ingredienty/milk-and-eggs/page{}",
    u'Мясо и мясная гастрономия': "http://eda.ru/wiki/ingredienty/meats/page{}",
    u'Овощи и корнеплоды': "http://eda.ru/wiki/ingredienty/vegs/page{}",
    u'Орехи': "http://eda.ru/wiki/ingredienty/nuts/page{}",
    u'Птица': "http://eda.ru/wiki/ingredienty/poultry_and_game/page{}",
    u'Рыба и морепродукты': "http://eda.ru/wiki/ingredienty/fish/page{}",
    u'Специи и приправы': "http://eda.ru/wiki/ingredienty/spices/page{}",
    u'Сыры': "http://eda.ru/wiki/ingredienty/cheese/page{}",
    u'Фрукты и ягоды': "http://eda.ru/wiki/ingredienty/fruits-and-berries/page{}"
}



class IngredientsParser(Queue):
    def __init__(self):
        Queue.__init__(self)
        self._sentinel = "stopped"
        self.count = 0
        self.threads = []
        self.start()



    def get_ingredients(self, url):
        idx = 1
        while True:
            URL = url.format(idx)
            try:
               urllib2.urlopen(URL)
            except urllib2.HTTPError as e:
                return

            idx += 1
            yield URL



    def start(self):
        for category in ing_categories:
            URL = ing_categories[category]
            t = threading.Thread(target=self.parse, args=(URL, category))
            self.threads.append(t)
            t.start()
            # t.join()



    def parse(self, URL, category):
        self.generator = self.get_ingredients(URL)
        for url in self.generator:
            parser = bs4.BeautifulSoup(urllib2.urlopen(url).read().decode('utf-8'))
            for tag in parser.findAll('div', {'class': 'b-list-item'}):
                name = img = None
                for div in tag.find('div', {'class': 'clearfix'}):
                    if isinstance(div, bs4.element.Tag):
                        if div.get(u'class') == ['b-list-item-right']:
                            name = unicode(div.h2.a.get_text().strip())

                            #по этому url список подпродуктов данного продукта, тобишь красный абсент это подпродукт абсента
                            _url = div.h2.a['href']
                        elif div.get(u'class') == ['b-list-item-left']:
                            img = unicode(div.a.img['src'].strip())


                if name and img:
                    self.put((name, category, img))
                else: print '!!! ERROR: %s .!!!!' % (url)

                sub = bs4.BeautifulSoup(urllib2.urlopen(_url).read().decode('utf-8'))
                for tag in sub.findAll('div', {'class': 'b-ingredient-list-item'}):
                    sub_name = sub_img = None
                    if tag:
                        for div in tag.find('div', {'class': 'hover'}):
                            if isinstance(div, bs4.element.Tag):
                                if div and div.get(u'class') == ['b-ingredient-list-item__left']:
                                    sub_name = unicode(div.h3.get_text().strip())
                                elif div and div.get(u'class') == ['g-float-right']:
                                    try:
                                        sub_img = unicode(div.img['src'].strip())
                                    except TypeError:
                                        sub_img = None
                

                    if sub_name:
                        self.put((sub_name, category, sub_img))
                    else: print '!!! ERROR: %s .!!!!' % (url)


        with threading.RLock():
            self.count += 1
            if self.count == len(ing_categories):
                for _ in range(len(self.threads)):
                    self.put(self._sentinel)



    def __iter__(self):
        return iter(self.get, self._sentinel)


    def next(self):
        item = self.get()
        if item is self._sentinel:  
            self.count = 0
            raise StopIteration
        else:
            return item
