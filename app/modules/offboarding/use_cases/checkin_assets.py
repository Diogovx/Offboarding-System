# app/modules/offboarding/use_cases/checkin_assets.py

import base64
import logging
import httpx

from datetime import datetime
from app.integrations.snipe_it import SnipeItService
from app.modules.offboarding.schemas import GeneratedTerm

logger = logging.getLogger(__name__)


async def checkin_assets(
    *,
    registration: str,
    target_name: str,
    snipeit_service: SnipeItService,
) -> tuple[bool, list[GeneratedTerm]]:
    """Generates checkin term documents and returns assets in Snipe-IT for all user assets.

    Iterates over all assets assigned to the user, generates a checkin term
    document for each one, performs the checkin operation, and returns the
    generated documents encoded in Base64.

    Args:
        registration (str): Employee registration number used to find the user in Snipe-IT.
        target_name (str): Full name of the user being offboarded, used for filename generation.
        snipeit_service (SnipeItService): Snipe-IT service instance.

    Returns:
        tuple[bool, list[GeneratedTerm]]: A tuple where the first element indicates
            whether at least one asset was processed successfully, and the second
            is the list of generated term documents.
    """

    generated_terms: list[GeneratedTerm] = []

    try:
        assets = await snipeit_service.search_assets_by_user(registration)

        if not assets:
            return False, []

        template_id = await snipeit_service.get_template_id_by_type("checkin")
        current_date = datetime.now().strftime("%Y%m%d")
        format_name = target_name.replace(" ", "_")

        for asset in assets:
            asset_tag = asset.get("asset_tag")
            filename = f"{registration}_{format_name}_{current_date}_{asset_tag}.docx"

            try:
                term_bytes = await snipeit_service.generate_term(
                    employee_num=registration,
                    template_id=template_id,
                    asset_tag=asset_tag,
                )
                generated_terms.append(
                    GeneratedTerm(
                        filename=filename,
                        content_base64=base64.b64encode(term_bytes).decode("utf-8"),
                    )
                )
                logger.info(f"Term generated for asset {asset_tag}.")

                await snipeit_service.checkin_asset(
                    registration, asset_tag, note="Automatic Offboarding"
                )
                logger.info(f"Checkin completed for asset {asset_tag}.")

            except Exception as e:
                logger.error(f"Failed to process asset {asset_tag}: {e}")
                continue

        return len(generated_terms) > 0, generated_terms

    except ValueError as ve:
        logger.warning(f"Snipe-IT warning for {registration}: {ve}")
    except httpx.HTTPStatusError as he:
        logger.error(
            f"Snipe-IT API failure for {registration}: {he.response.text}"
        )
    except Exception as e:
        logger.error(f"Snipe-IT unexpected error for {registration}: {e}")

    return False, []
