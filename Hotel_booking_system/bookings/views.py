import pymongo
from rest_framework import viewsets, status, generics, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from pymongo import MongoClient
from bson import ObjectId

from .models import Hotel, Room, Reservation
from .serializers import HotelSerializer, RoomSerializer, ReservationSerializer, UserSerializer


class HotelViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        client = MongoClient('localhost', 27017)
        db = client['hotel_booking']
        collection = db['hotels']

        hotels = collection.find({})

        serializer = HotelSerializer(hotels, many=True)
        return Response(serializer.data)

    def create(self, request):
        if not request.user.is_superuser:
            return Response({"error": "Только суперпользователь может создавать отели."},
                            status=status.HTTP_403_FORBIDDEN)

        client = MongoClient('localhost', 27017)
        db = client['hotel_booking']
        collection = db['hotels']

        serializer = HotelSerializer(data=request.data)
        if serializer.is_valid():
            hotel_data = serializer.validated_data
            collection.insert_one(hotel_data)  # Добавляем новый отель в коллекцию
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        client = MongoClient('localhost', 27017)
        db = client['hotel_booking']
        collection = db['hotels']

        hotel = collection.find_one({"_id": ObjectId(pk)})  # Получаем отель по идентификатору

        if hotel:
            serializer = HotelSerializer(hotel)
            return Response(serializer.data)
        else:
            return Response({"error": "Отель не найден"}, status=status.HTTP_404_NOT_FOUND)

    def update(self, request, pk=None):
        client = MongoClient('localhost', 27017)
        db = client['hotel_booking']
        collection = db['hotels']

        serializer = HotelSerializer(data=request.data)
        if serializer.is_valid():
            hotel_data = serializer.validated_data
            collection.update_one({"_id": ObjectId(pk)}, {"$set": hotel_data})  # Обновляем отель
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        client = MongoClient('localhost', 27017)
        db = client['hotel_booking']
        collection = db['hotels']

        result = collection.delete_one({"_id": ObjectId(pk)})  # Удаляем отель по идентификатору
        if result.deleted_count == 1:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"error": "Отель не найден"}, status=status.HTTP_404_NOT_FOUND)


class HotelRoomListView(generics.ListAPIView):
    serializer_class = RoomSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['room_type']
    ordering_fields = ['price', 'capacity']

    def get_queryset(self):
        client = MongoClient('localhost', 27017)
        db = client['hotel_booking']
        collection = db['rooms']

        # Получаем параметры фильтрации из запроса
        room_type = self.request.query_params.get('room_type')
        capacity = self.request.query_params.get('capacity')
        ordering = self.request.query_params.get('ordering')

        # Создаем пустой словарь для формирования фильтрации
        filters = {}

        # Добавляем фильтрацию по типу комнаты, если указан
        if room_type:
            filters['room_type'] = room_type

        # Добавляем фильтрацию по емкости, если указана
        if capacity:
            filters['capacity'] = int(capacity)

        # Формируем MongoDB запрос с учетом фильтрации
        rooms = collection.find(filters)

        # Если указано сортировать по цене или емкости, добавляем сортировку
        if ordering == 'price':
            rooms = rooms.sort("price", pymongo.ASCENDING)
        elif ordering == '-price':
            rooms = rooms.sort("price", pymongo.DESCENDING)
        elif ordering == 'capacity':
            rooms = rooms.sort("capacity", pymongo.ASCENDING)
        elif ordering == '-capacity':
            rooms = rooms.sort("capacity", pymongo.DESCENDING)

        # Преобразуем результаты запроса в список для передачи в сериализатор
        queryset = list(rooms)

        return queryset


class RoomViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        if not request.user.is_superuser:
            return Response({"error": "Только суперпользователь может создавать комнаты."},
                            status=status.HTTP_403_FORBIDDEN)

        client = MongoClient('localhost', 27017)
        db = client['hotel_booking']
        collection = db['rooms']

        serializer = RoomSerializer(data=request.data)
        if serializer.is_valid():
            room_data = serializer.validated_data
            result = collection.insert_one(room_data)  # Добавляем новую комнату в коллекцию
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReservationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = ReservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        room_id = serializer.validated_data['room'].id
        check_in_date = serializer.validated_data['check_in_date']
        check_out_date = serializer.validated_data['check_out_date']

        client = MongoClient('localhost', 27017)
        db = client['hotel_booking']
        collection = db['reservations']

        # Проверяем, зарезервирована ли комната на указанные даты
        reservations = list(collection.find({
            'room_id': room_id,
            'check_out_date': {'$gt': check_in_date},
            'check_in_date': {'$lt': check_out_date},
        }))

        if reservations:
            return Response({"error": "Комната уже зарезервирована на указанные даты."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Если комната свободна, добавляем новую бронь в коллекцию
        reservation_data = serializer.validated_data
        result = collection.insert_one(reservation_data)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        client = MongoClient('localhost', 27017)
        db = client['hotel_booking']
        collection = db['reservations']

        result = collection.delete_one({"_id": ObjectId(pk)})  # Удаляем бронь по идентификатору
        if result.deleted_count == 1:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"error": "Бронь не найдена"}, status=status.HTTP_404_NOT_FOUND)


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer

# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzA4MzYwMTI3LCJpYXQiOjE3MDgzNTk4MjcsImp0aSI6Ijg3MjU4NzdiNTEyNzQwM2U4Y2Q0NzVjNDFkYjhhOTlmIiwidXNlcl9pZCI6M30.Ql6EJBYzGfHSKZfQK65gBDzeZ6KuhIxOo--HQBUJWqI