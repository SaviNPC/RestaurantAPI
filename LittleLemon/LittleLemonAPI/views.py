from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from .models import MenuItem, Cart, Order, OrderItem
from .serializers import *
from rest_framework import status, generics
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User, Group
from .paginations import MenuItemListPagination, OrderListPagination
from .permissions import IsManager, IsDeliveryCrew

# @api_view(['GET', 'POST'])
# def menu_items(request):
# 	if(request.method=='GET'):
# 		items = MenuItem.objects.select_related('category').all()
# 		serialized_item = MenuItemSerializer(items, many=True)
# 		return Response(serialized_item.data)
# 	elif request.method=='POST':
# 		serialized_item = MenuItemSerializer(data=request.data)
# 		serialized_item.is_valid(raise_exception=True)
# 		serialized_item.save()
# 		return Response(serialized_item.validated_data, status.HTTP_201_CREATED)

# @api_view()
# def single_item(request, id):
# 	item = get_object_or_404(MenuItem, pk=id)
# 	serialized_item = MenuItemSerializer(item)
# 	return Response(serialized_item.data) 


#Menu Items:
class MenuItemList(generics.ListCreateAPIView):
    throttling_classes = [UserRateThrottle, AnonRateThrottle]
    serializer_class = MenuItemSerializer
    queryset = MenuItem.objects.all()
    
    search_fields = ['title', 'category__title']
    ordering_fields = ['price', 'category']
    pagination_class = MenuItemListPagination
    
    def get_permissions(self):
        permission_classes = []
        if self.request.method == 'POST':
            permission_classes = [IsAuthenticated, IsAdminUser | IsManager]
        return [permission() for permission in permission_classes]


#Single items
class SingleMenuItem(generics.RetrieveUpdateDestroyAPIView):
	throttling_classes = [UserRateThrottle, AnonRateThrottle]
	serializer_class = MenuItemSerializer
	queryset = MenuItem.objects.all()

	def get_permissions(self):
		permission_classes = []
		if self.request.method != 'GET':
			permission_classes = [IsAuthenticated, IsAdminUser | IsManager]

		return [permission() for permission in permission_classes]

#User views

class ManagerView(generics.ListCreateAPIView):
	throttling_classes = [UserRateThrottle, AnonRateThrottle]
	serializer_class = UserListSerializer
	permission_classes = [IsAuthenticated, IsAdminUser | IsManager]
	queryset = User.objects.filter(groups__name='Manager')
      
	def post(self, request, *args, **kwargs):
		username = request.data['username']
		if username:
			user = get_object_or_404(User, username=username)
			manager = Group.objects.get(name='Manager')
			manager.user_set.add(user)
			return Response(data={'message':'Succesfully added to Manager group'}, status=201)

class ManagerRemove(generics.DestroyAPIView):
	throttling_classes = [UserRateThrottle, AnonRateThrottle]
	serializer_class = UserListSerializer
	permission_classes = [IsAuthenticated, IsAdminUser | IsManager]
	queryset = User.objects.filter(groups__name='Manager')

	def delete(self, request, *args, **kwargs):
		pk = self.kwargs['pk']
		user = get_object_or_404(User, pk=pk)
		managers = Group.objects.get(name='Managers')
		managers.user_set.remove(user)
		return Response(status=200, data={'message':'User removed from Managers group'})

#Delivery Crew
class DeliveryCrewListView(generics.ListCreateAPIView):
    throttling_classes = [UserRateThrottle, AnonRateThrottle]
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser | IsManager]
    queryset = User.objects.filter(groups__name='Delivery crew')

    def post(self, request, *args, **kwargs):
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            managers = Group.objects.get(name='Delivery crew')
            managers.user_set.add(user)
            return Response(status=201, data={'message':'User added to Delivery crew group'})

class DeliveryCrewRemoveView(generics.DestroyAPIView):
    throttling_classes = [UserRateThrottle, AnonRateThrottle]
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser | IsManager]
    queryset = User.objects.filter(groups__name='Delivery crew')

    def delete(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        user = get_object_or_404(User, pk=pk)
        managers = Group.objects.get(name='Delivery crew')
        managers.user_set.remove(user)
        return Response(status=200, data={'message':'User removed from Delivery crew group'})


#Cart views
class UserCartView(generics.ListCreateAPIView):
    throttling_classes = [UserRateThrottle, AnonRateThrottle]
    serializer_class = CartAddSerializer # limits what POST on api view looks like
    permission_classes = [IsAuthenticated]

    def get_queryset(self, *args, **kwargs): 
        cart = Cart.objects.filter(user=self.request.user)
        return cart

    def list(self, request):
        queryset = self.get_queryset()
        serializer = CartListSerializer(queryset, many=True)
        return Response(serializer.data)

    # handling nonuser data inputs for POST
    def post(self, request,  *args, **kwargs):
        serializer = CartAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        id = request.data['menuitem']
        quantity = request.data['quantity']
        item = get_object_or_404(MenuItem, id=id)
        price = int(quantity) * item.price
        try:
            Cart.objects.create(user=request.user, quantity=quantity, unit_price=item.price, price=price, menuitem_id=id)
            return Response(status=201, data={'message':'Item added to cart!'})
        except:
            return Response(status=409, data={'message':'Item already in cart'})

    def delete(self, request,  *args, **kwargs):
        if request.data: 
            serializer = CartRemoveSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            item = request.data['menuitem']
            cart = get_object_or_404(Cart, user=request.user, menuitem=item)
            cart.delete()
            return Response(status=200, data={'message':'Item {} removed'.format(str(item))})
        else:
            Cart.objects.filter(user=request.user).delete()
            return Response(status=201, data={'message':'All Items removed from cart'})

########## ORDER MANAGEMENT ########## 

class OrderListView(generics.ListCreateAPIView):
    throttling_classes = [UserRateThrottle, AnonRateThrottle]
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self, *args, **kwargs):
        if self.request.user.groups.filter(name='Managers').exists():
            return Order.objects.all()
        elif self.request.user.groups.filter(name='Delivery crew').exists():
            return Order.objects.filter(delivery_crew=self.request.user)
        else: 
            return Order.objects.filter(user=self.request.user)
        
    # POST view on api_view kind of doesn't matter
    def post(self, request, *args, **kwargs):
        cart = Cart.objects.filter(user=request.user)

        if len(cart) == 0: return Response(status=404, data={'message':'There are no items in cart'})

        total = 0
        order = Order.objects.create(user=request.user, status=False, total=0, date=datetime.date.today())
        for item in cart:
            total += item.price
            OrderItem.objects.create(order=order, menuitem=item.menuitem, quantity=item.quantity)
            
        order.total = total
        order.save()
        cart.delete()
            
        return Response(status=201, data={'message':'Order #{} created!'.format(order.id)})

class SingleOrderView(generics.ListAPIView):
    throttling_classes = [UserRateThrottle, AnonRateThrottle]
    serializer_class = OrderItemSerializer

    search_fields = ['menuitem__title']
    ordering_fields=['menuitem__title','menuitem__price']
    pagination_class = OrderListPagination

    def get_queryset(self, *args, **kwargs): 
        return OrderItem.objects.filter(order_id=self.kwargs['pk'])

    def get_permissions(self):
        order = Order.objects.get(pk=self.kwargs['pk'])

        permission_classes = []

        if self.request.user == order.user and self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        elif self.request.method == 'DELETE' or self.request.method == 'PUT':
            permission_classes = [IsAuthenticated, IsAdminUser | IsManager]
        elif self.request.method == 'PATCH':
            permission_classes = [IsAuthenticated, IsDeliveryCrew]

        return [permission() for permission in permission_classes]


    def patch(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs['pk'])
        order.status = not order.status
        order.save()

        return Response(status=200, data={'message' : 'Status updated from {} to {}'.format(not order.status, order.status)})

    def put(self, request, *args, **kwargs):
        serializer = OrderPutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_pk = self.kwargs['pk']
        crew_pk = request.data['delivery_crew']
        print(crew_pk)

        order = get_object_or_404(Order, order_pk)
        crew = get_object_or_404(User, crew_pk)

        order.delivery_crew = crew
        order.save()

        return Response(status=200, data={'message':'Delivery crew added to order'})

    def delete(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs['pk'])
        order.delete()

        return Response(status=200, data={'message':'Order #{} deleted'.format(order.id)})

