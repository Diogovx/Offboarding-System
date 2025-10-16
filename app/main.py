from fastapi import FastAPI
from subprocess import run, PIPE, STDOUT
import json
from .models import ADUser

app = FastAPI()

@app.get("/")
async def root():
    return { "message": "Hello World"}
    
@app.get("/user", response_model=list[ADUser])
async def get_user(username: str | None = None):
    if not username:
        command = "powershell.exe -Command \"Get-AdUser -Filter '*' -Properties SamAccountName,Name,Enabled | ConvertTo-Json -Compress\""
    else:
        command = f"powershell.exe -Command \"Get-AdUser -Filter 'Name -like ''*{username}*''' -Properties SamAccountName,Name,Enabled | ConvertTo-Json -Compress\""
    
    command_output = run(command, shell=True, stdout=PIPE, stderr=STDOUT)
    
    output_string = command_output.stdout.decode('utf-8', errors='ignore').strip()
    
    try:
        json_data = json.loads(output_string)
        
        if isinstance(json_data, dict):
            users_list = [json_data]
        elif isinstance(json_data, list):
            users_list = json_data
        else:
            users_list = []
        
        return [ADUser.model_validate(user) for user in users_list]
    except json.JSONDecodeError:
        return {"error": "The command output is not valid JSON.", "output": output_string}