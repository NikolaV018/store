from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi_jwt_auth import AuthJWT
from models import User, Order
from schemas import OrderModel, OrderStatusModel
from database import Session, engine
from fastapi.encoders import jsonable_encoder

order_router = APIRouter(
    prefix="/orders"
)

Session =  Session(bind=engine)

@order_router.get('/')
async def hello(Authorize:AuthJWT=Depends()):

    """
        ## A sample hello world route
        This returns Hello world
    """

    try:
        Authorize.jwt_required()

    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid Token"
        )
    return{"message":"Hello World"}

@order_router.post('/order', status_code=status.HTTP_201_CREATED)
async def place_an_order(order:OrderModel, Authorize:AuthJWT=Depends()):

        """
            ## Placcing an Order
            This requires the following
            - quantity : integer
            - pizza_size : str
        """

        try:
            Authorize.jwt_required()

        except Exception as e:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail = "Invalid Token"
            )
        
        current_user = Authorize.get_jwt_subject()

        user = Session.query(User).filter(User.username==current_user).first()

        new_order = Order(
            pizza_size = order.pizza_size,
            quantity = order.quantity
        )

        new_order.user = user

        Session.add(new_order)

        Session.commit()


        response = {
            "pizza_size" : new_order.pizza_size,
            "quantity" : new_order.quantity,
            "id" : new_order.id,
            "order_status" : new_order.order_status
        }

        return jsonable_encoder(response)



@order_router.get('/orders')
async def list_all_orders(Authorize:AuthJWT=Depends()):
    
    """
        ## List all orders
        This lists all orders made. It can be accessed by superusers
    """
    
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Token"
        )

    current_user = Authorize.get_jwt_subject()

    user = Session.query(User).filter(User.username==current_user).first()

    if user.is_staff:
        orders = Session.query(Order).all()

        return jsonable_encoder(orders)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail="You are not a superuser"
        )

@order_router.get('/orders/{id}')
async def get_order_by_id(id:int,Authorize:AuthJWT=Depends()):
    
    """
        ## Get an order by it's ID
        This gets an order by it's ID and is only accessed by superusers
    """
    
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid Token"
        )
    
    user = Authorize.get_jwt_subject()

    current_user = Session.query(User).filter(User.username==user).first()

    if current_user.is_staff:
        order = Session.query(Order).filter(Order.id==id).first()

        return jsonable_encoder(order)
    
    raise HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "User is not alowed to carry out the request"
    )

@order_router.get('/user/orders')
async def get_user_orders(Authorize:AuthJWT=Depends()):
    
    """
        ## Get orders froma current user
        This lists the order made by the currently active user
    """    
    
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid Token"
        )
    
    user = Authorize.get_jwt_subject()

    current_user = Session.query(User).filter(User.username==user).first()

    return jsonable_encoder(current_user.orders)

@order_router.get('/user/orders/{id}/')
async def get_specific_order(id:int,Authorize:AuthJWT=Depends()):
    
    """
        ## Gets a specific order by ID
        This gives an order by ID for the currently logged in user
    """    
    
    try:
        Authorize.jwt_required()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail = "Invalid Token"
        )

    subject = Authorize.get_jwt_subject()

    current_user = Session.query(User).filter(User.username==subject).first()

    orders =  current_user.orders

    for o in orders:
        if o.id == id:
            return jsonable_encoder(o)

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
    detail = "No order with such id"
    )

@order_router.put('/order/update/{id}/')
async def update_order(id:int,order:OrderModel,Authorize:AuthJWT=Depends()):
    
    """
        ## This updates an order by ID
        This updates an order by ID for a currently logged in user, requires:
        - quantity : integer
        - pizza size : str
    """    
    
    try:
        Authorize.jwt_required()

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail= "Invalid Token"
        )

    order_to_update = Session.query(Order).filter(Order.id==id).first()

    
    order_to_update.quantity = order.quantity
    order_to_update.pizza_size = order.pizza_size

    Session.commit()

    response = {
                "id" : order_to_update.id,
                "quantity" : order_to_update.quantity,
                "pizza_siza" : order_to_update.pizza_size,
                "order_status" : order_to_update.order_status
            }
    
    return jsonable_encoder(order_to_update)


@order_router.patch('/order/update/{id}/')
async def update_order_status(id:int,
                              order:OrderStatusModel,
                              Authorize:AuthJWT=Depends()):

    """
        ## This updates the status of an order by ID
        This updates the status of an order by ID for a currently logged in user, only superusers, requires:
        - status_order : str
    """ 
    
    try:
        Authorize.jwt_required()

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail= "Invalid Token"
        )

    username = Authorize.get_jwt_subject()

    current_user = Session.query(User).filter(User.username==username).first()

    if current_user.is_staff:
        order_to_update = Session.query(Order).filter(Order.id==id).first()

        order_to_update.order_status = order.order_status

        Session.commit()

        response = {
                "id" : order_to_update.id,
                "quantity" : order_to_update.quantity,
                "pizza_siza" : order_to_update.pizza_size,
                "order_status" : order_to_update.order_status
            }

        return jsonable_encoder(response)


@order_router.delete('/order/delete/{id}/',status_code=status.HTTP_204_NO_CONTENT)
async def delete_an_order(id:int,Authorize:AuthJWT=Depends()):

    """
        ## This deletes an order of a user by ID
        This deletes an order by ID for a currently logged in user
    """ 

    try:
        Authorize.jwt_required()

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail= "Invalid Token"
        )


    order_to_delete = Session.query(Order).filter(Order.id==id).first()

    Session.delete(order_to_delete)

    Session.commit()

    return order_to_delete