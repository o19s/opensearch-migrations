package com.northstar.search.domain

data class SearchResponse(
    val query: String,
    val appliedFilters: Map<String, String>,
    val hits: List<AtlasDocument>,
    val notes: List<String>
)
