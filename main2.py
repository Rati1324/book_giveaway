from fastapi import FastAPI, status, HTTPException, Depends, Request
from src.config import Base, engine, SessionLocal
from src.schemas import UserSchema, UserLoginSchema, TokenSchema, BookSchema, Giveaway
# from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordRequestForm
from src.models import User, Genre, Book, Author, Giveaway
from sqlalchemy.orm import Session
from src.utils import (
    get_hashed_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_jwt,
    get_current_user
)
from src.jwt_bearer import JWTBearer

app = FastAPI()

Base.metadata.create_all(bind=engine)

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

@app.get("/")
def greet():
    return {"message": "hi"}

@app.get("/users")
async def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.get("/clear_users")
async def clear_users(db: Session = Depends(get_db)):
    db.query(User).delete()
    db.commit()
    return {"result": "all users deleted"}

@app.post("/users")
async def create_user(user: UserSchema, db: Session = Depends(get_db)):
    db_user = User(username=user.username, email=user.email, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/signup")
async def signup(db: Session = Depends(get_db), user_data: UserSchema = None):
    user = db.query(User).filter(or_(User.email=user_data.email, User.username=user_data.username)).first()

    if user is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(
        username=user_data.username, 
        email=user_data.email, 
        password=get_hashed_password(user_data.password)
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"result": "user successfully created"}

@app.post('/login', summary="Create access and refresh tokens for user", response_model=TokenSchema)
async def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(User).filter_by(email=user_data.email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    hashed_pass = user.password
    if not verify_password(user_data.password, hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    return {
        "access_token": create_access_token(user.username),
        "refresh_token": create_refresh_token(user.username),
    }


# @app.post("/book", dependencies=[Depends(JWTBearer())])
@app.post("/book")
async def insert_book(db: Session = Depends(get_db), dependencies = Depends(JWTBearer()), book_data: BookSchema = None):
    genre = db.query(Genre).filter_by(name=book_data.genre).first()
    if genre is None:
        genre = Genre(name=book_data.genre)
        db.add(genre)
        db.commit()
        db.refresh(genre)
        genre_id = genre.id
    else:
        book_data.genre = genre.id
    
    author = db.query(Author).filter_by(name=book_data.author).first()
    if author is None:
        author = Author(name=book_data.author)
        db.add(author)
        db.commit()
        db.refresh(author)
        author_id = author.id
    else:
        book_data.author = author.id

    decoded_token = decode_jwt(dependencies)
    current_user = db.query(User).filter_by(email=decoded_token["sub"]).first().id

    book = Book(
        title=book_data.title,
        condition=book_data.condition,
        genre_id=book_data.genre,
        author_id=book_data.author,
        for_borrow=book_data.for_borrow,
        owner_id=current_user,
        # borrower_id=book_data.borrower,
    )

    db.add(book)
    db.commit()
    db.refresh(book)
    return book

@app.post("/request_book"dependencies = Depends(JWTBearer()))
async def request_borrow(book_request: BookRequestSchema, db: Session = Depends(get_db), dependencies = Depends(JWTBearer())):
    decoded_token = decode_jwt(dependencies)

    current_user = db.query(User).filter_by(email=decoded_token["sub"]).first().id
    book_id = book_request.book_id

    giveaway = Giveaway(
        book_id=book_id,
        requester_id=current_user,
    )

    db.add(giveaway)
    return borrowings

@app.get("/borrowings")
async def get_borrowings(db: Session = Depends(get_db), dependencies = Depends(JWTBearer())):
    decoded_token = decode_jwt(dependencies)
    current_user = db.query(User).filter_by(email=decoded_token["sub"]).first().id

    # find books that the user owns that are also in the borrowings table
    borrowings = db.query(Book).filter_by(owner_id=current_user).join(Giveaway).all()
    print(borrowings)
    return borrowings

@app.get("/test")
async def get_me(dependencies = Depends(JWTBearer())):
    return {"data": dependencies}