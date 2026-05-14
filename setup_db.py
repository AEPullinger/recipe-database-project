import bcrypt
import os
from models import db, User, Recipe, Ingredient, Measurement, Category, RecipeQuantity, recipe_categories
from sqlalchemy import create_engine, insert
from sqlalchemy.orm import Session

engine = create_engine("sqlite:///instance/recipe_tin.db")

def create_data(session=None):
    if session is None:
        context_session = Session(engine)
    else:
        context_session = session

    salt = bcrypt.gensalt()
    
    ### Synthetic data
    # Create synthetic user data
    passwords_raw = [b'123', b'456', b'789', b'pass', b'word', b'potato', b'#p9ssw0rd', b'_44_', b'(its1999)', b'ima*']
    user_raw = [
        ('Jeff', 'jeff@gmail.com'), ('Reynard', 'rey@gmail.com'), ('Mila', 'mila@live.com'),
        ('Leia', 'leia@live.com'), ('User', 'user@email.com'), ('Tater', 'tot@tater.com'),
        ('L33t', 'gamer@cod.com'), ('Toothy', 'buck@teeth.com'), ('Nost', 'algia@critic.com'),
        ('imsocool', 'coolest@internet.com')
    ]

    # Create synthetic recipe data
    recipe_raw = [ 
        ("Pizza", "Cheesy", "1.) Get dough. 2.) Add cheese. 3.) Bake", 1),
        ("Ice Cream", "Creamy", "1.) Get cream. 2.) Add sugar. 3.) Freeze", 4),
        ("Sandwich", "", "1.) Make sandwich", 2),
        ("Candy", "Sweet!", "", 3),
        ("French Fries", "Crunchy", "1. Cut potatoes 2. Fry", 6),
        ("Hamburger", "I love this recipe!", "1. Make burger 2. Add cheese 3. Add toppings 4. Add bun", 5),
        ("Yogurt", "easy to make i think", "1. Add yogurt to milk 2. wait", 7),
        ("Salad", "Healthy!", "1. Mix veggies together 2. Add dressing", 8),
        ("Cereal", "Breakfast time", "1. Pour cereal. 2. Add milk.", 9),
        ("Nachos", "Yum!", "Make chips and add cheese...", 10)
    ]

    # Create synthetic measurement, ingredient, and category data.
    measure_raw = ['Tblspn(s)', 'Tspn(s)', 'Cup(s)', 'Count', 'Handful(s)', 'Slice(s)', 'Gallon(s)', 'Quart(s)', 'Percent', 'Or More', 'lbs', 'leaf']
    ingredient_raw = ['Tomato', 'Cheese', 'Dough', 'Cream', 'Sugar', 'Ice', 'Bread', 'Ham', 'Flavoring', 'Potato', 'Oil', 'Ground Beef', 'Bun', 'Lettuce', 'Milk', 'Yogurt', 'Dressing', 'Cereal', 'Chips']
    category_raw = ['Default', 'Dinner', 'Dessert', 'Lunch', 'Breakfast', 'Snack', 'Second Breakfast', 'Brunch', 'Cake', 'Puddings']
    
    # Create synthetic join data.
    rq_raw = [(1, 1, 4, 1), (1, 2, 5, 3), (1, 3, 4, 1), (2, 4, 3, 4), (2, 5, 3, 2), (2, 6, 3, 1), (3, 2, 6, 2), (3, 7, 6, 2), (3, 8, 6, 2), (4, 5, 3, 2), (4, 9, 1, 1), (5, 10, 10, 4), (5, 11, 7, 1), (6, 12, 11, 1), (6, 13, 4, 2), (6, 1, 6, 1), (6, 2, 6, 1), (6, 14, 12, 1), (7, 15, 3, 2), (7, 16, 3, 0.5), (8, 1, 4, 1), (8, 14, 4, 1), (8, 17, 3, 1), (9, 15, 3, 1), (9, 18, 3, 1), (10, 2, 5, 1), (10, 19, 5, 1)]
    rc_raw = [(1, 2), (1, 1), (1, 4), (2, 3), (2, 1), (3, 1), (3, 2), (4, 1), (4, 3), (5, 1), (5, 2), (5, 4), (6, 1), (6, 4), (7, 1), (7, 3), (8, 1), (8, 2), (9, 1), (9, 5), (10, 1), (10, 4)]

    try:
        # Add Users
        for i, (name, email) in enumerate(user_raw):
            hashed = bcrypt.hashpw(passwords_raw[i], salt).decode('utf-8')
            context_session.add(User(user_name=name, user_email=email, user_password=hashed))

        # Add Recipes
        for name, desc, steps, owner in recipe_raw:
            context_session.add(Recipe(recipe_name=name, recipe_desc=desc, steps=steps, uploaded_by=owner))

        # Add Ingredients, Measurements, and Categories
        for name in ingredient_raw: context_session.add(Ingredient(ingredient_name=name))
        for name in measure_raw: context_session.add(Measurement(measure_type=name))
        for name in category_raw: context_session.add(Category(category_name=name))
        
        context_session.flush() 

        # Add Join Table Data for Ingredients
        for r_id, i_id, m_id, qty in rq_raw:
            context_session.add(RecipeQuantity(rq_recipe_id=r_id, rq_ingred_id=i_id, rq_measur_id=m_id, rq_quantity=qty))

        # Add Join Table Data for Categories
        if rc_raw:
            context_session.execute(
                insert(recipe_categories),
                [{"rc_recipe_id": r_id, "rc_category_id": c_id} for r_id, c_id in rc_raw]
            )

        context_session.commit()
        print("Database seeded successfully!")

    except Exception as e:
        context_session.rollback()
        print(f"Error during seeding: {e}")
    finally:
        if session is None:
            context_session.close()

if __name__ == "__main__":
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    db.metadata.create_all(engine)
    
    print("Tables created successfully. Starting seed...")
    create_data()