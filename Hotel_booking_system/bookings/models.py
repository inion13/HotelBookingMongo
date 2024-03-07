from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('localhost', 27017)
db = client['hotel_booking']


class Hotel:
    @staticmethod
    def create(title, description, address):
        hotels_collection = db['hotels']
        return hotels_collection.insert_one({
            'title': title,
            'description': description,
            'address': address
        })

    @staticmethod
    def get_by_id(hotel_id):
        hotels_collection = db['hotels']
        return hotels_collection.find_one({'_id': ObjectId(hotel_id)})

    # Другие методы для работы с отелями


class Room:
    @staticmethod
    def create(hotel_id, room_number, description, price, capacity, room_type):
        rooms_collection = db['rooms']
        return rooms_collection.insert_one({
            'hotel_id': ObjectId(hotel_id),
            'room_number': room_number,
            'description': description,
            'price': price,
            'capacity': capacity,
            'room_type': room_type
        })

    @staticmethod
    def get_by_id(room_id):
        rooms_collection = db['rooms']
        return rooms_collection.find_one({'_id': ObjectId(room_id)})

    # Другие методы для работы с комнатами


class Reservation:
    @staticmethod
    def create(user_id, hotel_id, room_id, check_in_date, check_out_date, guests):
        reservations_collection = db['reservations']
        return reservations_collection.insert_one({
            'user_id': ObjectId(user_id),
            'hotel_id': ObjectId(hotel_id),
            'room_id': ObjectId(room_id),
            'check_in_date': check_in_date,
            'check_out_date': check_out_date,
            'guests': guests
        })

    # Другие методы для работы с бронированиями
