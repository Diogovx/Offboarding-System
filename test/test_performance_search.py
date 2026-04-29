import sys
import os
import time
import asyncio
from fastapi.concurrency import run_in_threadpool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))


from app.integrations.intouch import service
from app.services import ADService

async def verify_v1_old(registration: str):
    ad_service = ADService()
    
    ad_response = await run_in_threadpool(ad_service.search_users, registration=registration)
    intouch_data = await run_in_threadpool(service.search_user, registration=registration)
    
    return bool(ad_response), bool(intouch_data)

async def verify_v2_new(registration: str):
    ad_service = ADService()
    
    task_ad = run_in_threadpool(ad_service.search_users, registration=registration)
    task_intouch = run_in_threadpool(service.search_user, registration=registration)
    
    ad_response, intouch_data = await asyncio.gather(task_ad, task_intouch)
    
    return bool(ad_response), bool(intouch_data)

async def main():
    test_registration = "9998" 
    
    print(f"search: {test_registration}")
    print("-" * 30)

    print("Test V1 (old version - sequential)")
    start_v1 = time.perf_counter()
    await verify_v1_old(test_registration)
    end_v1 = time.perf_counter()
    time_v1 = end_v1 - start_v1
    print(f"time V1: {time_v1:.4f} seconds\n")

    print("Test V2 (new version - parallel)...")
    start_v2 = time.perf_counter()
    await verify_v2_new(test_registration)
    end_v2 = time.perf_counter()
    time_v2 = end_v2 - start_v2

    percentage = ((time_v1 - time_v2) / time_v1) * 100
    print(f"time V2: {time_v2:.4f} seconds\n")
    print("-" * 30)
    print(f"time saved: {time_v1 - time_v2:.4f} seconds per request")
    print(f"percentage of the economy: {percentage:.2f}%")

if __name__ == "__main__":
    asyncio.run(main())