from database import engine


try:
    with engine.connect():
        print("Database connection successful")

except Exception as error:
    print("Database connection failed")
    print(error)