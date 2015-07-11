import ingredients
import recipes
from app import models, db
import threading
import sys



class Initializator:
    def init(self):
        pass


class InitCategories(Initializator):
    def __init__(self):
        pass


    def init(self):
        print "Start parse and init CATEGORIES AND TAGS..."
        for category in ingredients.ing_categories:
            if db.session.query(models.Category).filter_by(name=category).first():
                continue
            db.session.add(models.Category(name=category))
            db.session.commit()
            print "\tCategory of product was added: %s" % (category)

        print "Categories of products was added: %s" % db.session.query(models.Category).count()

        for category in recipes.categories:
            if db.session.query(models.CategoryRecipe).filter_by(name=category).first():
                continue
            c = models.CategoryRecipe(name=category)
            db.session.add(c)
            db.session.commit()
            print "\tCategory of recipe was added: %s" % (category)

        print "Categories of recipes was added: %s" % db.session.query(models.CategoryRecipe).count()

        for tag in recipes.tags:
            if db.session.query(models.RecipeTags).filter_by(name=tag).first():
                continue

            t = models.RecipeTags(name=tag)
            db.session.add(t)
            db.session.commit()
            print "\tTag was added: %s" % (tag)
        
        print "Categories of recipes was added: %s" % db.session.query(models.RecipeTags).count()
        print "End init."


class InitIngredients(Initializator):
    def __init__(self):
        pass


    def init(self):
        print "Start parse and init PRODUCTS..."
        # threads = []
        parser = ingredients.IngredientsParser()
        for _ in range(10):
            t = threading.Thread(target=self.add_product, args=(parser, ))
            # threads.append(t)
            t.start()
            t.join()

           
        print "End init."


    def add_product(self, parser):
        idx = {} #cached categories
        for category in db.session.query(models.Category).all():
            idx[category.name] = category

        for data in parser:
            if db.session.query(models.Product).filter_by(name=data[0]).first():
                return

            new_p = models.Product(name=data[0], image=data[2])
            db.session.add(new_p)
            new_p.follow(idx[data[1]])
            db.session.add(new_p)
            db.session.commit()

            print  "\tProduct was added: %s" % (data[0])



class InitRecipes(Initializator):
    def __init__(self):
        pass

    def init(self):
        print "Start parse and init RECIPES..."
        parser = recipes.RecipeParser()

        for _ in range(10):
            t = threading.Thread(target=self.add_recipe, args=(parser, ))
            t.start()
            t.join()


    def add_recipe(self, parser):
        for data in parser:
            for key in data:
                #type(key) is tuple
                recipe_name = key[0]
                category = key[1]

                exists_category = db.session.query(models.CategoryRecipe).filter(models.CategoryRecipe.name == category).first()


                for d in data[key]:
                    for i in d:
                        if i == 'steps':
                            steps = d[i]
                        elif i == 'portions':
                            portions = d[i]
                        elif i == 'image':
                            image = d[i]
                        elif i == 'cookingTime':
                            cooking_time = d[i]
                        elif i == 'ingredients':
                            ingredients = []
                            for name in d[i]:

                                w = d[i][name]
                                ingredients.append((name, w))

                        elif i == 'tags':
                            tags = []
                            for t in d[i]:
                                exists_tag = db.session.query(models.RecipeTags).filter(models.RecipeTags.name == t).first()
                                if not exists_tag:
                                    exists_tag = models.RecipeTags(name=t)
                                    db.session.add(exists_tag)
                                    db.session.commit()

                                tags.append(exists_tag)

                r = models.Recipe(name=recipe_name, steps=steps)
                for t in ingredients:
                    name = t[0]
                    weight = t[1]

                    product = db.session.query(models.Product).filter(models.Product.name == name).first()
                    if not product:
                        product = models.Product(name=name, image='')
                        db.session.add(product)
                        db.session.commit()

                        print '\t\tProduct was not founded %s' % (name)
                    a = models.Association(weight=weight)
                    a.product = product
                    with db.session.no_autoflush:
                        r.ingredients.append(a)

                for tag in tags:
                    r.follow_tag(tag)
                    # db.session.add(r)
                    # db.session.commit()

                r.cookingTime = cooking_time
                r.portions = portions
                r.category = exists_category
                r.image = image
                db.session.add(r)
                db.session.commit()
                print '\tRecipe was added: %s' % (recipe_name)


        print "End init."



if __name__ == "__main__":
    # db.drop_all()
    # db.create_all()

    # inits = [InitCategories(), InitIngredients(), InitRecipes()]
    inits = [InitRecipes()]

    for i in inits:
        i.init()

    db.session.close()