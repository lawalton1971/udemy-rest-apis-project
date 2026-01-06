from flask_smorest import Blueprint, abort  
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from schemas import StoreSchema, StoreUpdateSchema
from models import StoreModel
from db import db

blp = Blueprint("stores", __name__, description="Operations on stores")

@blp.route("/store/<int:store_id>")
class Store(MethodView):
    @jwt_required()
    @blp.response(200, StoreSchema)
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store

    @jwt_required()
    def delete(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        db.session.delete(store)
        db.session.commit()
        return {"message": "Store deleted."}
    
    
    @jwt_required()
    @blp.arguments(StoreUpdateSchema)
    @blp.response(200, StoreSchema) 
    def put(self, store_data, store_id):
        store = StoreModel.query.get(store_id)
        if store:
            store.name = store_data["name"]
        else:
            store = StoreModel(id=store_id, **store_data)
        
        db.session.add(store)
        db.session.commit()
        return store

@blp.route("/store")
class StoreList(MethodView):
    @jwt_required()
    @blp.response(200, StoreSchema(many=True))
    def get(self):
        return StoreModel.query.all()   
    
    @jwt_required()
    @blp.arguments(StoreSchema)
    @blp.response(201, StoreSchema)
    def post(self, store_data):
        store = StoreModel(**store_data)
        try:
            db.session.add(store)
            db.session.commit()
        except IntegrityError:
            abort(400, message="Store with that name already exists.")
        except SQLAlchemyError:
            abort(500, message="An error occurred while creating the store.")
        return store