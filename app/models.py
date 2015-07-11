from app import db, app
# import sqlalchemy.orm

# from citext import CIText



category_products = db.Table('category_products',
	db.Column('category_id', db.Integer, db.ForeignKey('categories.id')),
	db.Column('product_id', db.Integer, db.ForeignKey('products.id'))
)

tags = db.Table('tags',
	db.Column('recipe_id', db.Integer, db.ForeignKey('recipes.id')),
	db.Column('tag_id', db.Integer, db.ForeignKey('recipe_tags.id'))
)


class Category(db.Model):
	__tablename__ = 'categories'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), unique=True, nullable=False, index=True)
	products = db.relationship('Product', 
		secondary=category_products,
		backref=db.backref('products', lazy='dynamic'),
		lazy='dynamic'
	)


	def __init__(self, name):
		self.name = name


	def __repr__(self):
		return '<Category name %s>' % (self.name)


	def followed_products(self):
		return Product.query.join(category_products, (category_products.c.category_id == self.id)).filter(category_products.c.product_id == Product.id)


	def follow(self, product):
		if not self.is_following(product):
			self.products.append(product)
			return self


	def is_following(self, product):
		return self.products.filter(category_products.c.product_id == product.id).count()



class CategoryRecipe(db.Model):
	__tablename__ = 'category_recipe'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), unique=True, nullable=False)

	def __init__(self, name):
		self.name = name



class RecipeTags(db.Model):
	__tablename__ = 'recipe_tags'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), unique=True, nullable=False)
	recipes = db.relationship('Recipe',
		secondary=tags,
		backref=db.backref('tags_of_recipe', lazy='dynamic'),
		lazy='dynamic'
	)


	def __init__(self, name):
		self.name = name




class Association(db.Model):
	__tablename__ = 'associations'

	left_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), primary_key=True)
	right_id = db.Column(db.Integer, db.ForeignKey('products.id'), primary_key=True)
	weight = db.Column(db.String(256))
	product = db.relationship('Product', backref='products_assoc')



class Recipe(db.Model):
	__tablename__ = 'recipes'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(256), nullable=False)
	image = db.Column(db.String(256), nullable=True)
	cookingTime = db.Column(db.String(32))
	portions = db.Column(db.String(32))
	category_id = db.Column(db.Integer, db.ForeignKey('category_recipe.id'))
	category = db.relationship('CategoryRecipe', backref='rec') 
	steps = db.Column(db.PickleType)
	tags = db.relationship('RecipeTags',
		secondary=tags,
		backref=db.backref('recipe_of_tag', lazy='dynamic'),
		lazy='dynamic'
	)
	ingredients = db.relationship('Association', backref=db.backref('recipes_assoc', uselist=True))


	def serializable(self):
		json = {}
		json['recipe_name'] = self.name
		json['recipe_id'] = self.id
		json['recipe_image'] = self.image
		json['recipe_cookingTime'] = self.cookingTime
		json['recipe_portions'] = self.portions
		json['recipe_steps'] = self.steps


		json['recipe_tags'] = []
		for x in self.tags.all():
			json['recipe_tags'].append(x.name)


		json['recipe_ingredients'] = []
		for x in self.ingredients:
			json['recipe_ingredients'].append((x.product.name, x.weight))

		return {'recipe': json}


	def __init__(self, name, steps):
		self.name = name
		self.steps = steps



	def follow_tag(self, tag):
		if not self.has_tag(tag):
			self.tags.append(tag)


	def unfollow_tag(self, tag):
		if self.has_tag(tag):
			self.tags.remove(tag)


	def has_tag(self, tag):
		return self.tags.filter(tags.c.tag_id == tag.id).count()


	def follow_product(self, assoc):
		if not self.has_product(assoc):
			self.ingredients.append(assoc)


	def unfollow_product(self, assoc):
		if self.has_product(assoc):
			self.ingredients.remove(assoc)


	def has_product(self, assoc):
		return self.ingredients.filter(assoc.product.id == Association.right_id).count()


	def followed_products(self):
		return self.ingredients




class Product(db.Model):
	__tablename__ = 'products'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String, nullable=False, unique=True, index=True)
	# name = db.Column(CIText(), nullable=False, unique=True, index=True)
	image = db.Column(db.String, nullable=True)
	categories = db.relationship('Category',
		secondary=category_products,
		backref=db.backref('bpsroducts', lazy='dynamic'),
		lazy='dynamic'
	)


	def __init__(self, name, image):
		self.name = name
		self.image = image


	def followed_categories(self):
		return Category.query.join(category_products, (category_products.c.product_id == self.id)).filter(category_products.c.category_id == Category.id)


	def follow(self, category):
		if not self.is_following(category):
			self.categories.append(category)
			return self


	def is_following(self, category):
		return self.categories.filter(category_products.c.category_id == category.id).count()


	
	def serializable(self):
		json = {}
		json['product_name'] = self.name
		json['product_image'] = self.image
		json['product_categories'] = []
		for c in self.categories.all():
			json['product_categories'].append(c.name)

		return {'ingredient': json}


