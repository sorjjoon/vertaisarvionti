from application import create_app

if __name__ == '__main__':
    app=create_app("")
    app.run(debug=True)
#--show-capture=no --cov-report html:cov --cov=application