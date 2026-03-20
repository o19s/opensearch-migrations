package com.northstar.search.domain

data class AtlasDocument(
    val id: String,
    val doc_type: String,
    val title: String? = null,
    val summary: String? = null,
    val body: String? = null,
    val part_number: String? = null,
    val model_number: String? = null,
    val product_line: String? = null,
    val region: String? = null,
    val language: String? = null,
    val visibility_level: String? = null,
    val dealer_tier: String? = null,
    val business_unit: String? = null,
    val published_at: String? = null,
    val updated_at: String? = null,
    val attr_application: List<String>? = null,
    val attr_compatible_models: List<String>? = null,
    val attr_document_class: List<String>? = null,
    val attr_error_code: List<String>? = null,
    val attr_case_status: List<String>? = null,
    val txt_keywords: List<String>? = null
)
