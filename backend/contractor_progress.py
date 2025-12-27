"""
Contractor Progress Tracking System
Defines standard task checklists for each contractor type based on industry standards
"""

from typing import Dict, List
from enum import Enum

# Predefined task checklists for each contractor type
# These are based on standard construction/interior industry workflows

CONTRACTOR_TASK_CHECKLISTS: Dict[str, List[Dict]] = {
    "Civil": [
        {"id": "civil_1", "name": "Foundation Work", "description": "Foundation excavation and concrete work"},
        {"id": "civil_2", "name": "Plinth Beam", "description": "Plinth beam construction completed"},
        {"id": "civil_3", "name": "Column Work", "description": "RCC column construction"},
        {"id": "civil_4", "name": "Beam & Slab", "description": "Beam and slab casting completed"},
        {"id": "civil_5", "name": "Brickwork", "description": "Brick/block wall construction"},
        {"id": "civil_6", "name": "Plastering", "description": "Internal and external plastering"},
        {"id": "civil_7", "name": "Waterproofing", "description": "Waterproofing treatment applied"},
        {"id": "civil_8", "name": "Final Finishing", "description": "Final civil finishing work"}
    ],
    
    "Electrical": [
        {"id": "elec_1", "name": "Conduiting Done", "description": "Electrical conduit piping installed"},
        {"id": "elec_2", "name": "Wiring Done", "description": "Electrical wiring pulled through conduits"},
        {"id": "elec_3", "name": "DB Installation", "description": "Distribution board installed"},
        {"id": "elec_4", "name": "Switch/Socket Boxes", "description": "Switch and socket boxes fixed"},
        {"id": "elec_5", "name": "Switches Installed", "description": "Switches and sockets installed"},
        {"id": "elec_6", "name": "Lights Fixed", "description": "Light fixtures installed"},
        {"id": "elec_7", "name": "Fans Installed", "description": "Ceiling fans installed"},
        {"id": "elec_8", "name": "Testing & Commissioning", "description": "Electrical testing completed"}
    ],
    
    "Plumbing": [
        {"id": "plumb_1", "name": "Underground Piping", "description": "Underground drainage piping"},
        {"id": "plumb_2", "name": "Riser Installation", "description": "Water supply risers installed"},
        {"id": "plumb_3", "name": "Drainage Points", "description": "Floor drainage points completed"},
        {"id": "plumb_4", "name": "Water Points", "description": "Hot/cold water points installed"},
        {"id": "plumb_5", "name": "Sanitary Fixtures", "description": "WC, basin, shower fixtures installed"},
        {"id": "plumb_6", "name": "Water Tank", "description": "Overhead/underground tank installed"},
        {"id": "plumb_7", "name": "Pump Installation", "description": "Water pump installed"},
        {"id": "plumb_8", "name": "Testing & Commissioning", "description": "Plumbing testing completed"}
    ],
    
    "HVAC": [
        {"id": "hvac_1", "name": "Copper Piping Done", "description": "Refrigerant copper piping installed"},
        {"id": "hvac_2", "name": "Drain Piping", "description": "AC drain piping completed"},
        {"id": "hvac_3", "name": "Cabling Done", "description": "AC power and signal cabling"},
        {"id": "hvac_4", "name": "IDU Installed", "description": "Indoor units installed"},
        {"id": "hvac_5", "name": "ODU Installed", "description": "Outdoor units installed"},
        {"id": "hvac_6", "name": "Ducting Done", "description": "AC ducting work completed"},
        {"id": "hvac_7", "name": "Grilles & Diffusers", "description": "AC grilles and diffusers installed"},
        {"id": "hvac_8", "name": "Testing & Commissioning", "description": "HVAC testing and gas charging"}
    ],
    
    "False Ceiling": [
        {"id": "fc_1", "name": "Framework Layout", "description": "Ceiling grid layout marked"},
        {"id": "fc_2", "name": "GI Channel Fixed", "description": "GI channels and hangers installed"},
        {"id": "fc_3", "name": "Framing Done", "description": "Metal framing structure completed"},
        {"id": "fc_4", "name": "Gypsum Boards Fixed", "description": "Gypsum boards installed"},
        {"id": "fc_5", "name": "Joint Treatment", "description": "Joints taped and filled"},
        {"id": "fc_6", "name": "Cove Light Boxing", "description": "Cove light boxes completed"},
        {"id": "fc_7", "name": "Primer Applied", "description": "Ceiling primer coating done"},
        {"id": "fc_8", "name": "Final Paint", "description": "Final ceiling paint completed"}
    ],
    
    "Furniture": [
        {"id": "furn_1", "name": "Material Received", "description": "Raw materials received at site"},
        {"id": "furn_2", "name": "Carcass Work", "description": "Cabinet carcass fabrication started"},
        {"id": "furn_3", "name": "Carcass Fixed", "description": "Carcass installed at site"},
        {"id": "furn_4", "name": "Shutter Work", "description": "Shutter fabrication in progress"},
        {"id": "furn_5", "name": "Shutters Fixed", "description": "Shutters installed"},
        {"id": "furn_6", "name": "Hardware Fixed", "description": "Hinges, channels, handles installed"},
        {"id": "furn_7", "name": "Part Completed", "description": "Partial furniture work completed"},
        {"id": "furn_8", "name": "Fully Completed", "description": "All furniture work completed"}
    ],
    
    "Flooring": [
        {"id": "floor_1", "name": "Sub-floor Preparation", "description": "Floor base leveling done"},
        {"id": "floor_2", "name": "Waterproofing", "description": "Floor waterproofing applied"},
        {"id": "floor_3", "name": "Tile Adhesive", "description": "Adhesive/mortar bed prepared"},
        {"id": "floor_4", "name": "Tiles Laid", "description": "Floor tiles/marble laid"},
        {"id": "floor_5", "name": "Grouting Done", "description": "Tile grouting completed"},
        {"id": "floor_6", "name": "Skirting Fixed", "description": "Skirting tiles installed"},
        {"id": "floor_7", "name": "Polishing Done", "description": "Floor polishing completed"},
        {"id": "floor_8", "name": "Final Cleaning", "description": "Floor cleaning and handover"}
    ],
    
    "Painting": [
        {"id": "paint_1", "name": "Surface Preparation", "description": "Wall putty and sanding done"},
        {"id": "paint_2", "name": "Primer Coat", "description": "Primer applied on all surfaces"},
        {"id": "paint_3", "name": "First Coat", "description": "First paint coat applied"},
        {"id": "paint_4", "name": "Second Coat", "description": "Second paint coat applied"},
        {"id": "paint_5", "name": "Touch-up Done", "description": "Touch-up and corrections done"},
        {"id": "paint_6", "name": "Texture/Design", "description": "Special textures/designs applied"},
        {"id": "paint_7", "name": "External Paint", "description": "External wall painting done"},
        {"id": "paint_8", "name": "Final Inspection", "description": "Paint work inspection completed"}
    ],
    
    "Glass & Aluminum": [
        {"id": "glass_1", "name": "Measurements Taken", "description": "Site measurements completed"},
        {"id": "glass_2", "name": "Fabrication Done", "description": "Frame fabrication completed"},
        {"id": "glass_3", "name": "Frame Fixed", "description": "Aluminum frames installed"},
        {"id": "glass_4", "name": "Glass Fitted", "description": "Glass panels installed"},
        {"id": "glass_5", "name": "Hardware Fixed", "description": "Handles and locks installed"},
        {"id": "glass_6", "name": "Sealant Applied", "description": "Silicone sealant applied"},
        {"id": "glass_7", "name": "Cleaning Done", "description": "Glass cleaning completed"},
        {"id": "glass_8", "name": "Final Handover", "description": "Work completed and handed over"}
    ],
    
    "Landscaping": [
        {"id": "land_1", "name": "Site Clearing", "description": "Site clearing and leveling"},
        {"id": "land_2", "name": "Soil Preparation", "description": "Garden soil prepared"},
        {"id": "land_3", "name": "Hardscape Work", "description": "Pathways and paving done"},
        {"id": "land_4", "name": "Irrigation System", "description": "Drip/sprinkler system installed"},
        {"id": "land_5", "name": "Grass Laid", "description": "Lawn grass planted"},
        {"id": "land_6", "name": "Plants Planted", "description": "Trees and plants installed"},
        {"id": "land_7", "name": "Lighting Installed", "description": "Garden lighting installed"},
        {"id": "land_8", "name": "Final Handover", "description": "Landscape work completed"}
    ],
    
    "Other": [
        {"id": "other_1", "name": "Work Started", "description": "Work commenced on site"},
        {"id": "other_2", "name": "25% Complete", "description": "25% of work completed"},
        {"id": "other_3", "name": "50% Complete", "description": "50% of work completed"},
        {"id": "other_4", "name": "75% Complete", "description": "75% of work completed"},
        {"id": "other_5", "name": "Work Complete", "description": "100% work completed"},
        {"id": "other_6", "name": "Inspection Done", "description": "Work inspected"},
        {"id": "other_7", "name": "Corrections Done", "description": "Corrections completed"},
        {"id": "other_8", "name": "Final Handover", "description": "Work handed over"}
    ]
}


def get_contractor_tasks(contractor_type: str) -> List[Dict]:
    """
    Get the task checklist for a specific contractor type
    Falls back to 'Other' if type not found
    """
    # Normalize contractor type
    normalized_type = contractor_type.strip().title()
    
    # Try exact match first
    if normalized_type in CONTRACTOR_TASK_CHECKLISTS:
        return CONTRACTOR_TASK_CHECKLISTS[normalized_type]
    
    # Try partial match
    for key in CONTRACTOR_TASK_CHECKLISTS.keys():
        if key.lower() in normalized_type.lower() or normalized_type.lower() in key.lower():
            return CONTRACTOR_TASK_CHECKLISTS[key]
    
    # Default to Other
    return CONTRACTOR_TASK_CHECKLISTS["Other"]


def get_all_contractor_types() -> List[str]:
    """Get list of all defined contractor types"""
    return list(CONTRACTOR_TASK_CHECKLISTS.keys())


def calculate_progress_percentage(completed_tasks: List[str], contractor_type: str) -> int:
    """
    Calculate the progress percentage based on completed tasks
    """
    all_tasks = get_contractor_tasks(contractor_type)
    if not all_tasks:
        return 0
    
    completed_count = sum(1 for task in all_tasks if task['id'] in completed_tasks)
    return int((completed_count / len(all_tasks)) * 100)
