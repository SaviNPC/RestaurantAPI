from rest_framework import serializers
from .models import MenuItem, Category, Cart, Order, OrderItem
from django.contrib.auth.models import User

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta():
        model = MenuItem
        fields = ['id','title','price','featured','category']
        depth = 1

class UserListSerializer(serializers.ModelSerializer):
    class Meta():
        model = User
        fields = ['id','username','email']


# Cart Serializers
class CartHelpSerializer(serializers.ModelSerializer):
    class Meta():
        model = MenuItem
        fields = ['id','title','price']

class CartListSerializer(serializers.ModelSerializer):
    menuitem = CartHelpSerializer() # allows for secondary serialization, without showing all details like "featured"
    class Meta():
        model = Cart
        fields = ['menuitem', 'quantity', 'price']

class CartAddSerializer(serializers.ModelSerializer):
    class Meta():
        model = Cart
        fields = ['menuitem', 'quantity']
        extra_kwargs = {
            'quantity': {'min_value': 1},
        }

class CartRemoveSerializer(serializers.ModelSerializer):
    class Meta():
        model = Cart
        fields = ['menuitem']

# Order serializers
class OrderSerializer(serializers.ModelSerializer):
    class Meta():
        model = Order
        fields = ['user', 'delivery_crew', 'status', 'total', 'date']

class OrderHelpserializer(serializers.ModelSerializer):
    class Meta():
        model = MenuItem
        fields = ['title','price','category']

class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = OrderHelpserializer()
    class Meta():
        model = OrderItem
        fields = ['menuitem','quantity']

class OrderPutSerializer(serializers.ModelSerializer):
    class Meta():
        model = Order
        fields = ['delivery_crew']