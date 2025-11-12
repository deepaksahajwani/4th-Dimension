# Drawing Templates for Sequential Workflow
# Each category has a predefined list of drawings in order

DRAWING_TEMPLATES = {
    "Architecture": [
        "LAYOUT PLAN GROUND FLOOR",
        "LAYOUT PLAN 1ST FLOOR",
        "LAYOUT PLAN 2ND FLOOR",
        "LAYOUT PLAN 3RD FLOOR",
        "TERRACE LAYOUT",
        "OVERHEAD TANK DETAIL",
        "SOAK PIT AND SEPTIC TANK DETAIL",
        "ELEVATION NORTH SIDE",
        "ELEVATION EAST SIDE",
        "ELEVATION SOUTH SIDE",
        "ELEVATION WEST SIDE",
        "3D OF BUILDING",
        "FOUNDATION DRAWING",
        "GROUND AND PLINTH BEAM",
        "SEPTIC TANK AND SOAK PIT DETAIL",
        "WORKING DRAWING GROUND FLOOR",
        "LINTEL DRAWING",
        "SLAB DETAIL 1",
        "ELECTRICAL PLAN GROUND FLOOR",
        "WORKING DRAWING 1ST FLOOR",
        "LINTEL DRAWING FIRST FLOOR",
        "SLAB DETAIL 2",
        "ELECTRICAL PLAN 1ST FLOOR",
        "WORKING DRAWING 3RD FLOOR",
        "LINTEL DRAWING THIRD FLOOR",
        "SLAB DETAIL 3",
        "ELECTRICAL PLAN 2ND FLOOR",
        "WORKING DRAWING TERRACE",
        "LIFT MACHINE ROOM DETAIL",
        "OVERHEAD WATER TANK DETAIL",
        "LANDSCAPE DETAIL",
        "COMPOUND WALL DETAIL",
        "COMPOUND GATE DETAIL",
        "ELEVATION ELECTRICAL DETAIL",
        "PLUMBING AND DRAINAGE DETAIL",
        "FLOORING DETAIL INDOOR",
        "INTERNAL PLUMBING DETAIL WITH ELEVATIONS",
        "LANDSCAPE FLOORING DETAIL"
    ],
    "Interior": [
        # Add interior drawings here - user can provide later
    ],
    "Landscape": [
        # Add landscape drawings here - user can provide later
    ],
    "Planning": [
        # Add planning drawings here - user can provide later
    ]
}

def get_template_drawings(category):
    """Get the drawing template for a specific category"""
    return DRAWING_TEMPLATES.get(category, [])

def get_all_categories():
    """Get list of all available categories"""
    return list(DRAWING_TEMPLATES.keys())
