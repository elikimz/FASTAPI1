
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

load_dotenv()  # Load environment variables from .env

# Print out all loaded environment variables
print(os.environ)  # This will print all environment variables to check if the .env variables are there.

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

print(setting.database_hostname)
print(setting.database_port)
