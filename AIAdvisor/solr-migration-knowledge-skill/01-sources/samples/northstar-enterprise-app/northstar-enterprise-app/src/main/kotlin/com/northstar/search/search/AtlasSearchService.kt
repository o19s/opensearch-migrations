package com.northstar.search.search

import com.northstar.search.domain.AtlasDocument
import com.northstar.search.domain.SearchRequest
import com.northstar.search.domain.SearchResponse
import com.northstar.search.indexing.SampleDocumentLoader
import com.northstar.search.config.OpenSearchProperties
import org.springframework.stereotype.Service

@Service
class AtlasSearchService(
    private val sampleDocumentLoader: SampleDocumentLoader,
    private val openSearchSearchClient: OpenSearchSearchClient,
    private val openSearchProperties: OpenSearchProperties
) {
    fun search(request: SearchRequest): SearchResponse {
        val appliedFilters = buildAppliedFilters(request)

        if (openSearchProperties.preferLiveSearch) {
            runCatching {
                val hits = openSearchSearchClient.search(request)
                return SearchResponse(
                    query = request.query,
                    appliedFilters = appliedFilters,
                    hits = hits,
                    notes = listOf(
                        "Results are coming from the OpenSearch read alias ${openSearchProperties.readAlias}.",
                        "If the demo index is not loaded, rerun scripts/reindex_northstar.py."
                    )
                )
            }.onFailure {
                // Fall through to the bundled sample corpus for a more resilient demo.
            }
        }

        val queryLower = request.query.trim().lowercase()
        val hits = sampleDocumentLoader.load()
            .asSequence()
            .filter { request.region == null || it.region == request.region }
            .filter { request.docType == null || it.doc_type == request.docType }
            .filter { request.visibilityLevel == null || it.visibility_level == request.visibilityLevel }
            .filter { request.dealerTier == null || it.dealer_tier == request.dealerTier }
            .filter { request.businessUnit == null || it.business_unit == request.businessUnit }
            .filter {
                if (queryLower.isBlank()) {
                    true
                } else {
                    listOfNotNull(
                        it.title,
                        it.summary,
                        it.body,
                        it.part_number,
                        it.model_number
                    ).any { field -> field.lowercase().contains(queryLower) } ||
                        (it.txt_keywords?.any { keyword -> keyword.lowercase().contains(queryLower) } == true)
                }
            }
            .toList()

        return SearchResponse(
            query = request.query,
            appliedFilters = appliedFilters,
            hits = hits,
            notes = listOf(
                "OpenSearch was unavailable or not ready, so results are coming from the bundled sample corpus.",
                "Use scripts/reindex_northstar.py to create the target index and bulk-load the same documents into OpenSearch."
            )
        )
    }

    fun sampleDocuments(): List<AtlasDocument> = sampleDocumentLoader.load()

    fun openSearchReachable(): Boolean = openSearchSearchClient.isReachable()

    private fun buildAppliedFilters(request: SearchRequest): Map<String, String> = buildMap {
        request.region?.let { put("region", it) }
        request.docType?.let { put("docType", it) }
        request.visibilityLevel?.let { put("visibilityLevel", it) }
        request.dealerTier?.let { put("dealerTier", it) }
        request.businessUnit?.let { put("businessUnit", it) }
    }
}
