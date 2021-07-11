from datetime import timedelta
import re
import time
import bcrypt
from flask import Flask,redirect,render_template, request, flash
from flask.globals import session
from flask.helpers import flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref, relation

app = Flask(__name__)
app.secret_key = "Testing"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///proger.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    uname = db.Column(db.String(20))
    password = db.Column(db.String(20))
    security = db.Column(db.String(100))
    securityAnswer = db.Column(db.String(20))
    intro = db.Column(db.Text)
    tools = db.relationship('Tools', backref='User')
    projects = db.relationship('Projects', backref='User')
    # skills = db.relationship('Skills', backref = 'User')

    def __init__(self, name, uname, password, security, securityAnswer, intro = None):
        self.name = name
        self.uname = uname
        self.password = password
        self.security = security
        self.securityAnswer = securityAnswer
        self.intro = intro
        
# class Skills(db.Model):
#     __tablename__ = "skills"
#     id = db.Column(db.Integer, primary_key=True)
#     skillName = db.Column(db.String(100))
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

#     def __init__(self, skillName, user):


class Tools(db.Model):
    __tablename__ = "tools"
    id = db.Column(db.Integer, primary_key=True)
    toolName = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    projects = db.relationship('Projects', backref='Tools')

    def __init__(self, toolName, user):
        self.toolName = toolName
        self.User = user
        

class Projects(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    projectName = db.Column(db.String(50))
    domain = db.Column(db.String(50))
    status = db.Column(db.String(20))
    tools_id = db.Column(db.Integer, db.ForeignKey('tools.id'))
    description = db.Column(db.String(1500))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, projectName, user ,domain = None, status = None, tools = None, description = None):
        self.projectName = projectName        
        self.domain = domain
        self.status = status
        self.tools = tools
        self.description = description
        self.User = user
        self.Tools = tools


@app.route("/register", methods = ["POST", "GET"])
def register():

    if request.method == "POST":
        name = request.form["name"]
        uname = request.form["uname"]
        unameFound = Users.query.filter_by(uname = uname).first()
        if unameFound:
            flash("Username already exists")
            return render_template("register.html")
        else:
            pwd1 = request.form["pwd1"]
            pwd2 = request.form["pwd2"]
            if pwd1 == pwd2:
                pwd1 = bcrypt.hashpw(pwd1.encode('utf-8'), bcrypt.gensalt(rounds=15))
                sQn = request.form["sQn"]
                sQA = request.form["sQA"] 
                userBio = Users(name, uname, pwd1, sQn, sQA, 0)
                db.session.add(userBio)
                db.session.commit()
                flash("Account created successfully")
                return redirect("/")
            else:
                flash("Password doesn't match")
                return render_template("register.html")
        
    else:
        return render_template("register.html")

@app.route("/", methods = ["POST", "GET"])
def home():
    if "_flashes" in session:
        session.pop("_flashes" ,None)
    
    if request.method == "GET":
        if "uname" in session:
            usrObj = Users.query.filter_by(uname = session["uname"]).first()
            return render_template("profile.html", introO = usrObj.intro)
        return render_template("login.html")
    else:
        if "_flashes" in session:
            session.pop("_flashes" ,None)
        usrname = request.form["uname"]
        pwd = request.form["pwd"]
        foundUser = Users.query.filter_by(uname=usrname).first()
        if foundUser:
            dbPass = foundUser.password
            if bcrypt.checkpw(pwd.encode('utf-8'), dbPass):
                session["uname"] = usrname
                usrObj = Users.query.filter_by(uname = session["uname"]).first()
                return render_template("profile.html", introO = usrObj.intro)
            else:
                flash("Incorrect Password")
                return render_template("login.html")
        else:
            flash("User doesn't Exists")
            return render_template("login.html")
        
@app.route("/forgot_password", methods = ["GET", "POST"])
def forgotPassword():
    if "_flashes" in session:
        session.pop("_flashes" ,None)
    if request.method == "GET":
        return render_template("recovery.html")
    else:
        if "uname" in request.form:
            uname = request.form["uname"]
            unameFound = Users.query.filter_by(uname = uname).first()
            if unameFound:
                session["security"] = unameFound.security
                session["uname"] = unameFound.uname
                session["answer"] = unameFound.securityAnswer
                return render_template("recovery.html" ,question=unameFound.security)
            else:
                flash("Username doesn't exists")
                return render_template("recovery.html")
        elif "answer" in  request.form:
            if request.form["answer"] == session["answer"]:
                return redirect("forgot_password/reset")
            else:
                flash("Incorrect Answer")
                return render_template("recovery.html")
        
@app.route("/forgot_password/reset", methods = ["POST", "GET"])
def reset():
    if "_flashes" in session:
        session.pop("_flashes" ,None)
    if request.method == "GET":
        return render_template("newPassword.html")
    else:
        p1 = request.form["pwd1"]
        p2 = request.form["pwd2"]
        if p1 == p2:
            usrr = Users.query.filter_by(uname = session["uname"]).first()
            usrr.password = bcrypt.hashpw(p1.encode('utf-8'), bcrypt.gensalt(rounds=15))
            
            db.session.commit()
            flash("Password Changed")
            session.pop("uname", None)
            session.pop("security", None)
            session.pop("answer", None)
            session.pop("_flashes")
            return redirect("/")
        else:
            flash("Passwords don't match")
            return render_template("newPassword.html")

@app.route("/profile", methods = ["GET", "POST"])
def profile():
    if request.method == "POST":
        intro = request.form["INTRO"]
        userObj = Users.query.filter_by(uname = session["uname"]).first()
        userObj.intro = intro
        db.session.add(userObj)
        db.session.commit()
        return redirect("/")
    else:
        return render_template("profile.html", introO = None)

@app.route("/tools")
def skills():
    if request.method == "GET":
        if "uname" in session:
            userObj = Users.query.filter_by(uname = session["uname"]).first()
            listt = Tools.query.filter_by(user_id = userObj.id).all()
            repeat = []
            for x in listt:
                if x.toolName in repeat:
                    continue
                repeat.append(x.toolName)
            if "toolsToProjects" in session:
                return render_template("tools.html", toolsList = repeat, toolsToProjects = session["toolsToProjects"])
            else:
                return render_template("tools.html", toolsList = repeat)
        return render_template("login.html")

@app.route("/tools/<toolName>")
def toolsClick(toolName):
    if "uname" in session:
        print("MamaCool")
        projects = Projects.query.filter_by().all()
        print("MamaCool")
        pros = []
        for x in projects:
            if x.Tools.toolName == toolName:
                pros.append(x.projectName)
        session["toolsToProjects"] = pros
        return redirect("/tools")
    

@app.route("/toolAdd", methods = ["GET", "POST"])
def addTool():
    if request.method == "POST":
        tool = request.form["tool"]
        print(tool)
        if tool != "":
            userObj = Users.query.filter_by(uname = session["uname"]).first()
            print("Tools")
            toolAd = Tools(tool, userObj)
            
            db.session.add(toolAd)
            db.session.commit()
    return redirect("/tools")
        

@app.route("/projects", methods = ["POST", "GET"])
def projects():
    if "uname" in session:
        if request.method == "POST":
            proName = request.form["proName"]
            return render_template("projectAdd.html", project = proName)
        userObj = Users.query.filter_by(uname = session["uname"]).first()
        proList = Projects.query.filter_by(user_id = userObj.id).all()
        repeat = []
        if proList:
            for x in proList:
                if x.projectName in repeat:
                    continue
                else:
                    repeat.append(x.projectName)

            
            return render_template("projects.html", projList = repeat)
        return render_template("projects.html")
    return render_template("login.html")

@app.route("/proAdd", methods = ["GET", "POST"])
def proAdd():
    if request.method == "POST":
        if "proName" in request.form:
            projectName = request.form["proName"]
            domain = request.form["domain"]
            status = request.form["status"]
            tools = request.form["tools"]
            desc = request.form["desc"]
            userObj = Users.query.filter_by(uname = session["uname"]).first()
            tools = tools.split(",")
            #projectName, user ,domain = None, status = None, tools = None, description = None
            for x in tools:
                proAdd = Projects(projectName, userObj, domain, status, Tools(x, userObj), desc)
                db.session.add(proAdd)
            db.session.commit()
    return redirect("/projects")
            
@app.route("/proDetails/<name>")
def proDetails(name):
    project = Projects.query.filter_by(projectName = name).first()
    toOls = Projects.query.filter_by(projectName = name).all()
    proTools = []
    for x in toOls:
        proTools.append(x.Tools.toolName)
    userObj = Users.query.filter_by(uname = session["uname"]).first()
    proList = Projects.query.filter_by(user_id = userObj.id).all()
    repeat = []
    for x in proList:
        if x.projectName not in repeat:
            repeat.append(x.projectName)

    if project:
        return render_template("projects.html", projectDetails = project, projList = repeat, toolsS = proTools)

@app.route("/proDetails/projects", methods = ["GET", "POST"])
def redirec():
    if request.method == "POST":
        proName = request.form["proName"]
        return render_template("projectAdd.html", project = proName)
    return redirect("/projects")



@app.route("/coding")
def coding():
    if "uname" in session:
        return render_template("coding.html")
    return render_template("login.html")
    
@app.route("/logout")
def logout():
    if "_flashes" in session:
        session.pop("_flashes" ,None)
    session.pop("uname", None)
    session.pop("toolsToProjects", None)
    return redirect("/")



if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)