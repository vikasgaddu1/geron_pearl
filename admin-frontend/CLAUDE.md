# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **📖 For comprehensive project documentation, features, installation, and usage instructions, see [README.md](README.md)**

## Project Overview

This is the R Shiny admin frontend for the PEARL research data management system. It provides a modern, real-time CRUD interface for managing studies that communicates with the FastAPI backend via REST API and WebSocket connections.

**Key Features**: Real-time WebSocket updates, modern Bootstrap 5 UI, multi-user synchronization
**Technology Stack**: R Shiny + bslib + WebSocket (JavaScript/R dual clients)

## Development Memories

- Read the claude.md and readme.md file to get understanding of the project

## Critical Development Constraints

> **🚨 IMPORTANT**: These constraints prevent breaking core functionality

### Environment Variable Integration
- **All URLs MUST use environment variables**: Never hardcode `localhost:8000` or API paths
- **Dynamic Loading Pattern**: Use `Sys.getenv()` with fallbacks in modules, not global variables
- **Correct Variables**: `PEARL_API_URL`, `PEARL_API_HEALTH_PATH`, `PEARL_API_STUDIES_PATH`, `PEARL_API_WEBSOCKET_PATH`

### WebSocket Integration Constraints
- **⚠️ CRITICAL**: Do NOT modify `www/websocket_client.js` message handling without checking backend format
- **Backend Message Format**: `{"type": "study_created", "data": {...}}` - no `module` property
- **Shiny Event Routing**: JavaScript sends to `'studies-websocket_event'`, Shiny receives `input$websocket_event`
- **Required Message Types**: `studies_update`, `study_created`, `study_updated`, `study_deleted`, `refresh_needed`
- **Status Updates**: Go to main app (`'websocket_status'`), not studies module

### Module Integration Rules
- **Source Order Matters**: `websocket_client.R` must be sourced BEFORE other modules that use WebSocket URLs
- **Environment Loading**: Call `load_dot_env()` BEFORE defining any endpoint URLs
- **Self-Contained Modules**: Each module should read environment variables directly, not depend on globals

## Architecture

> **📋 See [README.md - Architecture](README.md#architecture) for detailed file structure and module descriptions**

### Modern R Shiny Stack
- **Framework**: R Shiny with modern bslib Bootstrap 5 theming
- **UI Library**: bslib + bsicons for contemporary design
- **HTTP Client**: httr2 for REST API communication  
- **Real-time**: WebSocket integration (JavaScript primary, R secondary)
- **Package Management**: renv for reproducible environments