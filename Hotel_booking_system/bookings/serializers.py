from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Hotel, Room, Reservation
from pymongo import MongoClient


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        client = MongoClient('localhost', 27017)
        db = client['your_database_name']
        collection = db['your_collection_name']

        user = validated_data
        collection.insert_one(user)
        return user


class HotelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = ['id', 'title', 'description', 'address', 'rooms']

    rooms = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    def create(self, validated_data):
        client = MongoClient('localhost', 27017)
        db = client['hotel_booking']
        collection = db['hotels']

        hotel_data = validated_data
        inserted_hotel = collection.insert_one(hotel_data)

        # Добавляем вставленный идентификатор (_id) в данные отеля
        hotel_data['_id'] = inserted_hotel.inserted_id

        return hotel_data


class RoomSerializer(serializers.ModelSerializer):

    class Meta:
        model = Room
        fields = ['id', 'hotel', 'room_number', 'description', 'price', 'capacity', 'room_type']

    def create(self, validated_data):
        client = MongoClient('localhost', 27017)
        db = client['hotel_booking']
        collection = db['rooms']

        room_data = validated_data
        inserted_room = collection.insert_one(room_data)

        # Добавляем вставленный идентификатор (_id) в данные комнаты
        room_data['_id'] = inserted_room.inserted_id

        return room_data


class ReservationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reservation
        fields = ['id', 'user', 'hotel', 'room', 'check_in_date', 'check_out_date', 'guests']

    def create(self, validated_data):
        client = MongoClient('localhost', 27017)
        db = client['hotel_booking']
        collection = db['reservations']

        reservation_data = validated_data
        inserted_reservation = collection.insert_one(reservation_data)

        # Добавляем вставленный идентификатор (_id) в данные бронирования
        reservation_data['_id'] = inserted_reservation.inserted_id

        return reservation_data

    def get_fields(self):
        fields = super().get_fields()
        if 'hotel' in self.context['request'].data:
            hotel_id = int(self.context['request'].data['hotel'])
            # Фильтруем комнаты по отелю при сериализации
            fields['room'].queryset = Room.objects.filter(hotel_id=hotel_id)
        return fields
