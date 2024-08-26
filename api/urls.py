from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

# the below code is for viewsets
# router = DefaultRouter()
# router.register("products", views.ProductViewset)
# router.register("categories", views.CategoryViewset)

# the below code is for nested routers in modelviewset
router = routers.DefaultRouter()

router.register("products", views.ProductViewset)
router.register("categories", views.CategoryViewset)
router.register("carts", views.CartViewset)
router.register("profile", views.ProfileViewset)
router.register("orders", views.OrderViewset, basename="orders")

products_router = routers.NestedDefaultRouter(router, "products", lookup="product") # In DRF, nested router automatically appends _pk to the lookup field to prevent naming conflicts and to follow a common naming convention. (product_pk)
products_router.register("reviews", views.ReviewViewset, basename="product-reviews") # here, basename is optional

cart_router = routers.NestedDefaultRouter(router, "carts", lookup="cart")
cart_router.register("items", views.CartItemViewset, basename="cart_items")


# urlpatterns = router.urls

urlpatterns = [
    path('', include(router.urls)),
    path('', include(products_router.urls)),
    path('', include(cart_router.urls))

#     # path("products", views.ApiProducts.as_view()),
#     # path("products/<str:pk>", views.ApiProduct.as_view()), # uuid so str only
#     # path("categories", views.ApiCategories.as_view()),
#     # path("categories/<str:pk>", views.ApiCategory.as_view())
]


# nested router in modelviewset (e.g., for nested router products/1/reviews and products/1/reviews/1)
# to implement nested router in modelviewset install drf-nested-router