from django.urls import path, include
from . import views

urlpatterns = [
    path('menu-items/', views.MenuItemList, name="menu-items"),
    path('menu-items/<int:pk>', views.SingleMenuItem, name="single item"),

    path('groups/managers/users', views.ManagerView.as_view(), name="manager-list"),
    path('groups/managers/users/<int:pk>/', views.ManagerRemove.as_view(), name="manager-remove"),
    path('groups/delivery-crew/users', views.DeliveryCrewListView.as_view(), name="delivery-crew-list"),
    path('groups/delivery-crew/users/<int:pk>/', views.DeliveryCrewRemoveView.as_view(), name="delivery-crew-remove"),

    path('cart/menu-items/', views.UserCartView.as_view(), name="cart"),

    path('orders/', views.OrderListView.as_view(), name="orders"),
    path('orders/<int:pk>/', views.SingleOrderView.as_view(), name="single-order"),
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
]
