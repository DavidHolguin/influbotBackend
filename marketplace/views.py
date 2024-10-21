from rest_framework import serializers  # Asegúrate de importar serializers
from rest_framework import viewsets
from .models import Company, Category, Product, Order, OrderItem, BusinessHours, CompanyCategory, Country, TopBurgerSection, TopBurgerItem
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from .serializers import OrderSerializer, OrderItemSerializer, CompanyCategorySerializer, CountrySerializer, \
    OrderItem, CompanySerializer, CategorySerializer, ProductSerializer, TopBurgerSectionSerializer, TopBurgerItemSerializer
from django.conf import settings
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
import logging

class CompanyCategoryViewSet(viewsets.ModelViewSet):
    queryset = CompanyCategory.objects.all()
    serializer_class = CompanyCategorySerializer
    permission_classes = [AllowAny]

class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'])
    def available_countries(self, request):
        """
        Endpoint para obtener la lista de países disponibles con sus banderas
        """
        countries = [
            {
                'code': code,
                'name': name.split(maxsplit=1)[1],  # Removemos el emoji del nombre
                'flag_emoji': name.split()[0]  # Obtenemos solo el emoji
            }
            for code, name in Country.COUNTRY_CHOICES
        ]
        return Response(countries)

    def create(self, request, *args, **kwargs):
        # Validar que el código del país esté en las opciones disponibles
        code = request.data.get('code')
        if code not in dict(Country.COUNTRY_CHOICES):
            return Response(
                {'error': 'El código del país no es válido. Debe ser uno de los países disponibles.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = serializer.save()

        # Crear el horario de atención
        business_hours_data = request.data.get('business_hours', {})
        BusinessHours.objects.create(
            company=company,
            open_days=business_hours_data.get('open_days', []),
            open_time=business_hours_data.get('open_time'),
            close_time=business_hours_data.get('close_time')
        )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Actualizar el horario de atención
        business_hours_data = request.data.get('business_hours', {})
        business_hours, created = BusinessHours.objects.get_or_create(company=instance)
        business_hours.open_days = business_hours_data.get('open_days', business_hours.open_days)
        business_hours.open_time = business_hours_data.get('open_time', business_hours.open_time)
        business_hours.close_time = business_hours_data.get('close_time', business_hours.close_time)
        business_hours.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Incluir los datos de horario de atención en la respuesta
        try:
            business_hours = instance.business_hours
            data['business_hours'] = {
                'open_days': business_hours.open_days,
                'open_time': business_hours.open_time,
                'close_time': business_hours.close_time
            }
        except BusinessHours.DoesNotExist:
            data['business_hours'] = None

        return Response(data)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class SearchView(APIView):
    def get(self, request):
        query = request.query_params.get('q', '')
        companies = Company.objects.filter(name__icontains=query)
        products = Product.objects.filter(name__icontains=query)
        categories = Category.objects.filter(name__icontains=query)

        company_serializer = CompanySerializer(companies, many=True, context={'request': request})
        product_serializer = ProductSerializer(products, many=True, context={'request': request})
        category_serializer = CategorySerializer(categories, many=True)

        results = (
            company_serializer.data +
            product_serializer.data +
            category_serializer.data
        )

        return Response(results)
    
class LoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Verificar si el usuario está autenticado mediante el token
        if request.user.is_authenticated:
            return Response({
                'user_id': request.user.id,
                'username': request.user.username,
                'email': request.user.email
            })
        return Response(
            {'error': 'Usuario no autenticado'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Por favor proporcione usuario y contraseña'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user = authenticate(username=username, password=password)
        
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            })
            
        return Response(
            {'error': 'Credenciales inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    def put(self, request):
        # Actualizar datos del usuario
        if request.user.is_authenticated:
            user = request.user
            username = request.data.get('username')
            email = request.data.get('email')
            
            if username:
                user.username = username
            if email:
                user.email = email
                
            try:
                user.save()
                return Response({
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email
                })
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        return Response(
            {'error': 'Usuario no autenticado'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    def delete(self, request):
        # Eliminar usuario
        if request.user.is_authenticated:
            try:
                request.user.delete()
                return Response(
                    {'message': 'Usuario eliminado correctamente'},
                    status=status.HTTP_204_NO_CONTENT
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        return Response(
            {'error': 'Usuario no autenticado'},
            status=status.HTTP_401_UNAUTHORIZED
        )

class RegisterView(APIView):
    permission_classes = [AllowAny]  # Asegúrate de que esta línea esté presente
 
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        if User.objects.filter(username=username).exists():
            return Response({'error': 'El nombre de usuario ya existe'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=username, email=email, password=password)
        return Response({'message': 'Usuario creado exitosamente'}, status=status.HTTP_201_CREATED)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request):
        data = request.data
        user = request.user
        company_id = data.get('company')
        items = data.get('items', [])

        if not company_id or not items:
            return Response({"error": "Datos de pedido incompletos"}, status=status.HTTP_400_BAD_REQUEST)

        total = sum(item['price'] * item['quantity'] for item in items)
        order = Order.objects.create(user=user, company_id=company_id, total=total)

        for item in items:
            OrderItem.objects.create(
                order=order,
                product_id=item['product'],
                quantity=item['quantity'],
                price=item['price']
            )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(user=user)

logger = logging.getLogger(__name__)

class TopBurgerSectionView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Obtener todas las secciones ordenadas por posición
            sections = TopBurgerSection.objects.all()
            
            serializer = TopBurgerSectionSerializer(
                sections, 
                many=True,
                context={'request': request}
            )
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error in TopBurgerSectionView: {str(e)}")
            return Response({
                "error": str(e)
            }, status=500)

class TopBurgerItemSerializer(serializers.ModelSerializer):
    company_name = serializers.SerializerMethodField()
    company_logo = serializers.SerializerMethodField()
    company_profile_url = serializers.SerializerMethodField()
    featured_image = serializers.SerializerMethodField()

    class Meta:
        model = TopBurgerItem
        fields = [
            'company_name',
            'company_logo',
            'company_profile_url',
            'featured_image',
            'order',
            'item_type',  # Añadimos el campo item_type aquí
            'custom_url'  # También incluimos custom_url para elementos de tipo banner
        ]

    def get_company_name(self, obj):
        return obj.company.name if obj.company else ""

    def get_company_logo(self, obj):
        if obj.company and obj.company.profile_picture:
            return self.context['request'].build_absolute_uri(obj.company.profile_picture.url)
        return ""

    def get_company_profile_url(self, obj):
        if obj.company:
            return f"/company/{obj.company.id}"
        return ""

    def get_featured_image(self, obj):
        if obj.featured_image:
            return self.context['request'].build_absolute_uri(obj.featured_image.url)
        return ""
    
class TopBurgerSectionSerializer(serializers.ModelSerializer):
    items = TopBurgerItemSerializer(many=True, read_only=True)

    class Meta:
        model = TopBurgerSection
        fields = ['title', 'location', 'items']

    def to_representation(self, instance):
        # Asegurarnos de que items sea una lista vacía si no hay items
        representation = super().to_representation(instance)
        if not representation.get('items'):
            representation['items'] = []
        return representation