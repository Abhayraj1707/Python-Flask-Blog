from flask import Flask, render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail
from datetime import datetime
import json
import math
import os



with open("config.json",'r') as c:
    parmas = json.load(c)["parmas"]

local_server = False
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = parmas['uplode_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=parmas['gmail-user'],
    MAIL_PASSWORD=parmas['gmail-password']
)
mail = Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] =  parmas['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = parmas['prod_uri']

db = SQLAlchemy(app)

class Contacts(db.Model):
    __tablename__ = 'contacts'
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_no = db.Column(db.String(100), nullable=False)
    msg = db.Column(db.Text(), nullable=False)
    date = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=False)

    def __init__(self, name, phone_no, msg, email, date):
        self.name = name
        self.phone_no = phone_no
        self.msg = msg
        self.date = date
        self.email = email

class Posts(db.Model):
    __tablename__ = 'posts'
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text(), nullable=False)
    date = db.Column(db.String(120), nullable=True)
    tagline = db.Column(db.String(100), nullable=False)
    img_file = db.Column(db.String(100), nullable=True)

    def __init__(self, title, slug, content, date, tagline, img_file):
        self.title = title
        self.slug = slug
        self.content = content
        self.date = date
        self.tagline = tagline
        self.img_file = img_file



@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(parmas['no_of_posts']))
    # [0:parmas['no_of_posts']]
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(parmas['no_of_posts']): (page-1)*int(parmas['no_of_posts'])+int(parmas['no_of_posts'])]
    if page == 1:
        prev = "#"
        next = "/?page="+str(page+1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', parmas=parmas,posts=posts,prev=prev,next=next)

@app.route("/post/<string:post_slug>",methods =['GET'])
def post_route(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', parmas=parmas,post=post)


@app.route("/about")
def about():
    return render_template('about.html', parmas=parmas)

@app.route("/dashboard" ,methods=['GET','POST'])
def dashboard():
    if 'user' in session and session['user'] == parmas['admin_user']:
        posts = Posts.query.all()
        return render_template('dashboard.html',parmas=parmas,posts=posts)

    if request.method=='POST':
        username= request.form.get('uname')
        userpass= request.form.get('pass')
        if (username== parmas['admin_user'] and userpass ==parmas['admin_password']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html',parmas=parmas,posts=posts)
    return render_template('login.html', parmas=parmas)


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user'] == parmas['admin_user']:
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date=datetime.now()

            if sno == '0':
                post = Posts(title=box_title, slug=slug, content=content, tagline=tline, img_file=img_file,date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/dashboard')
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html',parmas=parmas,post=post,sno=sno)


@app.route("/uploder", methods=['GET', 'POST'])
def uploder():
    if 'user' in session and session['user'] == parmas['admin_user']:
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return "Uploaded Successfully"


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    if 'user' in session and session['user'] == parmas['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if(request.method =='POST'):
        #Add enter to the database
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_no=phone, msg=message, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()
        try:
            mail.send_message('New message from ' + name,
                              sender=email,
                              recipients=[parmas['gmail-user']],
                              body=message + "\n" + phone
                              )
        except Exception as e:
            print("Invalid Credentials")
    return render_template('contact.html', parmas=parmas)


if __name__ == '__main__':
    app.run(debug = True)
