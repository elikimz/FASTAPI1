
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
     

    
# class Config:
#        env_file=".env"

# setting =Setting()    

# print(setting.database_hostname)
# print(setting.database_port)
# print(setting.database_password)
# print(setting.database_username)



from pydantic import BaseSettings
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class Setting(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    class Config:
        env_file = ".env"  # this tells pydantic to look for the .env file

setting = Setting()  # Instantiate the settings

