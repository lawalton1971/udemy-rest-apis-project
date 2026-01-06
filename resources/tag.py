from flask_smorest import Blueprint, abort  
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError

from schemas import TagSchema, TagAndItemSchema
from models import TagModel, StoreModel, ItemModel
from db import db

blp = Blueprint("Tags", "tags", description="Operations on tags")

@blp.route("/store/<int:store_id>/tag")
class TagsInstore(MethodView):
    @jwt_required()
    @blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store.tags.all()
    
    @jwt_required()
    @blp.arguments(TagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        if TagModel.query.filter(
            TagModel.store_id == store_id, TagModel.name == tag_data["name"]
        ).first():
            abort(400, message="A tag with that name already exists in that store.")    
        tag = TagModel(store_id=store_id, **tag_data)
        try:
            db.session.add(tag)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while creating the tag.")
        return tag
    
@blp.route("/item/<int:item_id>/tag/<int:tag_id>")
class LinkTagsToItem(MethodView):   
    @jwt_required()
    @blp.response(200, TagAndItemSchema)
    def post(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)
        
        if tag in item.tags:
            abort(400, message="Tag is already linked to item.")
        
        item.tags.append(tag)
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while linking the tag to the item.")
        return {"message": "Tag linked to item.", "item": item, "tag": tag}
    
    @jwt_required()
    @blp.response(200, TagAndItemSchema)
    def delete(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)
        
        if tag not in item.tags:
            abort(400, message="Tag is not linked to item.")
        
        item.tags.remove(tag)
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while unlinking the tag from the item.")
        return {"message": "Tag unlinked from item.", "item": item, "tag": tag}
    
@blp.route("/tag/<int:tag_id>")
class Tag(MethodView):
    @jwt_required()
    @blp.response(200, TagSchema)
    def get(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        return tag

    @jwt_required()
    @blp.response(
        202,
        description="Deletes a tag if no item is tagged with it.",
        example={"message": "Tag deleted."},
        )
    @blp.alt_response(404, description="Tag not found.")
    @blp.alt_response(400, description="Tag is assigned to one or more items. Cannot delete.")
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        if not tag.items:
            db.session.delete(tag)
            db.session.commit()
            return {"message": "Tag deleted."}
        abort(400, message="Tag is assigned to one or more items. Cannot delete.")

@blp.route("/tag")
class TagList(MethodView):
    @jwt_required()
    @blp.response(200, TagSchema(many=True))
    def get(self):
        tags = TagModel.query.all()
        return tags