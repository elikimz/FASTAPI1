
# from pydantic_settings import BaseSettings
# from dotenv import load_dotenv

# load_dotenv()
# class Setting(BaseSettings): 
#  database_port: int 
#  database_username: str 
#  database_hostname: str 
#  database_password: str 
#  database_name: str 
#  secret_key: str 
#  algorithm: str 
#  access_token_expire_minutes: int   
#  MPESA_CONSUMER_KEY :str
#  MPESA_CONSUMER_SECRET:str
#  MPESA_SHORTCODE:str
#  MPESA_PASSKEY:str
#  CALLBACK_URL:str


    
# class Config:
#        env_file=".env"

# setting =Setting()    

# print(setting.database_hostname)
# print(setting.database_port)
# print(setting.database_password)
# print(setting.database_username)
# print(setting.CALLBACK_URL)

from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

class Setting(BaseSettings):
    database_port: int
    database_username: str
    database_hostname: str
    database_password: str
    database_name: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    MPESA_CONSUMER_KEY: str
    MPESA_CONSUMER_SECRET: str
    MPESA_SHORTCODE: str
    MPESA_PASSKEY: str
    CALLBACK_URL: str

    class Config:
        env_file = ".env"

setting = Setting()

# Debugging: Print values to check if they load
print("MPESA_CONSUMER_KEY:", setting.MPESA_CONSUMER_KEY)
print("CALLBACK_URL:", setting.CALLBACK_URL)

