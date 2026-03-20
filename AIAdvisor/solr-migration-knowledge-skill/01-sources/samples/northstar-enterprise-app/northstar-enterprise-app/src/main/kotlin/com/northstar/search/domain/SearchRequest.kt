package com.northstar.search.domain

data class SearchRequest(
    val query: String = "",
    val region: String? = null,
    val docType: String? = null,
    val visibilityLevel: String? = null,
    val dealerTier: String? = null,
    val businessUnit: String? = null
)
