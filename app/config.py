
# from pydantic_settings import BaseSettings
# from dotenv import load_dotenv

# load_dotenv()

# class Setting(BaseSettings):
#     database_hostname:str
#     database_port:str
#     database_password:str
#     database_name:str
#     database_username:str
#     secret_key:str
#     algorithm:str
#     access_token_expire_minutes:int
     

#     class Config:
#        env_file=".env"

# setting =Setting()    

# print(setting.database_hostname)
# print(setting.database_port)

from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()  # Make sure the .env file is loaded

class Setting(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    class Config:
        env_file = ".env"

setting = Setting()

# Print the values to check if they are correctly loaded from the .env file
print("Database Hostname:", setting.database_hostname)  # should print dpg-cuad03dumphs73ckdr1g-a
print("Database Port:", setting.database_port)  # should print 5432
