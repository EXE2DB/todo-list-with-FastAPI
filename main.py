"""
This is the file where the core logic is running.
The previous ones were just tools and scripts that will be used here.
There is a lot to explain here so buckle up and be prepared to get confused.
"""

#I start by importing core functions from the FastAPI library (I decided to go with this one instead of flask), among other stuff.
from fastapi import FastAPI, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

#And here I import defined variables, functions and classes from the other files.
#These will mostly act as helpers.
from database import engine, get_db, Base
from models import User, Todo, TodoList
from auth import hash_password, verify_password, create_session, get_current_user

#This tells SQLAlchemy to go to models.py and build the todo.db accordingly (yk, the users, todolists and todos table).
Base.metadata.create_all(bind=engine)

#This initializes an object from the FastAPI class. It will be the main framework of our website.
app = FastAPI()
#Kinda does the same thing as the one above. We initialize the template engine and we tell it to look at the templates folder.
# (the HTML/CSS in it was AI generated, I was lazy lol).
templates = Jinja2Templates(directory="templates")

#Here we use a decorator to add functionality to the .get() method from the FastAPI class.
#In summary, we redirect users to /lists so they don't end up in / (the root of the page). This would likely leave them in a blank page.
#If the user tried to access the website by just entering the main URL and not the complete path to their lists path,
# they would be faced with a blank page. We avoid this by catching the request and returning a redirection response that sends them back to the right path.
@app.get("/")
#Also, if you wonder why we define a function instead of actually executing it. This boils down to how webservers work.
#I won't talk too much about it but if we were to execute the functions in-place, this would probably break the server
# since they only need to run code when the user needs it. So the proper manner is defining the function first and then let the server decide when to execute it
# depending on the user's needs. That was it, I hope I was able to wrap it well. Ask me in person if I confused you more than I taught you.
def index():
    return RedirectResponse("/lists")

#If the user has no profile, they will likely want to create one. Luckily for them, I made a feature for that (satire).
#This part of the code listens for a GET request to /register and tells Jinja2 to render the html code previously mentioned.
@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

#Once the user submits their registration credentials, the browser will send a POST request to the /register path. This decorator handles it in the following manner:
@app.post("/register")
#Here we tell FastAPI where to exctract the input from the 'username' and 'password' input fields defined in the templates folder.
#We also inject a dependency to forge a bridge between the browser and the existing database to store/compare the user's POST request.
def register(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    #This will check if the username the initial user tried to register with already exists in the databse.
    #It works by sending a query to the database using the query() method from SQLAlchemy and stops at the first match to omit overhead
    # because we only need one match to conclude that the username already exists in the databse.
    #If it exists, it will re-load the /register page and put a nice little 'Username taken' for clarification.
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "Username taken"})
    #If no matches were found and the validation check passes, we proceed with creating the user with the submitted credentials.
    user = User(username=username, password_hash=hash_password(password))
    #We add the user object to the database with the .add() method.
    db.add(user)
    #And finally we write the changes to disk so they are actually stored in the todo.db file.
    db.commit()
    #After adding their data to the database we redirect them to the /login page so they can login like usual.
    return RedirectResponse("/login", status_code=303)

#Now, once our user registers their account and attempts to login once redirected to /login, this is the underlying logic that will run:

#DISCLAIMER (or whatever we call it in this context)
#I will skip some parts that I have already explained previously such as POST and GET requests and them being
# methods granted by the FastAPI class.
#I will also exclude trivialities in my explanation.

#Here, we just load the html for the /login page in the user's browser.
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

#Once the user attempts to login, we will perform several checks to ensure data safety.
@app.post("/login")
#We simply collect the submitted input from the /login page here and inject the databse dependency as it is needed to compare data.
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    #We kindly ask the database to find us a username that matches what the user submitted:
    user = db.query(User).filter(User.username == username).first()
    #This will check either of two potentially failing conditions. Either the username doesn't exist in the databse or the password is wrong.
    #If either of these conditions fail, it re-loads the page with a message telling the user why.
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(request=request, name="login.html", context={"error": "Invalid credentials"})
    #Otherwise it just grants access and redirects the user to the /lists page while generating a cookie named "session".
    #We enable the httponly flag to ensure that malicous JS code can't extract the cookie. (Also useless in this case but why not)
    response = RedirectResponse("/lists", status_code=303)
    response.set_cookie("session", create_session(user.id), httponly=True)
    return response

#Self explanatory. Once the user click on the logout button, it sends them back to the /login screen and deleted the signed session cookie.
@app.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("session")
    return response

#This is the front screen of any user profile. See it as the "home page". There, users can view their lists, add and remove them at will.
@app.get("/lists", response_class=HTMLResponse)
#We fetch the all the todo lists that belong to the user. This is done very easily since we already established a relationship between both in models.py.
def dashboard(request: Request, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    #Here we just render the html code to reflect the fetched data.
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"user": user})

#This is the feature that allows user to create new todo lists.
#It works by taking the the title from as the name for the list and injects both a bridge to the database and our get_current_user function to verify the session of the user.
#So if your session is no longer valid, you can't modify the user's data.
@app.post("/lists/add")
def add_list(title: str = Form(...), db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    #We create a new object from the TodoList class in models.py with the title and the id of the user to establish ownership.
    new_list = TodoList(title=title, user_id=user_id)
    db.add(new_list)
    db.commit()
    return RedirectResponse("/lists", status_code=303)

#Kind of the same as the one above. Just for when you want to delete a list instead of adding a new one.
#I believe you can figure out this one on your own, teach.
@app.post("/lists/{list_id}/delete")
def delete_list(list_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    #Makes sure that the todo list belongs to the user.
    todo_list = db.query(TodoList).filter(TodoList.id == list_id, TodoList.user_id == user_id).first()
    if todo_list:
        db.delete(todo_list)
        db.commit()
    return RedirectResponse("/lists", status_code=303)

#When the user tries to click on a specific list to access its contents. We make more or less the same checks as above before doing so.
@app.get("/lists/{list_id}", response_class=HTMLResponse)
def view_list(list_id: int, request: Request, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    todo_list = db.query(TodoList).filter(TodoList.id == list_id, TodoList.user_id == user_id).first()
    #If for some reason the todo_list doesn't exist or belong to the user, we raise a typical error 404.
    if not todo_list:
        #Website crashes here.
        raise HTTPException(status_code=404)
    #Otherwise we load the page like usual.
    return templates.TemplateResponse(request=request, name="todos.html", context={"list": todo_list})

#This is for when the user wants to add a task to their todo list.
#The underlying code speaks for itself, but I can make some redudant comments for that sweet, sweet grade (that you will DEFINTITELY give me).
@app.post("/lists/{list_id}/add")
def add_todo(list_id: int, text: str = Form(...), db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    #This might be the trickiest part. It only checks that the todo list belongs to the user before adding the task to it or else it throws an exception.
    todo_list = db.query(TodoList).filter(TodoList.id == list_id, TodoList.user_id == user_id).first()
    if not todo_list: raise HTTPException(status_code=403)
    todo = Todo(text=text, list_id=list_id)
    db.add(todo)
    db.commit()
    return RedirectResponse(f"/lists/{list_id}", status_code=303)

#Identical to the one above, just with the toggling feature on the tasks.
@app.post("/todos/{todo_id}/toggle")
def toggle_todo(todo_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    todo = db.query(Todo).join(TodoList).filter(Todo.id == todo_id, TodoList.user_id == user_id).first()
    #If for some reaason the todo is nowhere to be found while trying to change its state, the website crashes.
    #You can try this by manually removing the task from the todo.db file using sqlite3. It does indeed crash the website.
    if not todo: raise HTTPException(status_code=404)
    #This just flips its state. So when it is true, it becomes NOT true (false) and vice-versa.
    todo.done = not todo.done
    db.commit()
    return RedirectResponse(f"/lists/{todo.list_id}", status_code=303)

#Exactly the same as above but for deleting tasks. It's the same pattern.
@app.post("/todos/{todo_id}/delete")
def delete_todo(todo_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    todo = db.query(Todo).join(TodoList).filter(Todo.id == todo_id, TodoList.user_id == user_id).first()
    if not todo: raise HTTPException(status_code=404)
    list_id = todo.list_id
    db.delete(todo)
    db.commit()
    return RedirectResponse(f"/lists/{list_id}", status_code=303)