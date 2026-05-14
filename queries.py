import bcrypt
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import db, Recipe, Ingredient, Category, User, RecipeQuantity

### Select queries
def find_recipe_by_name(session: Session, name: str):
    stmt = select(Recipe).where(Recipe.recipe_name.ilike(f"%{name}%")).order_by(Recipe.recipe_order)
    return session.execute(stmt).scalars().all()

def find_recipe_by_ingredient(session: Session, ing_name: str):
    stmt = (
        select(Recipe)
        .join(Recipe.ingredients) 
        .join(RecipeQuantity.ingredient) 
        .where(Ingredient.ingredient_name == ing_name)
        .order_by(Recipe.recipe_order)
    )
    return session.execute(stmt).scalars().all()

def find_recipe_by_category(session: Session, cat_name: str):
    stmt = (
        select(Recipe)
        .join(Recipe.categories)
        .where(Category.category_name == cat_name)
        .order_by(Recipe.recipe_order)
    )
    return session.execute(stmt).scalars().all()

### Insert queries
def create_user(session: Session, name: str, email: str, password_raw: str):
    hashed = bcrypt.hashpw(password_raw.encode(), bcrypt.gensalt()).decode('utf-8')
    try:
        new_user = User(user_name=name, user_email=email, user_password=hashed)
        session.add(new_user)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        return False
    
def get_or_create_category(session: Session, name: str, commit: bool = False):
    stmt = select(Category).filter_by(category_name=name)
    category = session.execute(stmt).scalar_one_or_none()
    
    if not category:
        category = Category(category_name=name)
        session.add(category)
        session.flush()
    if commit:
        session.commit()
    return category

def get_or_create_ingredient(session: Session, name: str, commit: bool = False):
    stmt= select(Ingredient).filter_by(ingredient_name=name)
    ingredient = session.execute(stmt).scalar_one_or_none()
    
    if not ingredient:
        ingredient = Ingredient(ingredient_name=name)
        session.add(ingredient)
        session.flush() 
        
    if commit:
        session.commit()
            
    return ingredient
    
def create_recipe(session: Session, data: dict, user_id: int):
    try:
        new_recipe = Recipe(
            recipe_name=data['name'],
            recipe_desc=data['desc'],
            steps=data['steps'],
            uploaded_by=user_id
        )

        for cat_name in data.get('categories', []):
            cat = get_or_create_category(session, cat_name)
            new_recipe.categories.append(cat)

        for ing_data in data.get('ingredients_list', []):
            ing = get_or_create_ingredient(session, ing_data['name'])
            
            rq = RecipeQuantity(
                rq_quantity=float(ing_data['qty']),
                rq_ingred_id=ing.ingredient_id, 
                rq_measur_id=int(ing_data['meas_id'])
            )
            new_recipe.ingredients.append(rq)

        session.add(new_recipe)
        session.commit()
        return new_recipe

    except Exception as e:
        session.rollback()
        print(f"CRITICAL ERROR in create_recipe: {e}")
        return None

### Update queries
def update_password(session: Session, user_id: int, new_pass: str, old_pass: str):
    user = session.get(User, user_id)
    
    if user and bcrypt.checkpw(old_pass.encode(), user.user_password.encode()):
        user.user_password = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode('utf-8')
        session.commit()
        return True
    return False

### Delete queries
def delete_recipe(session: Session, recipe_id: int):
    try:
        recipe = session.get(Recipe, recipe_id)
        if recipe:
            session.delete(recipe)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"Error deleting: {e}")
        return False
        
### Login
def login(session, username, password_raw):
    user = session.execute(
        select(User).where(User.user_name == username)
    ).scalar_one_or_none()
    
    if user and bcrypt.checkpw(password_raw.encode(), user.user_password.encode()):
        return user
    return None

### Search
def search_recipes_unified(session: Session, user_id: int, name: str = "", ing_name: str = "", cat_list=None):
    stmt = select(Recipe).where(Recipe.uploaded_by == user_id).order_by(Recipe.recipe_order)

    if name:
        stmt = stmt.where(Recipe.recipe_name.ilike(f"%{name}%"))

    if ing_name:
        stmt = stmt.join(Recipe.ingredients).join(RecipeQuantity.ingredient).where(
            Ingredient.ingredient_name.ilike(f"%{ing_name}%")
        )

    if cat_list:
        for cat_name in cat_list:
            stmt = stmt.where(Recipe.categories.any(Category.category_name == cat_name))
        
    return session.execute(stmt).unique().scalars().all()