# Generated by Django 5.2.1 on 2025-06-13 07:47

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0006_remove_sharedrecipe_meal_photo"),
    ]

    operations = [
        migrations.CreateModel(
            name="Recipe",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("ingredients", models.JSONField()),
                ("instructions", models.JSONField()),
                ("tags", models.JSONField(blank=True, null=True)),
                (
                    "image",
                    models.ImageField(blank=True, null=True, upload_to="recipes/"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AlterModelOptions(
            name="savedrecipe",
            options={"ordering": ["-saved_at"]},
        ),
        migrations.AlterModelOptions(
            name="sharedrecipe",
            options={"ordering": ["-shared_at"]},
        ),
        migrations.RenameField(
            model_name="savedrecipe",
            old_name="created_at",
            new_name="saved_at",
        ),
        migrations.RemoveField(
            model_name="sharedrecipe",
            name="original",
        ),
        migrations.AddField(
            model_name="sharedrecipe",
            name="user_photo",
            field=models.ImageField(blank=True, null=True, upload_to="shared_photos/"),
        ),
        migrations.AlterField(
            model_name="savedrecipe",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="saved_recipes",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="sharedrecipe",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="shared_recipes",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="sharedrecipe",
            name="user_comment",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="GeneratedRecipe",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("ingredients", models.JSONField()),
                ("instructions", models.JSONField()),
                ("tags", models.JSONField(blank=True, null=True)),
                ("image_url", models.URLField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="generated_recipes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddField(
            model_name="savedrecipe",
            name="recipe",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="saved_by_users",
                to="recipes.recipe",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="sharedrecipe",
            name="recipe",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="shared_versions",
                to="recipes.recipe",
            ),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name="savedrecipe",
            unique_together={("user", "recipe")},
        ),
        migrations.CreateModel(
            name="RecipeRating",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "rating",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(5),
                        ]
                    ),
                ),
                (
                    "recipe",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ratings",
                        to="recipes.sharedrecipe",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("user", "recipe")},
            },
        ),
        migrations.DeleteModel(
            name="RecipeVote",
        ),
        migrations.RemoveField(
            model_name="savedrecipe",
            name="hash",
        ),
        migrations.RemoveField(
            model_name="savedrecipe",
            name="image",
        ),
        migrations.RemoveField(
            model_name="savedrecipe",
            name="ingredients",
        ),
        migrations.RemoveField(
            model_name="savedrecipe",
            name="instructions",
        ),
        migrations.RemoveField(
            model_name="savedrecipe",
            name="tags",
        ),
        migrations.RemoveField(
            model_name="savedrecipe",
            name="title",
        ),
    ]
