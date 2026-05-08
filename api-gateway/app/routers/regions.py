from fastapi import APIRouter
from app.schemas.openapi import RegionResponse

router = APIRouter(prefix="/api/v1/regions", tags=["Regions"])

REGIONS = [
    RegionResponse(id="indian", name="Indian", description="Indian cuisine"),
    RegionResponse(id="south-asian", name="South Asian", description="South Asian cuisine including Pakistani, Bangladeshi, Sri Lankan"),
    RegionResponse(id="mexican", name="Mexican", description="Mexican and Latin American cuisine"),
    RegionResponse(id="italian", name="Italian", description="Italian and Mediterranean cuisine"),
    RegionResponse(id="east-asian", name="East Asian", description="East Asian cuisine including Chinese, Japanese, Korean"),
    RegionResponse(id="mediterranean", name="Mediterranean", description="Mediterranean and Middle Eastern cuisine"),
    RegionResponse(id="global", name="Global", description="International and fusion cuisine"),
]


@router.get("", response_model=list[RegionResponse])
async def list_regions():
    return REGIONS
