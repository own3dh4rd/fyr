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



COUNT = 10

categories = {
	u'Выпечка и десерты': "http://eda.ru/recipelist/desserts/page{}?sorting=Rate",
	u'Завтраки': "http://eda.ru/recipelist/breakfast/page{}?sorting=Rate",				
	u'Закуски': "http://eda.ru/recipelist/snack/page{}?sorting=Rate",
	u"Напитки": "http://eda.ru/recipelist/drinks/page{}?sorting=Rate",
	u"Основные блюда": "http://eda.ru/recipelist/main_course/page{}?sorting=Rate",
	u"Паста и пицца": "http://eda.ru/recipelist/paste/page{}?sorting=Rate",
	u"Ризотто": "http://eda.ru/recipelist/risotto/page{}?sorting=Rate",
	u"Салаты": "http://eda.ru/recipelist/salad/page{}?sorting=Rate",
	u"Супы": "http://eda.ru/recipelist/soups/page{}?sorting=Rate",
	u"Соусы и маринады": "http://eda.ru/recipelist/sauce/page{}?sorting=Rate",
	u"Сэндвичи": "http://eda.ru/recipelist/sandwiches/page{}?sorting=Rate",
	u"Бульоны": "http://eda.ru/recipelist/bouillon/page{}?sorting=Rate"
}


tags = [
	u'Китайская кухня',
	u'Мексиканская кухня',
	u'Грузинская кухня',
	u'Французская кухня',
	u'Японская',
	u'Индийская',
	u'Русская',
	u'Узбекская',
	u'Армянская',
	u'Итальянская',
	u'Испанская',
	u'Азербайджанская',
	u'Вегетаринская еда',
	u'Основные блюда',
	u'Низкокалорийная еда',
	u'Детское меню',
	u'Постная еда',
	u'Пошаговые рецепты',
]

#RecipeRarser - класс, парсящий HTML, представляет из себя итерируемую очередь
#Usage:
#	parser = RecipeParser()
#	for data in parser:
#		...
#
#
#
#	Объекты, возвращаемые итератором, это словарь, ключами которого являются Имя рецепта и его категория.
#	Значение это массив словарей, ключами которого являются image, steps, tags, cookingTime, ingredients, potrions
#
#	Example:
#
#
#parser = RecipeParser()
# for data in parser:
# 	for key in data:
# 		recipeName = key[0]
# 		category = key[1]

# 		print "RecipeName: %s" % (recipeName)
# 		print "Category: %s" % (category)
# 		for d in data[key]:
# 			for i in d:
# 				print "%s : %s" % (i, d[i])
#
# Indredients - это словарь, ключи - ингредиент, значение - количество
# Steps - словарь, ключи - номер шага, значение - tupple из двух элементов: описание шага и URL картинки шага, если есть, иначе None
# Tags - массив из тэгов рецепта
# portions, cookingTime, image, name, category - строки
class RecipeParser(Queue):
	def __init__(self):
		self._sentinel = "stopped"
		Queue.__init__(self)
		self.count = 0
		self.threads = []


	def get_recipes(self, url):
		"""Generator for the link references to recipes """
		for idx in range(1, COUNT):
			URL = url.format(idx)
			print "Reading URL: %s" % (URL)

			try:
				parser = bs4.BeautifulSoup(urllib2.urlopen(URL).read().decode('utf-8'))
			except urllib2.HTTPError as e:
				return

			for h3 in parser.findAll('h3'):
				if h3.a and h3.a['id'].startswith('link-recipewidget-recipeName-'):
					yield h3.a['href']


	def start(self):
		for category in categories:
			URL = categories[category]
			t = threading.Thread(target=self.parse, args=(URL, category))
			self.threads.append(t)
			t.start()



	def parse(self, URL, category):
		self.generator = self.get_recipes(URL)

		for url in self.generator:
			parser = bs4.BeautifulSoup(urllib2.urlopen(url).read().decode('utf-8'))
			data = {}

			recipeName = self.name(parser)
			data[(recipeName, category)] = []

			functions = [self.image, self.cookingTime, self.ingredients, self.portions, self.steps, self.tags]
			try:
				for f in functions:
					data[(recipeName, category)].append({
						f.__name__: f(parser)
					})
			except TypeError as e:
				print 'Error in %s' % (recipeName)
				data[(recipeName, category)] = []
				continue

			self.put(data)

		with threading.RLock():
			self.count += 1
			if self.count == len(categories):
				for _ in range(len(self.threads)):
					self.put(self._sentinel)


	def __iter__(self):
		self.start()
		return iter(self.get, self._sentinel)


	def next(self):
		item = self.get()
		if item is self._sentinel: 
			raise StopIteration
		else: 
			return item


	def name(self, url):
		"""Returns name of recipe"""
		name = None
		name = url.h1.get_text().strip()

		if name: 
			return unicode(name)
		else:
			raise TypeError


	def image(self, url):
		img = url.find('link', {'rel': 'image_src'}) # full-size
		if img:
			img = img['href']
		else:
			raise TypeError

		return unicode(img)


	def ingredients(self, url):
		"""Return ingredients of the recipe"""
		ingredients = {}
		for tr in url.findAll("tr"):
			if tr and tr.get(u'class') == ['ingredient']:
				for td in tr.findAll("td"):
					if td and td.get(u'class') == ['ingredient-measure-amount']:
						count = td.span.get_text().strip()
					elif td and td.a and td.a.get(u'class') == ['name']:
						#если есть ссылка, то название может отличаться, а в hrefe есть ссылка на продукт
						name = unicode(td.a.get_text().strip())
					elif td and td.get(u'class') == ['name']:
						name = unicode(td.span.get_text().strip())
				if name and count:
					ingredients[name] = count
					name = count = None
				else:
					raise TypeError

		return ingredients


	def cookingTime(self, url):
		"""Return time of cook """
		cook_time = url.find('p', 'cook-time').find('time')
		if cook_time:
			cook_time = cook_time.get_text().strip()
		else:
			cook_time = u'unknown'

		return unicode(cook_time)


	def steps(self, url):
		"""Return steps"""
		steps = {}
		img = None
		instructions = url.find('ol', {'class': 'instructions'})
		for li in instructions.findAll('li', {'class': 'instruction'}):
			for tag in li.findAll('div'):
				try:
					if tag and tag.get(u'class') == ['text']:
						step = int(tag.b.get_text().strip()[:-1])
						text = unicode(tag.get_text().strip()[2:].strip())
					elif tag:
						img = tag.find('img')['src']
				except AttributeError:
					step = 1
					text = tag.get_text().strip()[2:].strip()

			if step:
				if text:
					steps[step] = (text, img)
				else:
					continue
			else:
				raise TypeError


		return steps


	def portions(self, url):
		portions = url.find('span', {'class': 'portions-count-for-print'})
		if portions:
			portions = portions.get_text().strip()
		else:
			portions = 'unknown'
		return unicode(portions)


	def tags(self, url):
		result = []
		tags = url.findAll('a', {'class': 'tag'})
		for tag in tags:
			if tag and tag.get(u'cuisine-type'):
				result.append(unicode(tag.strong.get_text().strip()))
			elif tag and tag.get(u'category'):
				continue
			elif tag and(not tag.get(u'cuisine-type') and not tag.get(u'category')):
				result.append(unicode(tag.strong.get_text().strip()))

		return result


def main():
	parser = RecipeParser()

	result = {}

	for data in parser:
		for key in data:
			recipeName = key[0]
			category = key[1]

			print "name: %s" % (recipeName)
			print "category: %s" % (category)
			for d in data[key]:
				for i in d:
					if i == 'ingredients':
						for k in d[i]:
							print k, d[i][k] 
					# print "%s : %s" % (i, d[i])



if __name__ == "__main__":
	main()