from pydantic import BaseModel, Field


class GenerateTermRequest(BaseModel):
    employee_num: str = Field(..., description="Employee registration")
    asset_tag: str = Field(..., description="Asset tag")
    template_id: int = Field(
        default=1,
        description="ID of the template to be generated"
    )


class CheckinAssetRequest(BaseModel):
    registration: str = Field(..., description="Matrícula do funcionário")
    asset_tag: str = Field(..., description="Etiqueta (Patrimônio) do equipamento")
    note: str = Field(default="Devolvido via API (Teste)", description="Nota opcional para o histórico")
