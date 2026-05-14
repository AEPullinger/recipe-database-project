from typing import List, Optional
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, String, Text, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

db: SQLAlchemy = SQLAlchemy(model_class=Base)

recipe_categories = db.Table(
    "Recipe_Categories",
    db.metadata,
    db.Column("rc_recipe_id", db.Integer, db.ForeignKey("Recipes.recipe_id"), primary_key=True),
    db.Column("rc_category_id", db.Integer, db.ForeignKey("Categories.category_id"), primary_key=True),
)

class User(db.Model, UserMixin):
    __tablename__ = "Users"
    
    user_id: Mapped[int] = mapped_column(primary_key=True)
    user_name: Mapped[str] = mapped_column(String(36))
    user_email: Mapped[str] = mapped_column(String(128), unique=True)
    user_password: Mapped[str] = mapped_column(String(128))

    # Relationships
    recipes: Mapped[List["Recipe"]] = relationship("Recipe", back_populates="author")

    def get_id(self):
        return str(self.user_id)

class Recipe(db.Model):
    __tablename__ = "Recipes"
    
    recipe_id: Mapped[int] = mapped_column(primary_key=True)
    recipe_name: Mapped[str] = mapped_column(String(256))
    recipe_desc: Mapped[Optional[str]] = mapped_column(Text)
    steps: Mapped[Optional[str]] = mapped_column(Text)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("Users.user_id"))
    recipe_order: Mapped[int] = mapped_column(default=0) 

    # Relationships
    author: Mapped["User"] = relationship("User", back_populates="recipes")
    categories: Mapped[List["Category"]] = relationship("Category", secondary=recipe_categories)
    ingredients: Mapped[List["RecipeQuantity"]] = relationship("RecipeQuantity", back_populates="recipe", cascade="all, delete-orphan")

class Category(db.Model):
    __tablename__ = "Categories"
    
    category_id: Mapped[int] = mapped_column(primary_key=True)
    category_name: Mapped[str] = mapped_column(String(256), unique=True)

class Ingredient(db.Model):
    __tablename__ = "Ingredients"
    
    ingredient_id: Mapped[int] = mapped_column(primary_key=True)
    ingredient_name: Mapped[str] = mapped_column(String(256), unique=True)

class Measurement(db.Model):
    __tablename__ = "Measurements"
    
    measure_id: Mapped[int] = mapped_column(primary_key=True)
    measure_type: Mapped[str] = mapped_column(String(128), unique=True)

class RecipeQuantity(db.Model):
    __tablename__ = "Recipe_Quantities"
    
    rq_id: Mapped[int] = mapped_column(primary_key=True)
    rq_recipe_id: Mapped[int] = mapped_column(ForeignKey("Recipes.recipe_id"))
    rq_ingred_id: Mapped[int] = mapped_column(ForeignKey("Ingredients.ingredient_id"))
    rq_measur_id: Mapped[int] = mapped_column(ForeignKey("Measurements.measure_id"))
    rq_quantity: Mapped[float] = mapped_column(Float)

    # Relationships
    ingredient: Mapped["Ingredient"] = relationship("Ingredient")
    measurement: Mapped["Measurement"] = relationship("Measurement")
    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="ingredients")