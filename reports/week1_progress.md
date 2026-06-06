# Week 1 Progress Report

## Project

MAPPS-Lite: A lightweight AI agent for explainable materials discovery.

## Goal

The goal is to build a small agent that can rank battery cathode materials using scientific features such as stability, voltage, capacity, cost, and supply risk.

## What I Completed

- Created the project structure
- Wrote a summary of the MAPPS workflow
- Chose battery cathode materials as the first domain
- Created a starter dataset of candidate materials
- Built a baseline scoring system
- Generated explanations for ranked materials

## Current Method

The current ranking system uses a weighted score based on:

- Stability
- Voltage
- Capacity
- Cost practicality
- Supply risk

## Early Result

The system can rank a small set of candidate cathode materials and explain each ranking using simple scientific reasoning.

## Next Steps

In Week 2, I will replace the mock dataset with real materials data, likely from the Materials Project API or another public materials database. I will also begin turning the ranking system into a more agent-like workflow with planning, tool use, and revision.