#coding: utf-8
from app import app, db, models
from flask import render_template, jsonify, request, abort
from sqlalchemy import func



#API:
#GET - /recipe/id - получить json с рецептом

#GET - /ingredient/id - получить json с ингредиентом

#POST - /recipes
#поиск рецептов по ингредиентам, которые передаются в теле запроса jsonoм,
#{ingredients: [], mode: 0/1}





@app.route('/')
@app.route('/index')
def index():
	return render_template('index.html')



@app.route('/recipe/<int:id>', methods=["GET"])
def recipe(id):
	if request.method == "GET":
		recipe = db.session.query(models.Recipe).get(id)
		return jsonify(recipe.serializable() if recipe else abort(404))



@app.route('/ingredient/<int:id>', methods=["GET"])
def ingredient(id):
	if request.method == "GET":
		ingredient = db.session.query(models.Product).get(id)
		return jsonify(ingredient.serializable() if ingredient else abort(404))



@app.route('/recipes', methods=['POST'])
def search():
	if request.method == 'POST':
		if request.json:
			args = request.json.get('ingredients', [])
			mode = int(request.json.get('mode', 0))
		else:
			abort(404)

		if not args:
			return jsonify({})

		# print "Args from client: %s. Mode: %s" % (args, mode)

		recipes = db.session.query(models.Recipe)\
		.join(models.Association, (models.Association.left_id == models.Recipe.id))\
		.join(models.Product, (models.Product.id == models.Association.right_id))\
		.filter(func.lower(models.Product.name).in_([func.lower(a) for a in args])).all()

		if mode:
			# result = []
			# args_id = set([p.id for a in args for p in db.session.query(models.Product).filter(func.lower(models.Product.name) == func.lower(a)).all()])


			# db.session.query(models.Recipe).join(models.Association, (models.Association.left_id == models.Recipe.id)).filter()
			# for recipe in recipes:
			# 	products_id = set([p.right_id for p in recipe.ingredients])

			# 	if len(args_id) == len(products_id):
			# 		# print args_id
			# 		# print products_id
			# 		# print args_id & products_id
			# 		# print
			# 		if args_id == products_id:
			# 			result.append(recipe)

			# recipes = result
			r = set()
			for a in args:
				result = set(db.session.query(models.Recipe)\
						.join(models.Recipe.ingredients)\
						.join(models.Product)\
						.filter(func.lower(models.Product.name) == a.lower()).all())

				if not r:
					r = result
				else:
					r = r & result

			recipes = r



		return jsonify({'recipes': [r.id for r in recipes]} if recipes else {})


@app.route('/autocomplete', methods=['POST'])
def get_products():
	if request.method == "POST":
		if request.json: term = unicode(request.json['term']).lower()
		else: abort(400)

		if not term: return jsonify({})

		data = []
		# result = db.session.query(models.Product).filter(func.lower(models.Product.name).ilike(term.lower())).all()
		result = db.session.query(models.Product).filter(func.lower(models.Product.name).startswith(term)).all()
		for x in result:
			data.append(x.name)

		return jsonify({'ingredients': data})








