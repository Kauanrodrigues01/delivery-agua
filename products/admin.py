from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "description")
    fieldsets = (
        (None, {"fields": ("name", "description")}),
        (
            "Datas",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ("created_at",)
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_active", "created_at")
    list_filter = ("is_active", "category", "created_at")
    search_fields = ("name", "description")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "description",
                    "category",
                    "price",
                    "image",
                    "is_active",
                )
            },
        ),
        (
            "Datas",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["name"].label = "Nome"
        form.base_fields["description"].label = "Descrição"
        form.base_fields["category"].label = "Categoria"
        form.base_fields["price"].label = "Preço"
        form.base_fields["image"].label = "Imagem"
        form.base_fields["is_active"].label = "Ativo"
        return form
