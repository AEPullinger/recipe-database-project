from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length
from sqlalchemy import select, event
from sqlalchemy.orm import joinedload

# My own imports
from models import db, User, Recipe, Category, Measurement, Ingredient, RecipeQuantity
from queries import login as query_login, create_recipe, search_recipes_unified, update_password
from setup_db import create_data

app = Flask(__name__)
app.secret_key = ""
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipe_tin.db'
app.config['SQLALCHEMY_ECHO'] = False

# Initialize Extensions
bootstrap = Bootstrap5(app)
db.init_app(app)
csrf = CSRFProtect(app)

### Login/Logout Logic
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login" #type: ignore

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 36)])
    password = PasswordField('Password', validators=[DataRequired(), Length(3, 150)])
    remember = BooleanField('Remember me')
    submit = SubmitField()
    
class LogoutForm(FlaskForm):
    pass

class ResetPasswordForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    old_password = PasswordField('Old Password', validators=[DataRequired(), Length(3, 150)])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(3, 150)])
    submit = SubmitField('Update Password')
    
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = query_login(db.session, form.username.data, form.password.data)
        
        if user:
            login_user(user, remember=form.remember.data)
            return redirect(url_for('home'))
        
        flash("Invalid username or password")
    return render_template('login.html', form=form)

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.") 
    return redirect(url_for('login'))

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = db.session.execute(
            select(User).where(User.user_name == form.username.data)
        ).scalar_one_or_none()

        if user:
            success = update_password(
                db.session, 
                user.user_id, 
                form.new_password.data, 
                form.old_password.data
            )

            if success:
                flash("Password updated successfully!")
                return redirect(url_for('login'))
            else:
                flash("Incorrect old password.")
        else:
            flash("Username not found.")
            
    return render_template('reset_password.html', form=form)

@app.route('/')
@app.route('/home')
@login_required
def home():
    stmt = (
        select(Recipe)
        .options(
            joinedload(Recipe.ingredients).joinedload(RecipeQuantity.ingredient),
            joinedload(Recipe.categories)
        )
        .where(Recipe.uploaded_by == current_user.user_id)
        .order_by(Recipe.recipe_order)
    )
    recipes = db.session.execute(stmt).unique().scalars().all()

    categories = db.session.execute(select(Category).where(Category.category_name != 'Default')).scalars().all()
    measurements = db.session.execute(select(Measurement)).scalars().all()

    return render_template('index.html', recipes=recipes, categories=categories, measurements=measurements, is_searching=False)

@app.route('/create-recipe', methods=['POST'])
@login_required
def create_recipe_route():
    raw_cats = request.form.get('final_categories', '')
    cat_names = [c.strip() for c in raw_cats.split(',') if c.strip()]
    if 'Default' not in cat_names:
        cat_names.append('Default')

    names = request.form.getlist('ingredients[]')
    qtys = request.form.getlist('quantities[]')
    meas = request.form.getlist('measurements[]')
    
    ingredients_list = []
    for i in range(len(names)):
        if names[i].strip():
            ingredients_list.append({
                'name': names[i].strip(),
                'qty': float(qtys[i]) if qtys[i] else 0.0,
                'meas_id': int(meas[i])
            })

    recipe_data = {
        'name': request.form.get('name'),
        'desc': request.form.get('desc'),
        'steps': request.form.get('steps'),
        'categories': cat_names,
        'ingredients_list': ingredients_list
    }

    result = create_recipe(db.session, recipe_data, current_user.user_id)

    if result:
        flash("Recipe created successfully!")
    else:
        flash("There was an error saving your recipe.")

    return redirect(url_for('home'))

@app.route('/edit-recipe', methods=['POST'])
@login_required
def edit_recipe():
    recipe_id = request.form.get('recipe_id')
    if not recipe_id:
        abort(400)
    
    recipe = db.session.get(Recipe, int(recipe_id))
    if not recipe or recipe.uploaded_by != current_user.user_id:
        abort(404)

    recipe.recipe_name = request.form.get('name')
    recipe.recipe_desc = request.form.get('desc')
    recipe.steps = request.form.get('steps')

    raw_cats = request.form.get('final_categories', '')
    cat_names = [c.strip() for c in raw_cats.split(',') if c.strip()]
    if 'Default' not in cat_names:
        cat_names.append('Default')

    recipe.categories = []
    for name in cat_names:
        cat = db.session.execute(select(Category).filter_by(category_name=name)).scalar_one_or_none()
        if not cat:
            cat = Category(category_name=name)
            db.session.add(cat)
        recipe.categories.append(cat)

    recipe.ingredients = [] 

    names = request.form.getlist('ingredients[]')
    qtys = request.form.getlist('quantities[]')
    meas = request.form.getlist('measurements[]')
    
    for name, qty, meas_id in zip(names, qtys, meas):
        val = name.strip()
        if val:
            # Check for existing ingredient
            ing = db.session.execute(
                select(Ingredient).filter_by(ingredient_name=val)
            ).scalar_one_or_none()
            
            if not ing:
                ing = Ingredient(ingredient_name=val)
                db.session.add(ing)
                db.session.flush()

            # Append new quantity record
            recipe.ingredients.append(RecipeQuantity(
                rq_ingred_id=ing.ingredient_id,
                rq_quantity=float(qty) if qty else 0.0, 
                rq_measur_id=int(meas_id)
            ))

    db.session.commit()
    return redirect(url_for('home'))

@app.route('/get-recipe/<int:recipe_id>')
@login_required
def get_recipe(recipe_id):
    stmt = (
        select(Recipe)
        .options(
            joinedload(Recipe.ingredients).joinedload(RecipeQuantity.ingredient),
            joinedload(Recipe.ingredients).joinedload(RecipeQuantity.measurement),
            joinedload(Recipe.categories)
        )
        .where(Recipe.recipe_id == recipe_id)
        .order_by(Recipe.recipe_order)
    )
    
    result = db.session.execute(stmt).unique() 
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        return {"error": "Not found"}, 404

    return {
        "name": recipe.recipe_name,
        "desc": recipe.recipe_desc,
        "steps": recipe.steps,
        "categories": [c.category_name for c in recipe.categories],
        "ingredients": [
            {
                "name": i.ingredient.ingredient_name if i.ingredient else "Unknown",
                "qty": i.rq_quantity,
                "meas_id": int(i.rq_measur_id) if i.rq_measur_id else 1
            } for i in recipe.ingredients
        ]
    }
    
@app.route('/delete-recipe/<int:recipe_id>', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    from queries import delete_recipe

    if delete_recipe(db.session, recipe_id):
        flash("Recipe deleted!")
    else:
        flash("Error deleting recipe.")
        
    return redirect(url_for('home'))
    
@app.route('/search-recipes')
@login_required
def search_recipes():
    name = request.args.get('name', '')
    ingred = request.args.get('ingredient', '')
    cats_raw = request.args.get('categories', '')
    cat_list = [c.strip() for c in cats_raw.split(',') if c.strip()]

    is_searching = any([name, ingred, cat_list])
    
    recipes = search_recipes_unified(db.session, current_user.user_id, name, ingred, cat_list)
    return render_template('partials/_recipe_cards.html', recipes=recipes, is_searching=is_searching)

  
@app.route('/update-recipe-order', methods=['POST'])
@login_required
def update_recipe_order():
    data = request.get_json()
    new_ids = data.get('ids', [])

    # Update each recipe with its new index
    for index, r_id in enumerate(new_ids):
        recipe = db.session.get(Recipe, int(r_id))
        if recipe and recipe.uploaded_by == current_user.user_id:
            recipe.recipe_order = index
    
    db.session.commit()
    return {"status": "success"}, 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not db.session.query(User).first():
            print("Database is empty. Seeding synthetic data...")
            create_data()
        else:
            print("Database already contains data. Skipping seed.")
    app.run(debug=True)
    
  