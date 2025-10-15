from fastapi import FastAPI
from subprocess import run, PIPE, STDOUT
import json

app = FastAPI()

@app.get("/user")
async def root():
    user_name = 'diogo'
    command = f"powershell.exe -Command \"Get-AdUser -Filter 'Name -like ''*{user_name}*''' -Properties SamAccountName,Name,Enabled | ConvertTo-Json -Compress\""
    
    command_output = run(command, shell=True, stdout=PIPE, stderr=STDOUT)
    
    output_string = command_output.stdout.decode('utf-8', errors='ignore').strip()
    
    
    try:
        json_data = json.loads(output_string)
        return {"message": json_data}
    except json.JSONDecodeError:
        return {"error": "The command output is not valid JSON.", "output": output_string}