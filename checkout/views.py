from django.shortcuts import render

from django.views.generic import TemplateView

class CheckoutView(TemplateView):
	template_name = 'checkout/checkout.html'
