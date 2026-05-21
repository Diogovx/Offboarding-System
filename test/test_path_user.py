# ==========================================
# INTEGRATION TEST: FULL IFS WORKFLOW | python -m test.test_path_user
# ==========================================

if __name__ == "__main__":
    import asyncio
    import httpx
    
    from app.core.config import settings
    from app.integrations.ifs.service import IFSService

    async def test_full_workflow():
        print("Starting full IFS integration workflow test...")
        
        if not settings.IFS_BASE_URL:
            print("ERROR: IFS_BASE_URL environment variable is missing. Test aborted.")
            return

        ifs_service = IFSService(base_url=settings.IFS_BASE_URL)
        
        async with httpx.AsyncClient() as client:
            try:
                test_registration = "1094"
                
                # --- STEP 1: Fetch PersonId ---
                print(f"Step 1: Fetching PersonId for registration '{test_registration}'...")
                person_result = await ifs_service._get_person_user_ifs(test_registration, client)
                
                if not person_result.value:
                    print(f"WARNING: No user found with registration '{test_registration}'. Test aborted.")
                    return
                
                extracted_person_id = person_result.value[0].PersonId
                print(f"SUCCESS: PersonId retrieved -> {extracted_person_id}")
                
                # --- STEP 2: Fetch User Data and ETag ---
                print(f"Step 2: Fetching user data and ETag for Identity '{extracted_person_id}'...")
                user_data = await ifs_service._get_user_ifs(extracted_person_id, client)
                
                print(f"SUCCESS: ETag captured -> {user_data.etag}")
                print(f"INFO: Current Active status -> {user_data.Active}")

                # --- STEP 3: Update Status (Deactivate) ---
                print("Step 3: Sending deactivation request (PATCH) to IFS...")
                is_success = await ifs_service._patch_user_ifs(
                    registration=extracted_person_id,
                    etag=user_data.etag,
                    active=False,
                    client=client
                )

                if is_success:
                    print("SUCCESS: User successfully deactivated in IFS.")
                else:
                    print("WARNING: Request completed, but did not return a successful status code.")
                
            except httpx.HTTPStatusError as e:
                print(f"HTTP ERROR (Status {e.response.status_code}):")
                print(f"Response details: {e.response.text}")
            except Exception as e:
                print(f"INTERNAL ERROR: {str(e)}")

    asyncio.run(test_full_workflow())