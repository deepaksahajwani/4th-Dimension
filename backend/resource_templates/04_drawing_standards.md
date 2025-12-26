# Drawing Standards Manual
## 4th Dimension Architects

---

## 1. Purpose
This manual establishes the drawing standards for all architectural documentation at 4th Dimension Architects. Adherence ensures consistency, professionalism, and efficient collaboration.

---

## 2. Drawing Sizes & Scales

### Standard Sheet Sizes
| Size | Dimensions (mm) | Use |
|------|-----------------|-----|
| A0 | 841 x 1189 | Master plans, large projects |
| A1 | 594 x 841 | Primary working drawings |
| A2 | 420 x 594 | Detail sheets |
| A3 | 297 x 420 | Client presentations, reports |

### Standard Scales
| Drawing Type | Preferred Scale | Alternative |
|--------------|-----------------|-------------|
| Site Plan | 1:500 | 1:200 |
| Floor Plans | 1:100 | 1:50 |
| Elevations | 1:100 | 1:50 |
| Sections | 1:50 | 1:100 |
| Details | 1:20, 1:10 | 1:5 |
| Furniture Layout | 1:50 | 1:100 |

---

## 3. Title Block

### Required Information
- Company logo and name
- Project name and code
- Drawing title
- Drawing number
- Scale
- Date
- Drawn by / Checked by / Approved by
- Revision table
- Sheet number (X of Y)

### Title Block Location
- Always bottom-right corner
- Standard size: 180mm x 60mm

---

## 4. Layer Naming Convention

### Format: DISCIPLINE-ELEMENT-STATUS

### Disciplines
| Code | Discipline |
|------|------------|
| A | Architectural |
| S | Structural |
| M | Mechanical |
| E | Electrical |
| P | Plumbing |
| L | Landscape |
| I | Interior |

### Elements
| Code | Element |
|------|----------|
| WALL | Walls |
| DOOR | Doors |
| WIND | Windows |
| FURN | Furniture |
| CLNG | Ceiling |
| FLOR | Flooring |
| DIMS | Dimensions |
| TEXT | Text/Notes |
| HATCH | Hatching |
| GRID | Grid lines |

### Status
| Code | Meaning |
|------|----------|
| NEW | New work |
| EXIST | Existing |
| DEMO | To be demolished |
| FUT | Future work |

### Examples
- `A-WALL-NEW` - New architectural walls
- `A-DOOR-EXIST` - Existing doors
- `I-FURN-NEW` - New furniture
- `A-WALL-DEMO` - Walls to be demolished

---

## 5. Line Types & Weights

### Line Weights
| Weight | mm | Use |
|--------|------|------|
| Heavy | 0.50 | Section cuts, outlines |
| Medium | 0.35 | Major elements, walls |
| Light | 0.25 | Furniture, text |
| Fine | 0.18 | Hatching, dimensions |
| Hairline | 0.13 | Construction lines |

### Line Types
| Type | Use |
|------|------|
| Continuous | Visible outlines |
| Dashed | Hidden lines, above cut |
| Chain | Center lines, grid |
| Dotted | Demolished/removed |

---

## 6. Text Standards

### Font
- Primary: Arial or Simplex
- Titles: Arial Bold

### Text Heights
| Use | Height (mm) |
|-----|-------------|
| Drawing title | 5.0 |
| Room names | 3.5 |
| Dimensions | 2.5 |
| Notes | 2.5 |
| Fine annotations | 2.0 |

---

## 7. Dimension Standards

### Rules
- Always dimension to finished surfaces
- Use running dimensions where possible
- Maintain consistent dimension line spacing (10mm)
- Place dimensions outside the drawing when possible

### Dimension Styles
- Arrow type: Architectural tick or oblique
- Text position: Above line, centered
- Units: Millimeters (no suffix)

---

## 8. Hatching Standards

### Common Patterns
| Material | Pattern | Scale |
|----------|---------|-------|
| Brick | ANSI31 | 1.0 |
| Concrete | AR-CONC | 0.5 |
| Earth | EARTH | 1.0 |
| Insulation | INSUL | 1.0 |
| Wood | WOOD | 1.0 |
| Glass | Solid | - |

---

## 9. Drawing Numbering

### Format: PROJECT-DISCIPLINE-TYPE-NUMBER

### Example: 2024-001-A-FP-01
- 2024-001: Project code
- A: Architectural
- FP: Floor Plan
- 01: Sheet number

### Drawing Types
| Code | Type |
|------|------|
| LOC | Location plan |
| SP | Site plan |
| FP | Floor plan |
| RCP | Reflected ceiling plan |
| EL | Elevation |
| SEC | Section |
| DET | Details |
| SCH | Schedules |
| 3D | 3D views |

---

## 10. Revision Management

### Revision Clouds
- Use revision clouds to highlight changes
- Triangle marker with revision letter

### Revision Table
| Rev | Date | Description | By |
|-----|------|-------------|----|
| A | 01/01/25 | Issued for Review | DS |
| B | 15/01/25 | Client comments | AK |

### Revision Naming
- Pre-issue: P1, P2, P3...
- Issued: A, B, C...

---

## 11. File Naming Convention

### Format
`[ProjectCode]-[Discipline]-[Type]-[Number]-[Rev]`

### Example
`2024-001-A-FP-01-B.dwg`

---

## 12. Quality Checklist Before Issue

- [ ] All layers correctly named
- [ ] Title block complete and accurate
- [ ] Dimensions verified
- [ ] Text spell-checked
- [ ] Hatching consistent
- [ ] File purged (PURGE command)
- [ ] Xrefs bound (for issue)
- [ ] PDF generated correctly
- [ ] Reviewed by Team Leader

---

*Standard effective from: January 2025*
*Review annually*