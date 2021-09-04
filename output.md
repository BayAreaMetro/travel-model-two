---
layout: page
title: Output
---

# Output Files

---
CONTENTS

1. [Person Type Segmentation](#person-type)

---

## Person Type Segmentation

The MTC activity-based model system is implemented in a microsimulation framework. A key advantage of
using the microsimulation approach is that there are essentially no computational constraints on
the number of explanatory variables that can be included in a model specification. However, even with
this flexibility, the model system will include some segmentation of decision‐makers. Segmentation
is a useful tool to both structure models, such that each person‐type segment could have their own
model for certain choices, and also to characterize person roles within a household. Segments can be
created for persons as well as households.

A total of eight segments of person‐types, shown in the below table, are used for the MTC model system.
The person‐types are mutually exclusive with respect to age, work status, and school status.

| **NUMBER** | **PERSON TYPE**               | **AGE** | **WORK STATUS** | **SCHOOL STATUS** |
|:-----------|:------------------------------|:--------|:----------------|:------------------|
| 1          | Full-time worker (30 hours+)  | 18+     | Full-time       | None              |
| 2          | Part-time worker (<30 hours)  | 18+     | Part-time       | None              | 
| 3          | College student               | 18+     | Any             | College+          |
| 4          | Non-working adult             | 18-64   | Unemployed      | None              |
| 5          | Non-working senior            | 65+     | Unemployed      | None              |
| 6          | Driving age student           | 16-17   | Any             | Pre-college       |
| 7          | Non-driving student           | 6-15    | None            | Pre-college       |
| 8          | Pre-school                    | 0-5     | None            | None              |

