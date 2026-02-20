# Geospatial Analytics SCL

Welcome to the Geospatial Analytics SCL repository. This analytical repository supports the preprocessing and analysis of geospatial data for the Social Sector work in Latin America and the Caribbean (LAC), providing tools and resources to facilitate data analysis and exploration.

## Table of Contents

- [Introduction](#introduction)
- [Repository structure](#repository-structure)
- [How to use?](#how-to-use)
- [Author](#author)
- [Citation](#citation)
- [Limitations](#limitations)

## Introduction

This repository is designed around two goals: 

1. Reusable building blocks for common geospatial tasks (in `src/`).
2. Applied sector workflows that demonstrate how to use those building blocks end-to-end (in `sector/`).

To support collaboration and long-term maintainability, workflows are organized to be easy to navigate, adapt, and hand off, with lightweight metadata and clear conventions for inputs/outputs and intermediate products. In line with the [SCL geospatial governance](https://idbg.sharepoint.com/:b:/r/sites/DataGovernance-SCL/Shared%20Documents/General/M.%20Manuals%20%26%20Standards/M.1%20Data%20Governance/M.1.6%20Geospatial%20Data/SCL%20Geospatial%20Data%20Governance%20Framework.pdf?csf=1&web=1&e=KwhwHo), the emphasis is on consistency, reproducibility, and clear documentation practices across projects. 

## Repository structure

The repository contains:

- `src/`  
  Reusable Python modules for geospatial processing and analysis. These components are meant to be imported by notebooks/scripts in `sector/`.

- `sector/`  
  Sector- or use-case–specific workflows (typically notebooks and scripts) that tend **apply** the reusable modules in `src/` in a more complete, end-to-end way.

- `metadata-sample.csv`  
  A template to help standardize how datasets, intermediate outputs, and derived geospatial products are documented within analytical work (inputs/outputs, owner/contact, notes, etc.). This is consistent with the governance emphasis on maintaining complete metadata for geospatial layers and products.

- `requirements.txt`  
  List of Python dependencies typically used across the repository notebooks/scripts.

- `setup.py`  
  Packaging file to support importing the modules in `src/` in a consistent way across projects (e.g., editable installs in local environments). This README intentionally does **not** include installation/setup instructions, since the repo is primarily used as an analytical workspace.

## How to use?

1. **Start in **`sector/`: pick the workflow closest to your use case and run it as the “reference implementation”.
2. **Trace back to **`src/`: reuse the underlying functions/modules for your own project (instead of re-implementing processing steps).
3. **Document what you produce**: use `metadata-sample.csv` as a starting point to document key inputs/outputs and support reproducibility and handoff.
4. **Archive appropriately**: keep workflows that are meant to be reusable in this repository; keep strictly project-specific scripts with the project deliverables when they are not intended for broader reuse

## Author 

Created by **[Laura Goyeneche](https://github.com/lgoyenec)**, Social Data Consultant at the Inter-American Development Bank (IDB), and maintained by **SCL Geospatial team**.

## Citation 

If you use this repository in a report, paper, or product, please cite it as:

> "Inter-American Development Bank (IDB), Geospatial Analytics SCL (consultation date: YYYY-MM-DD)"

We recommend including the consultation date because analytical inputs and derived outputs can evolve over time.

> All rights concerning the public datasets used from Meta, HDX, OpenStreetMaps, and healthsites.io belong to their respective owners.

## Limitations of responsibilities 

The IDB is not responsible, under any circumstance, for damage or compensation, moral or patrimonial; direct or indirect; accessory or special; or by way of consequence, foreseen or unforeseen, that could arise: (i) under any concept of intellectual property, negligence, or detriment of another party theory; (ii) following the use of the digital tool, including, but not limited to defects in the Digital Tool, or the loss or inaccuracy of data of any kind. The foregoing includes expenses or damages associated with communication failures and/or malfunctions of computers linked to the use of the digital tool.

## Contributing 

We welcome contributions from the community! If you have suggestions for new features, improvements, or bug fixes, please feel free to submit a pull request. When contributing, please ensure that your code is well-documented and follows the project's coding standards.
