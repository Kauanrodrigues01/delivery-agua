from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.views.decorators.http import require_http_methods, require_POST
from products.models import Product
from .utils.metrics import calculate_metrics

# Login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard:dashboard')
        else:
            return render(request, 'dashboard/login.html', {'error': 'Invalid credentials'})
    return render(request, 'dashboard/login.html')

# Dashboard view
@login_required
def dashboard_view(request):
    metrics = calculate_metrics()
    return render(request, 'dashboard/dashboard.html', {'metrics': metrics})

# Product CRUD views
@login_required
def product_list(request):
    # Get filter parameter from the request
    status_filter = request.GET.get('status')

    # Filter products based on the status
    if status_filter == 'active':
        products = Product.objects.filter(is_active=True).order_by('-created_at')
    elif status_filter == 'inactive':
        products = Product.objects.filter(is_active=False).order_by('-created_at')
    else:
        products = Product.objects.all().order_by('-created_at')

    return render(request, 'dashboard/product_list.html', {'products': products, 'status_filter': status_filter})

@login_required
@require_POST
def product_create(request):
    name = request.POST.get('name')
    price = request.POST.get('price')
    image = request.FILES.get('image')
    is_active = request.POST.get('is_active') == "true"

    Product.objects.create(
        name=name,
        price=price,
        image=image,
        is_active=is_active
    )

    return redirect('dashboard:product_list')

@login_required
@require_POST
def product_edit(request, pk):
    product = Product.objects.get(pk=pk)
    product.name = request.POST['name']
    product.price = request.POST['price']
    product.image = request.FILES.get('image', product.image)
    product.save()
    return redirect('dashboard:product_list')

@login_required
@require_http_methods(["DELETE"])
def product_delete(request, pk):
    product = Product.objects.get(pk=pk)
    product.delete()
    return redirect('dashboard:product_list')

@login_required
@require_POST
def product_toggle_active(request, pk):
    product = Product.objects.get(pk=pk)
    product.is_active = not product.is_active
    product.save()
    return redirect('dashboard:product_list')