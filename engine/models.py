"""
Data models and schemas for Pharmapolyscope Physicochemical Input Generator.
Maintains 100% fidelity with the frozen input_dataset.json and input_dataset.csv schemas.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class EntityType(str, Enum):
    DRUG = "drug"
    POLYMER = "polymer"


class ProvenanceCategory(str, Enum):
    EXPERIMENTAL = "EXPERIMENTAL"
    LITERATURE = "LITERATURE"
    CALCULATED = "CALCULATED"
    ESTIMATED = "ESTIMATED"
    COMPUTED_DESCRIPTOR = "COMPUTED-DESCRIPTOR"
    ASSUMED = "ASSUMED"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StructureMetadata(BaseModel):
    pubchem_cid: Optional[int] = None
    iupac_name: Optional[str] = None
    formula: Optional[str] = None
    neutral_parent: bool = True
    stereo: Optional[str] = None


class RepeatUnitMetadata(BaseModel):
    value: str
    record_version: str = "1.0"
    composition: Optional[str] = None
    formula: Optional[str] = None
    repeat_unit_mw: Optional[float] = None


class PolymerGradeMetadata(BaseModel):
    carrier: str
    grade: str
    pharmacopoeia: Optional[str] = None
    k_value: Optional[str] = None
    composition: Optional[str] = None
    dissolution_pH: Optional[float] = None


class TmData(BaseModel):
    value: float
    unit: str = "K"
    form: Optional[str] = "form I (stable at 25 C)"
    convention: Optional[str] = "DSC onset, primary source selected by Table 4-1 rule"
    all_sources: List[Union[float, str]] = Field(default_factory=list)


class TgData(BaseModel):
    value: float
    unit: str = "K"
    method_id: Optional[str] = "TG-RATIO-01"
    equation: Optional[str] = "0.70 * Tm"
    uncertainty_K: Optional[float] = 21.0
    measurement_method: Optional[str] = None
    moisture_state: Optional[str] = "dry"
    validation_reference: Optional[Union[List[float], float, str]] = None
    cross_source_K: Optional[float] = None
    cross_source_note: Optional[str] = None


class DensityData(BaseModel):
    value: Optional[float] = None
    unit: str = "g/cm3"
    state: Optional[str] = "Fedors liquid-state surrogate for crystalline field"
    molar_volume_cm3_mol: Optional[float] = None
    note: Optional[str] = None
    validation_reference: Optional[Dict[str, Any]] = None


class HspData(BaseModel):
    delta_D: float
    delta_P: float
    delta_H: float
    primary_total: Optional[float] = None
    tabulated_total: Optional[float] = None
    recomputed_total: Optional[float] = None
    method_id: str = "HSP-HVK-01"
    secondary_fedors_total: Optional[float] = None
    displacement: Optional[float] = None
    qc_note: Optional[str] = None


class R0Data(BaseModel):
    value: float = 7.5
    unit: str = "MPa^0.5"
    band: List[float] = Field(default_factory=lambda: [7.0, 8.0])
    provenance: str = "ASSUMED"


class LogPData(BaseModel):
    primary: Optional[float] = None
    primary_algorithm: str = "RDKit Crippen"
    cross_check: Optional[Dict[str, Any]] = None


class QCResult(BaseModel):
    identity_roundtrip: str = "pass"
    ranges: str = "pass"
    descriptor_crosscheck: Optional[str] = None
    hsp_primary_secondary_displacement: Optional[float] = None
    molar_volume_consistency_pct: Optional[float] = None
    borderline_flag: bool = False
    status: str = "APPROVED"
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class EntityRecord(BaseModel):
    entity_id: str
    entity_type: EntityType
    name: str
    abbreviation: Optional[str] = None
    canonical_smiles: Optional[str] = None
    repeat_unit_smiles: Optional[Union[RepeatUnitMetadata, str]] = None
    structure: Optional[StructureMetadata] = None
    grade: Optional[Union[PolymerGradeMetadata, Dict[str, Any]]] = None
    mn: Optional[Union[float, str]] = None
    mw: Optional[float] = None
    mn_note: Optional[str] = None
    tm_K: Optional[Union[TmData, float]] = None
    tg_K: Optional[Union[TgData, float]] = None
    density_g_cm3: Optional[Union[DensityData, float]] = None
    hsp_mpa_half: Optional[HspData] = None
    delta_D: Optional[float] = None
    delta_P: Optional[float] = None
    delta_H: Optional[float] = None
    R0: Optional[Union[R0Data, float, Dict[str, Any]]] = Field(default_factory=lambda: {"value": 7.5, "band": [7.0, 8.0]})
    logP: Optional[Union[LogPData, float, Dict[str, Any]]] = None
    TPSA: Optional[float] = None
    HBD: Optional[int] = None
    HBA: Optional[int] = None
    BCS_class: Optional[str] = None
    provenance: Dict[str, str] = Field(default_factory=dict)
    source: str = ""
    method: List[str] = Field(default_factory=list)
    algorithm: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    uncertainty: Dict[str, Any] = Field(default_factory=dict)
    qc: Optional[QCResult] = None
    calculation_date: str = "2026-09-01"
    software_version: str = "input-generator/1.0"



class InputDatasetStore(BaseModel):
    schema_version: str = "1.0"
    generator_version: str = "input-generator/1.0"
    generated: str = "2026-09-01"
    description: str = "Physicochemical Input Generator output store for Pharmapolyscope manual entry."
    controlled_vocabularies: Dict[str, List[str]] = Field(default_factory=dict)
    field_contract: List[Dict[str, Any]] = Field(default_factory=list)
    records: List[EntityRecord] = Field(default_factory=list)
