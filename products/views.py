from django.shortcuts import render

from django.views.generic import ListView, DetailView
from .models import Product

class ProductListView(ListView):
	model = Product
	template_name = 'products/product_list.html'
	context_object_name = 'products'
	queryset = Product.objects.filter(is_active=True)

class ProductDetailView(DetailView):
	model = Product
	template_name = 'products/product_detail.html'
	context_object_name = 'product'
