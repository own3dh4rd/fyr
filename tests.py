#coding=utf-8
import os
import unittest

from app import app, db
from app import model


class TestCase(unittest.TestCase):
	def setUp(self):
		app.config['TESTING'] = True
		app.config['CSRF_ENABLED'] = False
		app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:glotka@localhost/test'
		self.app = app.test_client()
		db.create_all()



	def tearDown(self):
		db.session.remove()
		db.drop_all()



	def test_products(self):
		#тест для продуктов и категорий продуктов
		categories = [
			model.Category(name='Крупы, бобовые и мука'),
			model.Category(name='Молочные продукты и яйца'),
			model.Category(name='Бакалея'),
			model.Category(name='Орехи')
		]

		products = [ 
			(model.Product(name='Шоколад темный', image='src_image'), categories[0]),
			(model.Product(name='Масло сливочное', image='src_image'), categories[1]), 
			(model.Product(name='Сахар коричневый', image='src_image'), categories[2]), 
			(model.Product(name='Яйцо куриное', image='src_image'), categories[1]),
			(model.Product(name='Мука пшеничная', image='src_image'), categories[0]), 
			(model.Product(name='Орехи грецкие', image='src_image'), categories[3])
		]

		for c in categories:
			db.session.add(c)
			db.session.commit()

		for p in products:
			db.session.add(p[0])
			db.session.commit()

		assert model.Category.query.count() == 4
		assert model.Product.query.count() == 6

		for t in products:
			pr, ct = t[0], t[1:]

			for c in ct:
				pr.follow(c)

				db.session.add(pr)
				db.session.commit()
				assert pr.is_following(c)

			assert pr.categories.count() == len(ct)
			assert pr.followed_categories().count() == len(ct)


	def test_recipes(self):
		r = model.Recipe(name='r', steps=[])

		p1 = model.Product(name='p1', image='image')
		p2 = model.Product(name='p2', image='image')
		p3 = model.Product(name='p3', image='image')
		p4 = model.Product(name='p4', image='image')
		e1 = model.ExtProduct('500gramm')
		e2 = model.ExtProduct('400gramm')
		e3 = model.ExtProduct('300gramm')
		e4 = model.ExtProduct('200gramm')
		e1.mainproduct = p1
		e2.mainproduct = p2
		e3.mainproduct = p3
		e2.mainproduct = p4

		db.session.add(p1)
		db.session.add(p2)
		db.session.add(p3)
		db.session.add(p4)
		db.session.add(e1)
		db.session.add(e2)
		db.session.add(e3)
		db.session.add(e4)
		db.session.add(r)
		db.session.commit()


		assert r.has_product(e1) == 0
		assert r.has_product(e2) == 0
		assert r.has_product(e3) == 0

		r.follow_product(e1)
		r.follow_product(e2)
		r.follow_product(e3)
		db.session.add(r)
		db.session.commit()

		assert r.has_product(e1) == 1
		assert r.has_product(e2) == 1
		assert r.has_product(e3) == 1


		assert r.followed_products().count() == 3


		r.unfollow_product(e1)
		r.unfollow_product(e2)
		r.unfollow_product(e3)
		db.session.add(r)
		db.session.commit()

		assert r.has_product(e1) == 0
		assert r.has_product(e2) == 0
		assert r.has_product(e3) == 0


		assert r.followed_products().count() == 0


	def test_rec_cat(self):
		r = model.Recipe(name='r', steps=[])
		c = model.CategoryRecipe(name=u'Выпечка и десерты')

		db.session.add(c)
		db.session.add(r)
		db.session.commit()

		r.category = c

		db.session.add(r)
		db.session.commit()

		assert r.category.id == c.id
		assert r.category.name == c.name

		r.category = None

		db.session.add(r)
		db.session.commit()

		assert r.category == None


	def test_tags(self):
		t1 = model.RecipeTags(name='t1')
		t2 = model.RecipeTags(name='t2')

		r1 = model.Recipe(name='r1', steps=[])
		r2 = model.Recipe(name='r2', steps=[])

		db.session.add(t1)
		db.session.add(t2)
		db.session.add(r1)
		db.session.add(r2)
		db.session.commit()


		assert r1.unfollow_tag(t1) == None
		assert r2.unfollow_tag(t1) == None

		r1.follow_tag(t1)
		db.session.add(r1)
		db.session.commit()

		assert r1.has_tag(t1) == 1
		assert r1.has_tag(t2) == 0

		r1.unfollow_tag(t1)
		db.session.add(r1)
		db.session.commit()

		assert r1.has_tag(t1) == 0


	def test_recipe(self):
		#необходимо составить 2 запроса к базе: по заданному кортежу ингридиентов отдать кортеж рецептов
		#1). по включению(то есть в рецепте есть все продукты из запроса)
		#2). хотя бы один из ингридиентов есть в рецепте

		#второй делается так: пройтись по всем ингридиентам, а т.к. у рецепта есть бэкреф, то легко вытащить все рецепты
		#по каждому продукту можно найти его инстанс Product в базе. далее пройтись по всем ExtProduct, у которых mainproduct.id совпадает с Product.id
		#и выдернуть все рецепты по backref

		#первый: 


		# db.session.query(model.Recipe).
		steps = {u'step1': u'img', u'step2': u'img', u'step3': u'img'}
		r1 = model.Recipe(name='r1', steps=steps)
		r2 = model.Recipe(name='r2', steps=steps)
		r3 = model.Recipe(name='r3', steps=steps)
		r4 = model.Recipe(name='r4', steps=steps)

		db.session.add(r1)
		db.session.commit()
		db.session.add(r2)
		db.session.commit()
		db.session.add(r3)
		db.session.commit()
		db.session.add(r4)

		db.session.commit()


		p1 = model.Product('p1', '')
		p2 = model.Product('p2', '')
		p3 = model.Product('p3', '')
		p4 = model.Product('p4', '')
		p5 = model.Product('p5', '')
		p6 = model.Product('p6', '')
		db.session.add(p1)
		db.session.add(p2)
		db.session.add(p3)
		db.session.add(p4)
		db.session.add(p5)
		db.session.add(p6)
		db.session.commit()

		e1 = model.ExtProduct('100g')
		e1.mainproduct = p1

		e2 = model.ExtProduct('200g')
		e2.mainproduct = p2

		e3 = model.ExtProduct('300g')
		e3.mainproduct = p3

		e4 = model.ExtProduct('400g')
		e4.mainproduct = p4

		e5 = model.ExtProduct('500g')
		e5.mainproduct = p5

		e6 = model.ExtProduct('600g')
		e6.mainproduct = p6
		db.session.add(e1)
		db.session.commit()
		db.session.add(e2)
		db.session.commit()
		db.session.add(e3)
		db.session.commit()
		db.session.add(e4)
		db.session.commit()
		db.session.add(e5)
		db.session.commit()
		db.session.add(e6)
		db.session.commit()

		assert e1.mainproduct == p1
		assert e2.mainproduct == p2
		assert e3.mainproduct == p3
		assert e4.mainproduct == p4
		assert e5.mainproduct == p5
		assert e6.mainproduct == p6

		r1.follow_product(e1)		
		r1.follow_product(e2)
		db.session.add(r1)
		db.session.commit()


		assert r1.ingredients.count() == 2
		assert r1.ingredients.all() == [e1, e2]
		assert e1.recipes.all() == [r1]
		assert e2.recipes.all() == [r1]
		

		r2.follow_product(e3)
		r2.follow_product(e4)
		db.session.add(r2)
		db.session.commit()

		assert r2.ingredients.count() == 2
		assert r2.ingredients.all() == [e3, e4]
		assert e3.recipes.all() == [r2]
		assert e4.recipes.all() == [r2]



		r3.follow_product(e5)
		r3.follow_product(e6)
		db.session.add(r3)
		db.session.commit()

		assert r3.ingredients.count() == 2
		assert r3.ingredients.all() == [e5, e6]
		assert e5.recipes.all() == [r3]
		assert e6.recipes.all() == [r3]

		r4.follow_product(e1)
		r4.follow_product(e4)
		r4.follow_product(e2)
		db.session.add(r4)
		db.session.commit()

		assert r4.ingredients.count() == 3
		assert r4.ingredients.all() == [e1, e2, e4]
		assert e1.recipes.all() == [r1, r4]
		assert e2.recipes.all() == [r1, r4]
		assert e4.recipes.all() == [r2, r4]

		q1_result = []
		query1 = ['p1']
		for pr_name in query1:
			q_pr = db.session.query(model.Product).filter_by(name = pr_name).first()

			assert q_pr == p1

			q_ext = db.session.query(model.ExtProduct).filter_by(product_id = q_pr.id).all()

			assert q_ext == [e1]

			assert q_ext[0].recipes.all() == [r1, r4]



if __name__ == '__main__':
	unittest.main()

