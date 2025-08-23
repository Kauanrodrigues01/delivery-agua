from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from products.models import Product

# Login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'dashboard/login.html', {'error': 'Invalid credentials'})
    return render(request, 'dashboard/login.html')

# Dashboard view
@login_required
def dashboard_view(request):
    return render(request, 'dashboard/dashboard.html')

# Product CRUD views
@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'dashboard/product_list.html', {'products': products})

@login_required
def product_create(request):
    if request.method == 'POST':
        name = request.POST['name']
        price = request.POST['price']
        Product.objects.create(name=name, price=price)
        return redirect('product_list')
    return render(request, 'dashboard/product_form.html')

@login_required
def product_edit(request, pk):
    product = Product.objects.get(pk=pk)
    if request.method == 'POST':
        product.name = request.POST['name']
        product.price = request.POST['price']
        product.save()
        return redirect('product_list')
    return render(request, 'dashboard/product_form.html', {'product': product})

@login_required
def product_delete(request, pk):
    product = Product.objects.get(pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'dashboard/product_confirm_delete.html', {'product': product})
