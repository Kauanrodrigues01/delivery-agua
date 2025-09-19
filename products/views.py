from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView

from cart.models import CartItem
from cart.views import get_cart

from .models import Category, Product


def add_to_cart(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    product_id = request.POST.get("product_id")
    if not product_id:
        return JsonResponse({"error": "No product id"}, status=400)

    cart = get_cart(request)
    # SEGURANÇA: Só permite adicionar produtos ativos
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()

    return JsonResponse({"success": True, "cart_count": cart.total_quantity})


class ProductListView(ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 9

    def get_queryset(self):
        queryset = (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .order_by("-created_at")
        )

        # Filtro de busca por nome
        search_query = self.request.GET.get("search", "")
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        # Filtro por categoria
        category_filter = self.request.GET.get("category", "")
        if category_filter:
            queryset = queryset.filter(category_id=category_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = get_cart(self.request)
        context["cart_count"] = cart.total_quantity if cart else 0
        context["search_query"] = self.request.GET.get("search", "")
        context["category_filter"] = self.request.GET.get("category", "")
        context["categories"] = Category.objects.all().order_by("name")
        return context

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect("dashboard:dashboard")
        return super().get(request, *args, **kwargs)


class ProductDetailView(DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"
