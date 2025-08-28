from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.http import require_http_methods, require_POST
from django.db import transaction
from products.models import Product
from checkout.models import Order, OrderItem
from .utils.metrics import calculate_metrics


# Login view
def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard:dashboard")
        else:
            return render(
                request, "dashboard/login.html", {"error": "Credenciais inválidas"}
            )
    return render(request, "dashboard/login.html")


# Dashboard view
@login_required
def dashboard_view(request):
    metrics = calculate_metrics()
    return render(request, "dashboard/dashboard.html", {"metrics": metrics})


# Product CRUD views
@login_required
def product_list(request):
    # Get filter parameter from the request
    status_filter = request.GET.get("status")

    # Filter products based on the status
    if status_filter == "active":
        products = Product.objects.filter(is_active=True).order_by("-created_at")
    elif status_filter == "inactive":
        products = Product.objects.filter(is_active=False).order_by("-created_at")
    else:
        products = Product.objects.all().order_by("-created_at")

    return render(
        request,
        "dashboard/product_list.html",
        {"products": products, "status_filter": status_filter},
    )


@login_required
@require_POST
def product_create(request):
    name = request.POST.get("name")
    price = request.POST.get("price")
    image = request.FILES.get("image")
    is_active = request.POST.get("is_active") == "true"

    Product.objects.create(name=name, price=price, image=image, is_active=is_active)

    return redirect("dashboard:product_list")


@login_required
@require_POST
def product_edit(request, pk):
    product = Product.objects.get(pk=pk)
    product.name = request.POST["name"]
    product.price = request.POST["price"]
    product.image = request.FILES.get("image", product.image)
    product.save()
    return redirect("dashboard:product_list")


@login_required
@require_http_methods(["DELETE"])
def product_delete(request, pk):
    product = Product.objects.get(pk=pk)
    product.delete()
    return redirect("dashboard:product_list")


@login_required
@require_POST
def product_toggle_active(request, pk):
    product = Product.objects.get(pk=pk)
    product.is_active = not product.is_active
    product.save()
    return redirect("dashboard:product_list")


# Logout view
@login_required
def logout_view(request):
    logout(request)
    return redirect("dashboard:login")


# Order CRUD views
@login_required
def order_list(request):
    # Get filter parameter from the request
    status_filter = request.GET.get("status")

    # Filter orders based on the status
    if status_filter == "pending":
        orders = Order.objects.filter(status="pending").order_by("-created_at")
    elif status_filter == "completed":
        orders = Order.objects.filter(status="completed").order_by("-created_at")
    elif status_filter == "cancelled":
        orders = Order.objects.filter(status="cancelled").order_by("-created_at")
    else:
        orders = Order.objects.all().order_by("-created_at")

    return render(
        request,
        "dashboard/order_list.html",
        {"orders": orders, "status_filter": status_filter},
    )


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, "dashboard/order_detail.html", {"order": order})


@login_required
def order_create(request):
    if request.method == "POST":
        customer_name = request.POST.get("customer_name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        status = request.POST.get("status", "pending")

        # Get product IDs and quantities from the form
        product_ids = request.POST.getlist("product_id")
        quantities = request.POST.getlist("quantity")

        # Create order with items in a transaction
        with transaction.atomic():
            order = Order.objects.create(
                customer_name=customer_name, phone=phone, address=address, status=status
            )

            # Create order items
            for product_id, quantity in zip(product_ids, quantities):
                if product_id and quantity and int(quantity) > 0:
                    product = Product.objects.get(pk=product_id)
                    OrderItem.objects.create(
                        order=order, product=product, quantity=int(quantity)
                    )

        return redirect("dashboard:order_list")

    # GET request - show form
    products = Product.objects.filter(is_active=True)
    return render(request, "dashboard/order_create.html", {"products": products})


@login_required
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.method == "POST":
        order.customer_name = request.POST.get("customer_name")
        order.phone = request.POST.get("phone")
        order.address = request.POST.get("address")
        order.status = request.POST.get("status")

        # Get product IDs and quantities from the form
        product_ids = request.POST.getlist("product_id")
        quantities = request.POST.getlist("quantity")

        # Update order and items in a transaction
        with transaction.atomic():
            order.save()

            # Delete existing items and create new ones
            order.items.all().delete()

            # Create new order items
            for product_id, quantity in zip(product_ids, quantities):
                if product_id and quantity and int(quantity) > 0:
                    product = Product.objects.get(pk=product_id)
                    OrderItem.objects.create(
                        order=order, product=product, quantity=int(quantity)
                    )

        return redirect("dashboard:order_detail", pk=order.pk)

    # GET request - show form
    products = Product.objects.filter(is_active=True)

    # Prepare products with order information
    order_items = {item.product.id: item for item in order.items.all()}
    products_with_order_info = []
    for product in products:
        product_info = {
            "product": product,
            "is_in_order": product.id in order_items,
            "quantity": order_items[product.id].quantity
            if product.id in order_items
            else 1,
        }
        products_with_order_info.append(product_info)

    return render(
        request,
        "dashboard/order_edit.html",
        {
            "order": order,
            "products": products,
            "products_with_order_info": products_with_order_info,
        },
    )


@login_required
@require_http_methods(["POST"])
def order_cancel(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.status = "cancelled"
    order.save()
    return redirect("dashboard:order_list")


@login_required
@require_POST
def order_toggle_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    # Não permitir alterar status de pedidos cancelados
    if order.status == "cancelled":
        return redirect("dashboard:order_detail", pk=order.pk)
    
    if order.status == "pending":
        order.status = "completed"
    else:
        order.status = "pending"
    order.save()
    return redirect("dashboard:order_detail", pk=order.pk)
