import uuid
from rest_framework.decorators import api_view, action
from .serializers import ProductSerilaizer, CategorySerializer, ReviewSerializer, CartSerializer, ProductReadSerializer, CartItemSerializer, AddCartItemSerializer, UpdateCartItemSerializer, ProfileSerializer, OrderSerializer, CreateOrderSerializer
from storeapp.models import Product, Category, Review, Cart, Cartitems, Profile, Order, OrderItem
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.http import Http404, HttpResponse
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ProductFilter
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
import requests
from django.conf import settings

# Create your views here.


def initiate_payment(amount, email, order_id):
    url = "https://api.flutterwave.com/v3/payments"
    headers = {
        "Authorization": f"Bearer {settings.FLW_SEC_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "tx_ref": str(uuid.uuid4()),
        "amount": str(amount), 
        "currency": "INR",
        "redirect_url": f"http://localhost:8000/api/orders/confirm_payment/?o_id={order_id}", # formatted string literals
        "meta": {
            "consumer_id": 23,
            "consumer_mac": "92a3-912ba-1192a"
        },
        # "max_retry_attempt": 2,
        "customer": {
            "email": email,
            "phonenumber": "080****4528",
            "name": "Yemi Desola"
        },
        "customizations": {
            "title": "Easy Solution Payments",
            "logo": "https://marketplace.canva.com/EAFvDRwEHHg/1/0/1600w/canva-colorful-abstract-online-shop-free-logo-cpI8ixEpis8.jpg"
        }
    }
    

    try:
        response = requests.post(url, headers=headers, json=data)
        print('res', response)
        response_data = response.json()
        return Response(response_data)
    
    except requests.exceptions.RequestException as err:
        print("the payment didn't go through", err)
        return Response({"error": str(err)}, status=500)





class ProductViewset(ModelViewSet): # performs CRUD operations
    queryset = Product.objects.all()
    # serializer_class = ProductSerilaizer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # filterset_fields = ["category", "old_price"]
    filterset_class = ProductFilter
    search_fields = ["name", "description"]
    ordering_fields = ["old_price"] # to pass query params as ?ordering=old_price or ordering=-old_price
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.request.method in ["GET"]:
            return ProductReadSerializer
        return ProductSerilaizer

class ReviewViewset(ModelViewSet):
    # queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(product=self.kwargs["product_pk"])
    
    # get_serializer_context(self) in ModelViewSet returns a dictionary that contains additional context to be supplied to the serializer
    def get_serializer_context(self):
        return {"product": self.kwargs["product_pk"]}


class CategoryViewset(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CartViewset(CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer


class CartItemViewset(ModelViewSet):
    # queryset = Cartitems.objects.all()
    # serializer_class = CartItemSerializer
    http_method_names = ["get","post","patch","delete"]

    def get_queryset(self):
        return Cartitems.objects.filter(cart=self.kwargs["cart_pk"])
    
    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartItemSerializer
        elif self.request.method == "PATCH":
            return UpdateCartItemSerializer
        return CartItemSerializer
    
    def get_serializer_context(self):
        return {"cart_id": self.kwargs["cart_pk"]}
    

class OrderViewset(ModelViewSet):
    # queryset = Order.objects.all()
    # serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]


    # @action in DRF is used to create a custom action on a viewset. 
    # It's used when you need an endpoint that doesn't directly map to a standard CRUD operation
    @action(detail=True, methods=["POST"]) # detail=True: This means the action is for a single instance of a model
    def pay(self, request, pk):
        order = self.get_object() # get_object(): This method retrieves the object specified by the PK in the URL.
        amount = order.total_price
        email = request.user.email
        # redirect_url = "http://127.0.0.1:8000/confirm"
        return initiate_payment(amount, email, order.id)
    
    @action(detail=False, methods=["POST"])
    def confirm_payment(self, request):
        order_id  = request.GET.get("o_id")
        order = Order.objects.get(id=order_id)
        order.pending_status = "C"
        order.save()

        serializer = OrderSerializer(order)
        data = {
            "msg": "Payment was successful",
            "data": serializer.data
        }
        return Response(data)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(owner=user)
    
    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateOrderSerializer
        return OrderSerializer
    
    def get_serializer_context(self):
        return {"user_id": self.request.user.id}


class ProfileViewset(ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

# class ApiProducts(ListCreateAPIView): # Extends: GenericAPIView, ListModelMixin, CreateModelMixin
#     queryset = Product.objects.all()
#     serializer_class = ProductSerilaizer

    # def get(self,request):
    #     products = Product.objects.all()
    #     serilaizer = ProductSerilaizer(products, many=True)
    #     return Response(serilaizer.data)
    
    # def post(self, request):
    #     serilaizer = ProductSerilaizer(data=request.data)
    #     serilaizer.is_valid(raise_exception=True)
    #     serilaizer.save()
    #     return Response(serilaizer.data)
    

# class ApiProduct(RetrieveUpdateDestroyAPIView):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerilaizer

    # def get_object(self, pk):
    #     try:
    #         return Product.objects.get(id=pk)
    #     except Product.DoesNotExist:
    #         raise Response({'msg':'not found'}, status=status.HTTP_400_BAD_REQUEST)
        
    # def get(self, request, pk, format=None):
    #     product = self.get_object(pk)
    #     serializer = ProductSerilaizer(product)
    #     return Response(serializer.data)

    # def put(self, request, pk, format=None):
    #     product = self.get_object(pk)
    #     serializer = ProductSerilaizer(product, data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def delete(self, request, pk, format=None):
    #     product = self.get_object(pk)
    #     product.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)

# class ApiCategories(ListCreateAPIView):
#     queryset = Category.objects.all()
#     serializer_class = CategorySerializer

    # def get(self,request):
    #     categories = Category.objects.all()
    #     serilaizer = CategorySerializer(categories, many=True)
    #     return Response(serilaizer.data)
    
    # def post(self, request):
    #     serilaizer = CategorySerializer(data=request.data)
    #     serilaizer.is_valid(raise_exception=True)
    #     serilaizer.save()
    #     return Response(serilaizer.data)   

# class ApiCategory(RetrieveUpdateDestroyAPIView):
#     queryset = Category.objects.all()
#     serializer_class = CategorySerializer

    # def get_object(self, pk):
    #     try:
    #         return Category.objects.get(category_id=pk)
    #     except Category.DoesNotExist:
    #         return Response({'msg':'not found'}, status=status.HTTP_400_BAD_REQUEST)
        
    # def get(self, request, pk, format=None):
    #     category = self.get_object(pk)
    #     serializer = CategorySerializer(category)
    #     print("sss,", serializer.data)
    #     return Response(serializer.data)

    # def put(self, request, pk, format=None):
    #     category = self.get_object(pk)
    #     serializer = CategorySerializer(category, data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def delete(self, request, pk, format=None):
    #     category = self.get_object(pk)
    #     category.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)
    

@api_view(["GET","POST"])
def api_products(request):
    if request.method == "GET":
        products = Product.objects.all()
        serilaizer = ProductSerilaizer(products, many=True)
        return Response(serilaizer.data)
    
    if request.method == "POST":
        serilaizer = ProductSerilaizer(data=request.data)
        serilaizer.is_valid(raise_exception=True)
        serilaizer.save()
        return Response(serilaizer.data)


@api_view(["GET", "PUT", "DELETE"])
def api_product(request, uuid):

    product = get_object_or_404(Product, id=uuid) # or self.kwargs['uuid']

    if request.method == "GET":
        serializer = ProductSerilaizer(product)
        return Response(serializer.data)
    
    if request.method == "PUT":
        serializer = ProductSerilaizer(product, data=request.data)
        # if serializer.is_valid():  # this commented part of the code is ugly so below part is the effevtive way to write (raise_exception=True)
        #     serializer.save()
        #     return Response(serializer.data)
        # else:
        #     return Response(serializer.errors)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    if request.method == "DELETE":
        product.delete()
        return Response({"message":"success"})


@api_view(["GET", "POST"])
def api_categories(request):
    if request.method == "GET":
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    if request.method == "POST":
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@api_view(["GET","PUT","DELETE"])
def api_category(request, pk):

    category = get_object_or_404(Category, category_id=pk)

    if request.method == "GET":
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    if request.method == "PUT":
        serializer = CategorySerializer(category, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    if request.method == "DELETE":
        category.delete()
        return Response({"message": "success"})