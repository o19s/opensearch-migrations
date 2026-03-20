package com.northstar.search.search

import com.fasterxml.jackson.databind.JsonNode
import com.fasterxml.jackson.databind.ObjectMapper
import com.northstar.search.config.OpenSearchProperties
import com.northstar.search.domain.AtlasDocument
import com.northstar.search.domain.SearchRequest
import org.springframework.stereotype.Component
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.time.Duration

@Component
class OpenSearchSearchClient(
    private val objectMapper: ObjectMapper,
    private val openSearchProperties: OpenSearchProperties
) {
    private val httpClient: HttpClient = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(3))
        .build()

    fun isReachable(): Boolean {
        val request = HttpRequest.newBuilder()
            .uri(URI.create("${openSearchProperties.url}/_cluster/health"))
            .timeout(Duration.ofSeconds(3))
            .GET()
            .build()

        return runCatching {
            val response = httpClient.send(request, HttpResponse.BodyHandlers.ofString())
            response.statusCode() in 200..299
        }.getOrDefault(false)
    }

    fun search(request: SearchRequest): List<AtlasDocument> {
        val payload = buildSearchPayload(request)
        val httpRequest = HttpRequest.newBuilder()
            .uri(URI.create("${openSearchProperties.url}/${openSearchProperties.readAlias}/_search"))
            .timeout(Duration.ofSeconds(5))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(payload)))
            .build()

        val response = httpClient.send(httpRequest, HttpResponse.BodyHandlers.ofString())
        if (response.statusCode() !in 200..299) {
            throw IllegalStateException("OpenSearch search failed: ${response.statusCode()} ${response.body()}")
        }

        val root = objectMapper.readTree(response.body())
        return root.path("hits").path("hits").mapNotNull { hit ->
            parseDocument(hit)
        }
    }

    private fun buildSearchPayload(request: SearchRequest): Map<String, Any> {
        val filters = mutableListOf<Map<String, Any>>()
        request.region?.let { filters += termFilter("region", it) }
        request.docType?.let { filters += termFilter("doc_type", it) }
        request.visibilityLevel?.let { filters += termFilter("visibility_level", it) }
        request.dealerTier?.let { filters += termFilter("dealer_tier", it) }
        request.businessUnit?.let { filters += termFilter("business_unit", it) }

        val mustClause: Map<String, Any> =
            if (request.query.isBlank()) {
                mapOf("match_all" to emptyMap<String, Any>())
            } else {
                mapOf(
                    "multi_match" to mapOf(
                        "query" to request.query,
                        "fields" to listOf(
                            "title^8",
                            "part_number^12",
                            "model_number^10",
                            "summary^4",
                            "body^1",
                            "txt_keywords^5",
                            "score_text^3"
                        ),
                        "type" to "best_fields"
                    )
                )
            }

        return mapOf(
            "size" to 12,
            "_source" to true,
            "sort" to listOf(
                mapOf("_score" to "desc"),
                mapOf("published_at" to mapOf("order" to "desc", "unmapped_type" to "date"))
            ),
            "query" to mapOf(
                "bool" to mapOf(
                    "must" to listOf(mustClause),
                    "filter" to filters
                )
            )
        )
    }

    private fun termFilter(field: String, value: String): Map<String, Any> =
        mapOf("term" to mapOf(field to value))

    private fun parseDocument(hit: JsonNode): AtlasDocument? {
        val source = hit.path("_source")
        if (source.isMissingNode || source.isNull) {
            return null
        }
        return objectMapper.treeToValue(source, AtlasDocument::class.java)
    }
}
