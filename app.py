from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html", var1="VANI")
    #return render_template("login.html", var1="VANI")

if __name__ == "__main__":
    app.run(debug=True)
    
