"""
Seed Data Sources for Hierarchical Task Decomposition.

This package provides loaders for comprehensive datasets that serve as
the foundation for building a complete task taxonomy.

DATA SOURCES:
=============

1. O*NET Database (PRIMARY for work)
   - 23 major occupation groups
   - 1,016 occupations
   - 18,796 task statements
   - 2,087 Detailed Work Activities
   Source: U.S. Department of Labor

2. Life Activities Taxonomy (for non-work)
   - 12 life domains
   - Personal care, household, caregiving, etc.
   - Covers all non-work human activities
   Source: Based on ATUS/ADL/IADL

MODULES:
========
    taxonomy - Life domains and activity categories
    onet - O*NET database loader (occupations + tasks)
    base - Base classes for seed data
    loaders - Additional dataset loaders (WikiHow, COIN, etc.)
"""

from taskpedia.seeds.base import BaseSeedLoader, SeedTask
from taskpedia.seeds.onet import (
    SOC_MAJOR_GROUPS,
    DetailedWorkActivity,
    IntermediateWorkActivity,
    Occupation,
    ONetDatabase,
    TaskStatement,
    load_onet,
)
from taskpedia.seeds.taxonomy import (
    DOMAIN_NAMES,
    LIFE_ACTIVITIES,
    SOC_TO_DOMAIN,
    ActivityCategory,
    LifeDomain,
    get_all_domains,
    get_all_life_tasks,
    get_categories_for_domain,
    get_domain_name,
    get_life_domains,
    get_work_domains,
    is_life_domain,
    is_work_domain,
)

__all__ = [
    # Base
    "BaseSeedLoader",
    "SeedTask",
    # Taxonomy
    "LifeDomain",
    "ActivityCategory",
    "LIFE_ACTIVITIES",
    "DOMAIN_NAMES",
    "SOC_TO_DOMAIN",
    "get_all_domains",
    "get_work_domains",
    "get_life_domains",
    "get_categories_for_domain",
    "get_all_life_tasks",
    "get_domain_name",
    "is_work_domain",
    "is_life_domain",
    # O*NET
    "ONetDatabase",
    "Occupation",
    "TaskStatement",
    "DetailedWorkActivity",
    "IntermediateWorkActivity",
    "SOC_MAJOR_GROUPS",
    "load_onet",
]
